import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import japanize_matplotlib
import matplotlib.ticker as ticker
import os

#1.データ加工・取得を行う「工場」エリア
def normalize_tickers(text_input: str) -> list[str]:
    #手入力されたテキストを整形して、銘柄コードのリストにする関数ex7203->7203.T
    tickers = []
    lines = text_input.split('\n')

    for line in lines:
        #全角数字を半角に変換
        code = line.strip().replace("０", "0").replace("１", "1").replace("２", "2").replace("３", "3").replace("４", "4").replace("５", "5").replace("６", "6").replace("７", "7").replace("８", "8").replace("９", "9")

        if not code:
            continue
        #英数字4文字なら.Tをつける
        if code.isalnum() and len(code) == 4:
            code = f"{code}.T"
        tickers.append(code)
    return list(set(tickers))#重複を除去して返す

@st.cache_data
def load_jpx_data(file_path: str) -> pd.DataFrame:
    #JPXのExcelファイルを読み込み、分析に必要な列だけを抽出する関数
    if not os.path.exists(file_path):
        return pd.DataFrame()

    try:
        df = pd.read_excel(file_path)
        #必要列を抽出
        target_columns = ["コード", "銘柄名", "33業種区分", "市場・商品区分"]
        use_cols = [c for c in target_columns if c in df.columns]
        df = df[use_cols]

        #コード整形:4桁なら.Tをつける
        def format_code(x):
            s = str(x).strip()
            if len(s) == 4:
                return f"{s.upper()}.T"
            return s
        
        df["コード"] = df["コード"].apply(format_code)
        
        #s上区分でフィルタリング(プロ向け市場などを除外)
        if "市場・商品区分" in df.columns:
            target_markets = ["プライム（内国株式）", "スタンダード（内国株式）", "グロース（内国株式）"]
            df = df[df["市場・商品区分"].isin(target_markets)]
        return df
    except Exception as e:
        st.error(f"マスターファイルの読み込みに失敗: {e}")
        return pd.DataFrame()


@st.cache_data
def fetch_financial_metrics(tickers: list[str], name_map: dict = None) -> pd.DataFrame:
    #yahoo financeから株価指標を取得する関数
    #name_map: JPXデータで作った{コード:日本語社名}の辞書
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, code in enumerate(tickers):
        status_text.text(f"取得中: {code} ... ")
        try:
            ticker_info = yf.Ticker(code)
            info = ticker_info.info

            #社名取得ロジック
            company_name = info.get("longName")
            if company_name is None:
                company_name = info.get("shortName")
            if name_map and company_name is None and code in name_map:
                company_name = name_map[code]
            if company_name is None:
                company_name = "不明"

            #データの辞書作成
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
    #PER/PBRの散布図を描画する関数

    #グラフ用にデータをコピーし異常値を除外
    df_plot = df[
        (df["PER(予)"] < 50) & (df["PER(予)"] > 0) &
        (df["PBR"] < 5) & (df["PBR"] > 0)
    ].copy()

    if df_plot.empty:
        st.warning("グラフ表示に適した範囲(PER<50, PBR<5)のデータがありませんでした。")
        return
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df_plot["PER(予)"], df_plot["PBR"], color="royalblue", alpha=0.6)

    #平均線の描画
    per_mean = df_plot["PER(予)"].mean()
    pbr_mean = df_plot["PBR"].mean()
    if pd.notna(per_mean):
        ax.axvline(per_mean, color="red", linestyle="--", alpha=0.5, label=f"平均PER: {per_mean:.1f}倍")
    if pd.notna(pbr_mean):
        ax.axhline(pbr_mean, color="red", linestyle="--", alpha=0.5, label=f"平均PBR: {pbr_mean:.1f}倍")

    #銘柄名のプロット
    for idx, row in df_plot.iterrows():
        ax.text(row["PER(予)"], row["PBR"], row["会社名"][:6], fontsize=8, alpha=0.7)
    
    ax.set_title("割安性分析(PER vs PBR)", fontsize=16)
    ax.set_xlabel("PER(倍) - 収益性", fontsize=12)
    ax.set_ylabel("PBR(倍) - 資産性", fontsize=12)
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.6)

    st.pyplot(fig)
    st.info("ヒント: グラフの「左下」にある銘柄ほど、割安と判断されます")

#2.アプリのメイン指令室(UI構築)
st.title("株価分析ダッシュボード")

#サイドバー：入力設定
st.sidebar.header("分析モード選択")

mode = st.sidebar.radio("データの入力方法", ["手入力・ファイル", "業種別リスト(JPX)"])
target_tickers = []
name_map = {}

if mode == "手入力・ファイル":
    upload_file = st.sidebar.file_uploader("銘柄リスト(txt)", type=["txt"])

    if upload_file is not None:
        string_data = upload_file.getvalue().decode("utf-8")
        st.sidebar.success(f"ファイルの読み込み成功:{upload_file.name}")
    else:
        default_tickers = "7203\n6758\n8035\n9984\n9434\n8058"
        string_data = st.sidebar.text_area("またはコード手入力(改行区切り)", value=default_tickers,height=150)

    target_tickers = normalize_tickers(string_data)

elif mode == "業種別リスト(JPX)":
    jpx_file = "data_j.xls"
    df_jpx = load_jpx_data(jpx_file)
    if df_jpx.empty:
        st.sidebar.error(f"'{jpx_file}' が見つかりません。作業フォルダに置いてください。")
    else:
        #業種選択
        sector = df_jpx["33業種区分"].unique().tolist()
        selected_sector = st.sidebar.selectbox("業種を選択してください", sector)
        #その業種の銘柄を抽出
        df_sector_stocks = df_jpx[df_jpx["33業種区分"] == selected_sector]
        st.sidebar.info(f"{selected_sector}: {len(df_sector_stocks)}銘柄が見つかりました")
        #取得対象リスト作成
        target_tickers = df_sector_stocks["コード"].tolist()
        #ここで辞書(code -> Name)を作成
        name_map = dict(zip(df_sector_stocks["コード"], df_sector_stocks["銘柄名"]))
        #取得件数の制限(全権取得も可能)
        limit = st.sidebar.slider("取得上限数", 5, len(df_sector_stocks), 10)
        target_tickers = target_tickers[:limit]
        st.sidebar.text(f"まずは上位{len(target_tickers)}件を取得します")

#ボタンが押されたらデータを取得して保存
if st.sidebar.button("データを取得する"):
    if target_tickers:
        if mode == "業種別リスト(JPX)":
            st.write(f"### 業種分析: {target_tickers}")
        #データ取得実行
        df = fetch_financial_metrics(target_tickers, name_map=name_map)

        #セッションステート(一時保管庫)に保存
        st.session_state["df_data"] = df
    else:
        st.sidebar.warning("銘柄コードがみつかりません")

#3.結果表示エリア(データがあるときだけ動く)
if "df_data" in st.session_state:
    df = st.session_state["df_data"]

    st.write(f"### 取得結果 ({len(df)}銘柄) ")
    with st.expander("元のデータを見る"):
        st.dataframe(df)
    
    st.divider()
    st.subheader("条件絞り込み")

    #フィルタリングUI
    col1, col2 = st.columns(2)

    with col1:
        min_market_cap = st.slider(
            "時価総額の下限(兆円)",
            min_value=0.0, max_value=50.0, value=1.0, step=0.5
        )
        threshold_cap = min_market_cap * 1_000_000_000_000

    with col2:
        min_yield = st.slider(
            "配当利回りの下限(%)",
            min_value=0.0, max_value=10.0, value=2.5, step=0.1
        )
        min_yield_raw = min_yield
    
    #フィルタリング実行
    df_filtered = df[
        (df["時価総額"] >= threshold_cap) &
        (df["配当利回り"] >= min_yield_raw)
    ]

    st.success(F"条件に合う銘柄: {len(df_filtered)}件")

    #表示用データの作成(見た目の整形)
    df_display = df_filtered.copy()
    if not df_display.empty:
        if "ROE" in df_display.columns:
            df_display["ROE"] = df_display["ROE"] * 100
        
        df_display = df_display.rename(columns={
            "PER(予)": "PER(予/倍)",
            "PBR": "PBR(倍)",
            "ROE": "ROE(%)",
            "配当利回り": "配当利回り(%)"
        })



        st.dataframe(
            df_display.style.format({
                "PER(予/倍)": "{:.1f}",
                "PBR(倍)": "{:.1f}",
                "ROE(%)": "{:.1f}",
                "配当利回り(%)": "{:.2f}",
                "時価総額": "{:,.0f}"
            })
        )
        #CSVダウンロードボタン
        csv_data = df_display.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="分析結果をCSVでダウンロード",
            data=csv_data,
            file_name = "my_stock_analysis.csv",
            mime="text/csv",
        )
    #分析グラフエリア   
    st.divider()
    st.subheader("分析グラフ")

    tab1, tab2 = st.tabs(["時価総額比較", "割安性分析(PER/PBR)"])

    with tab1:
        if not df_filtered.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(df_filtered["会社名"], df_filtered["時価総額"], color="skyblue")
            ax.set_ylabel("時価総額")
            def trillion_formatter(x, pos):
                return f'{x / 1_000_000_000_000:.1f}兆円'
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(trillion_formatter))
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            st.pyplot(fig)

    with tab2:
        if not df_filtered.empty:
            visualize_scatter(df_filtered)
        