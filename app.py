import streamlit as st
import pandas as pd
import stock_utils  # ★作成した裏方ファイルを読み込む！

# ==========================================
#  アプリの画面処理 (UI)
# ==========================================

st.title("株価分析ダッシュボード 📊")

# --- 1. サイドバー（入力） ---
st.sidebar.header("分析モード選択")
mode = st.sidebar.radio("データの入力方法", ["手入力・ファイル", "業種別リスト(JPX)"])

target_tickers = []
name_map = {}

if mode == "手入力・ファイル":
    uploaded_file = st.sidebar.file_uploader("銘柄リスト(txt)", type=["txt"])
    if uploaded_file is not None:
        string_data = uploaded_file.getvalue().decode("utf-8")
        st.sidebar.success(f"読み込み成功: {uploaded_file.name}")
    else:
        default_tickers = "7203\n6758\n8035\n9984\n9434\n8058"
        string_data = st.sidebar.text_area("コード手入力", value=default_tickers, height=150)
    
    # ★裏方の関数を呼び出すときは stock_utils.関数名
    target_tickers = stock_utils.normalize_tickers(string_data)

elif mode == "業種別リスト(JPX)":
    jpx_file = "data_j.xls"
    # ★裏方の関数呼び出し
    df_jpx = stock_utils.load_jpx_data(jpx_file)
    
    if df_jpx.empty:
        st.sidebar.error(f"'{jpx_file}' が見つかりません。")
    else:
        sectors = df_jpx["33業種区分"].unique().tolist()
        selected_sector = st.sidebar.selectbox("業種を選択してください", sectors)
        
        df_sector_stocks = df_jpx[df_jpx["33業種区分"] == selected_sector]
        st.sidebar.info(f"{selected_sector}: {len(df_sector_stocks)}銘柄")
        
        target_tickers = df_sector_stocks["コード"].tolist()
        name_map = dict(zip(df_sector_stocks["コード"], df_sector_stocks["銘柄名"]))

        limit = st.sidebar.slider("取得上限数", 5, len(df_sector_stocks), 10)
        target_tickers = target_tickers[:limit]
        st.sidebar.text(f"上位{len(target_tickers)}件を取得します")


# --- 2. データ取得実行 ---
if st.sidebar.button("データを取得する"):
    if target_tickers:
        if mode == "業種別リスト(JPX)":
            st.write(f"### 業種分析: {len(target_tickers)}件を取得中...")
        
        # ★裏方にデータ取得を依頼
        df = stock_utils.fetch_financial_metrics(target_tickers, name_map=name_map)
        st.session_state["df_data"] = df
    else:
        st.sidebar.warning("銘柄コードが見つかりません")


# --- 3. 結果表示 ---
if "df_data" in st.session_state:
    df = st.session_state["df_data"]

    st.write(f"### 取得結果 ({len(df)}銘柄)")
    with st.expander("詳細データを確認する"):
        st.dataframe(df)
    
    st.divider()
    st.subheader("条件絞り込み")

    col1, col2 = st.columns(2)
    with col1:
        min_market_cap = st.slider("時価総額の下限(兆円)", 0.0, 50.0, 1.0, 0.5)
        threshold_cap = min_market_cap * 1_000_000_000_000
    with col2:
        min_yield = st.slider("配当利回りの下限(%)", 0.0, 10.0, 2.5, 0.1)
    
    df_filtered = df[
        (df["時価総額"] >= threshold_cap) &
        (df["配当利回り"] >= min_yield)
    ].copy()

    st.success(f"条件に合う銘柄: {len(df_filtered)}件")

    # 表示用データの作成
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
                "PER(予/倍)": lambda x: "{:.2f}".format(x) if x is not None else "-",
                "PBR(倍)": lambda x: "{:.2f}".format(x) if x is not None else "-",
                "ROE(%)": lambda x: "{:.1f}".format(x) if x is not None else "-",
                "配当利回り(%)": lambda x: "{:.2f}".format(x) if x is not None else "-",
                "時価総額": "{:,.0f}"
            })
        )
        csv_data = df_display.to_csv(index=False).encode("utf-8-sig")
        st.download_button(label="分析結果CSVダウンロード", data=csv_data, file_name="my_stock.csv", mime="text/csv")

    # --- グラフ表示エリア ---
    st.divider()
    st.subheader("分析グラフ")
    tab1, tab2 = st.tabs(["時価総額比較", "割安性分析(PER/PBR)"])

    with tab1:
        if not df_filtered.empty:
            # ★裏方のグラフ描画関数を呼ぶだけ！スッキリ！
            stock_utils.visualize_bar_chart(df_filtered)

    with tab2:
        if not df_filtered.empty:
            df_chart = df_filtered.dropna(subset=["PER(予)", "PBR"])
            # ★裏方のグラフ描画関数を呼ぶだけ！
            stock_utils.visualize_scatter(df_chart)
    
    # --- 4.個別銘柄の深掘り分析エリア ---
    st.divider()
    st.subheader("個別銘柄の業績分析")

    #セレクトボックスで詳細を見たい企業を1つ選ばせる
    if not df_filtered.empty:
        #"コード: 会社名"の形式リストを作る
        company_list = [f"{row['コード']} : {row['会社名']}" for idx, row in df_filtered.iterrows()]

        selected_company = st.selectbox("詳しく見たい企業を選択してください", company_list)

        if selected_company:
            #選択された文字列からコードだけ取り出す("7203.T : トヨタ" -> "7203.T")
            selected_code = selected_company.split(" : ")[0]
            selected_name = selected_company.split(" : ")[1]
            
            st.write(f"**{selected_name} ({selected_code})** の決算データを取得中...")

            #裏方の関数を呼び出してデータ取得
            df_performance = stock_utils.fetch_company_performance(selected_code)

            if not df_performance.empty:
                #表を表示
                st.write("業績データ(単位: 円)") 
                st.dataframe(df_performance.style.format("{:,.0f}"))

                #裏方の関数でグラフ描画
                stock_utils.visualize_performance(df_performance, selected_name)
                st.info("解説: 青い棒グラフｇ「売上(ビジネスの規模)」、オレンジの線が「利益(手元に残るお金)」です。両方とも右肩上がりが理想です")
                
                st.divider()#区切り線
                st.subheader(f"{selected_name}の株価チャート(Plotly)")
                #1.裏方に「過去データ取得の依頼」
                df_history = stock_utils.fetch_stock_history(selected_code)

                st.write(df_history.head())

                if not df_history.empty:
                    with st.sidebar.expander("チャート表示設定", expanded=True):
                        short_span = st.slider('短期線の周期を選択してください', 5, 50, 5, 5)
                        long_span = st.slider('長期線の周期を選択してください', 50, 200, 50, 25)
                        show_bollinger = st.checkbox('ボリンジャーバンドを表示する', value=True)

                    #2.裏方に「plotly図の作成」を依頼
                    fig = stock_utils.plot_stock_plotly(df_history, selected_name, short_span, long_span, show_bollinger)
                    #3.画面に表示
                    st.plotly_chart(fig, use_container_width=True)
                    #4.出来高グラフを追加
                    st.subheader("出来高推移")
                    fig_vol = stock_utils.plot_volume_plotly(df_history, selected_name)
                    st.plotly_chart(fig_vol, use_container_width=True)
                    #5.RSIグラフを追加
                    st.subheader("RSI")
                    fig_rsi = stock_utils.plot_RSI_plotly(df_history, selected_name)
                    st.plotly_chart(fig_rsi, use_container_width=True)
                    #6.銘柄と日経平均の変化率比較
                    st.subheader("日経平均との変化率比較")
                    current_period = st.session_state.get('selected_period_code', '1y')
                    df_benchmark = stock_utils.fetch_stock_history('^N225', period=current_period)
                    if not df_benchmark.empty:
                        fig_comparison = stock_utils.plot_comparison_plotly(df_history, df_benchmark, selected_name)
                        st.plotly_chart(fig_comparison, use_container_width=True)
                    else:
                        st.warning("日経平均データが取得できませんでした")
                else:
                    st.warning("株価データが取得できませんでした")
            else:
                st.warning("決算データが取得できませんでした(ETFや直近上場企業の可能性があります)")
    