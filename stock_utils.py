import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import japanize_matplotlib
import matplotlib.ticker as ticker
import os

# ==========================================
#  裏方の処理をまとめたファイル (Utils)
# ==========================================

def normalize_tickers(text_input: str) -> list[str]:
    """手入力されたテキストを整形して銘柄コードリストにする"""
    tickers = []
    lines = text_input.split('\n')
    for line in lines:
        # 全角数字→半角変換
        code = line.strip().translate(str.maketrans({chr(0xFF10 + i): str(i) for i in range(10)}))
        if not code:
            continue
        if code.isalnum() and len(code) == 4:
            code = f"{code}.T"
        tickers.append(code)
    return list(set(tickers))

@st.cache_data
def load_jpx_data(file_path: str) -> pd.DataFrame:
    """JPXのExcelファイルを読み込む"""
    if not os.path.exists(file_path):
        return pd.DataFrame()

    try:
        df = pd.read_excel(file_path)
        target_columns = ["コード", "銘柄名", "33業種区分", "市場・商品区分"]
        use_cols = [c for c in target_columns if c in df.columns]
        df = df[use_cols]

        def format_code(x):
            s = str(x).strip()
            if len(s) == 4:
                return f"{s.upper()}.T"
            return s
        df["コード"] = df["コード"].apply(format_code)
        
        if "市場・商品区分" in df.columns:
            target_markets = ["プライム（内国株式）", "スタンダード（内国株式）", "グロース（内国株式）"]
            df = df[df["市場・商品区分"].isin(target_markets)]
        return df
    except Exception as e:
        st.error(f"マスターファイルの読み込みに失敗: {e}")
        return pd.DataFrame()

@st.cache_data
def fetch_financial_metrics(tickers: list[str], name_map: dict = None) -> pd.DataFrame:
    """Yahoo Financeからデータを取得する"""
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, code in enumerate(tickers):
        status_text.text(f"取得中: {code} ... ")
        try:
            ticker_info = yf.Ticker(code)
            info = ticker_info.info

            # 社名解決ロジック
            company_name = None
            if name_map and code in name_map:
                company_name = name_map[code]
            if company_name is None:
                company_name = info.get("longName")
            if company_name is None:
                company_name = info.get("shortName")
            if company_name is None:
                company_name = "不明"

            data = {
                "コード": code,
                "会社名": company_name,
                "現在値": info.get("currentPrice", 0),
                "PER(予)": info.get("forwardPE", None),
                "PBR": info.get("priceToBook", None),
                "ROE": info.get("returnOnEquity", None),
                "配当利回り": info.get("dividendYield", 0),
                "時価総額": info.get("marketCap", 0)
            }
            results.append(data)
        except Exception as e:
            st.error(f"{code} の取得に失敗: {e}")
        
        progress_bar.progress((i + 1) / len(tickers))
    
    status_text.empty()
    progress_bar.empty()
    return pd.DataFrame(results)

def visualize_scatter(df):
    """PER/PBR散布図を描画する"""
    df_plot = df[
        (df["PER(予)"] < 50) & (df["PER(予)"] > 0) &
        (df["PBR"] < 5) & (df["PBR"] > 0)
    ].copy()

    if df_plot.empty:
        st.warning("グラフ表示に適した範囲(PER<50, PBR<5)のデータがありませんでした。")
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df_plot["PER(予)"], df_plot["PBR"], color="royalblue", alpha=0.6)

    per_mean = df_plot["PER(予)"].mean()
    pbr_mean = df_plot["PBR"].mean()
    if pd.notna(per_mean):
        ax.axvline(per_mean, color="red", linestyle="--", alpha=0.5, label=f"平均PER: {per_mean:.1f}倍")
    if pd.notna(pbr_mean):
        ax.axhline(pbr_mean, color="red", linestyle="--", alpha=0.5, label=f"平均PBR: {pbr_mean:.1f}倍")

    for idx, row in df_plot.iterrows():
        ax.text(row["PER(予)"], row["PBR"], row["会社名"][:6], fontsize=8, alpha=0.7)
    
    ax.set_title("割安性分析(PER vs PBR)", fontsize=16)
    ax.set_xlabel("PER(倍) - 収益性", fontsize=12)
    ax.set_ylabel("PBR(倍) - 資産性", fontsize=12)
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.6)

    st.pyplot(fig)
    st.info("ヒント: グラフの「左下」にある銘柄ほど、割安と判断されます")

def visualize_bar_chart(df):
    """時価総額の棒グラフを描画する（新しく切り出しました）"""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df["会社名"], df["時価総額"], color="skyblue")
    ax.set_ylabel("時価総額")
    def trillion_formatter(x, pos):
        return f'{x / 1_000_000_000_000:.1f}兆円'
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(trillion_formatter))
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    st.pyplot(fig)

def fetch_company_performance(code: str) -> pd.DataFrame:
    #指定された銘柄の過去業績(売上・純利益)を取得する関数
    try:
        ticker = yf.Ticker(code)
        #損益計算書を取得
        df_income = ticker.income_stmt

        #データがない場合のガード
        if df_income.empty:
            return pd.DataFrame()
        
        #必要項目(売上、純利益)を抽出
        #※yfinanceのバージョンや銘柄によってキーが微妙に違う場合があるため、存在確認する
        target_keys = ["Total Revenue", "Net Income"]
        existing_keys = [k for k in target_keys if k in df_income.index]

        if not existing_keys:
            return pd.DataFrame()
        
        #データを抽出して行列を入れ替える(年月を縦軸、項目を横軸)
        df_result = df_income.loc[existing_keys].T

        #列名を日本語にわかりやすく変更
        rename_map = {
            "Total Revenue": "売上高",
            "Net Income": "純利益"
        }
        df_result = df_result.rename(columns=rename_map)

        #日付順(古い順)に並べ替え
        df_result = df_result.sort_index()

        return df_result
    except Exception as e:
        st.error(f"業績データの取得に失敗: {e}")
        return pd.DataFrame

def visualize_performance(df_performance, company_name):
    #売上高(棒グラフ)と純利益(折れ線グラフ)の複合グラフを描く
    if df_performance.empty:
        st.warning("表示できる業績データがありませんでした")
        return
    
    #グラフの準備
    fig, ax1 = plt.subplots(figsize=(10, 5))

    #x軸(年度)のラベル作成(日付型から年だけ取り出す)
    years = [d.strftime('%Y年') for d in df_performance.index]

    #1.売上高の棒グラフ(左軸ax1)
    ax1.bar(years, df_performance["売上高"], color="skyblue", alpha=0.6, label="売上高")
    ax1.set_ylabel("売上高(円)")

    #2.純利益の折れ線グラフ(右軸ax2)
    #ax1と同じx軸を共有する「双子」の軸を作る
    ax2 = ax1.twinx()
    ax2.plot(years, df_performance["純利益"], color="orange", marker="o", linewidth=2, label="純利益")
    ax2.set_ylabel("純利益(円)")

    #3.数値のフォーマット(兆円単位で見やすく)
    def trillion_formatter(x, pos):
        if abs(x) >= 1_000_000_000_000:
            return f'{x / 1_000_000_000_000:.1f}兆'
        else:
            return f'{x / 1_000_000_000:.0f}億'
    
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(trillion_formatter))
    ax2.yaxis.set_major_formatter(ticker.FuncFormatter(trillion_formatter))

    #タイトルと凡例
    ax1.set_title(f"{company_name}の業績推移(直近4年)", fontsize=16)

    #凡例をまとめて表示するテクニック
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    st.pyplot(fig)