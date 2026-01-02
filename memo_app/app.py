import streamlit as st
import pandas as pd
import datetime
import os

# ブラウザタブの装飾
st.set_page_config(
    page_title="私の家計簿",
    page_icon="💰",
    layout="centered"
)


# タイトルを表示
st.title("家計簿アプリ 💰")

file_name = "kakeibo.csv"

# ここに入力フォームを作ります
with st.form("input_form", clear_on_submit=True):
    
    date = st.date_input("日付", datetime.date.today())
    item = st.text_input("内容")
    amount = st.number_input("金額", step=100)

    # フォームを送信するボタン
    submitted = st.form_submit_button("登録")

    # ボタンが押されたら、入力された内容を表示してみる（確認用）
    if submitted:

        new_data = pd.DataFrame({
            "日付": [date.strftime("%Y-%m-%d")],
            "内容": [item],
            "金額": [int(amount)]
        })

        

        if os.path.exists(file_name):
            #ファイルがある場合:読み込んで今回のデータと合体させる
            df_past = pd.read_csv(file_name)
            df_combined = pd.concat([df_past, new_data], ignore_index=True)
        else:
            #ファイルがない場合(初回):今回のデータがそのまま保存データになる
            df_combined = new_data

        df_combined.to_csv(file_name, index=False)

        st.success("登録しました！")

        #保存されたデータの確認
        st.dataframe(df_combined)

st.divider() #区切り線
st.subheader("📝 データの確認・修正")

if os.path.exists(file_name):
    #1.現在のデータを読み込む
    df_current = pd.read_csv(file_name)

    #1.「日付」列を本物の日付データに変換する(月をデータ取得のため)
    df_current["日付"] = pd.to_datetime(df_current["日付"])

    #2.「年月」という新しい列を作って、"2026-01"のような形を入れる
    df_current["年月"] = df_current["日付"].dt.strftime("%Y-%m")

    #3.存在する「年月」のリストを作って(重複無し)、セレクトボックスを作る
    #unique()で重複無し、sort_values()で古い順に並べる
    month_list = df_current["年月"].unique()
    target_month = st.selectbox("表示する月を選んでください", month_list)

    #4.選ばれた月だけのデータに絞り込む
    #「年月」列が選ばれた「target_month」と同じ行だけを取り出す
    df_filtered = df_current[df_current["年月"] == target_month]

    # --- ここから下は df_filtered(絞り込んだデータ)を使います
    
    #編集画面
    df_edited = st.data_editor(df_filtered, num_rows="dynamic", key="editor_filtered")

    #3.編集結果を保存するボタン
    if st.button("修正内容を保存する"):
        try:
            #1.元データから今回表示している行を一旦削除する(インデックス指定)
            #df_filtered.indexは、絞り込まれたデータの行番号リスト
            df_current = df_current.drop(df_filtered.index)
            #2.編集後のデータ(df_edited)を合体させる
            df_current = pd.concat([df_current, df_edited])
            #3.念のため、日付順に並べなおす
            df_current = df_current.sort_values("日付")
            #4.保存
            df_current.to_csv(file_name, index=False)
            
            st.success("データを更新しました！")
            st.rerun()
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
    
    st.divider()
    st.subheader("📊 支出の分析")

    df_grouped = df_filtered.groupby("内容")[["金額"]].sum()
    #3.グラフを表示する
    st.bar_chart(df_grouped)
else:
    st.info("まだデータがありません。")
