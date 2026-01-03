import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 設定エリア ---
# ★ここにさっきのIDをコピペしてください！
SPREADSHEET_KEY = '14rdBOuqlwEwJwTXrGAMr2DRCIgYwEjOUjVQ54LuNau4'

st.set_page_config(page_title="私の家計簿", page_icon="💰", layout="centered")
st.title("家計簿アプリ 💰 (Google Sheets版)")

# --- 関数エリア: 毎回書くのが大変な処理をまとめる ---

# 1. スプレッドシートに接続する関数（キャッシュ機能付きで高速化）
# 修正版 get_worksheet 関数
@st.cache_resource
def get_worksheet():
    # 認証情報を設定
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # ★ここが変わりました！
    # Streamlit Cloudの「Secrets」に鍵があるか確認する
    if "gcp_service_account" in st.secrets:
        # クラウド用: Secretsから情報を読み取る
        key_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    else:
        # ローカル用: パソコン内のjsonファイルを見る
        creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
        
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
    return sheet

# 2. データを読み込む関数
def load_data(sheet):
    data = sheet.get_all_records()
    # データが空っぽのときの処理
    if not data:
        return pd.DataFrame(columns=["日付", "内容", "金額", "年月"])
    
    df = pd.DataFrame(data)
    # 日付データを正しく認識させる
    # (スプレッドシートから読むと文字列になりがちなので変換)
    # ※既存データが空文字の場合などに備えて errors='coerce'
    df["日付"] = pd.to_datetime(df["日付"], errors='coerce') 
    # 再度、文字列のきれいな形に戻しておく（表示用）
    df["日付"] = df["日付"].dt.strftime("%Y-%m-%d")
    return df

# 3. データを保存（全書き換え）する関数
def save_data(sheet, df):
    # データフレームの日付などが崩れないように全て文字列にする
    df_to_save = df.astype(str)
    
    # シートを一旦まっさらにする
    sheet.clear()
    
    # ヘッダー（列名）と中身を書き込む
    # [columns] + [values] でリストを合体させて書き込みます
    sheet.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())


# --- アプリのメイン処理 ---

# 接続開始！
try:
    sheet = get_worksheet()
    df_current = load_data(sheet)
except Exception as e:
    st.error(f"スプレッドシートへの接続エラー: {e}")
    st.stop() # ここで止める

# 入力フォーム
with st.form("input_form", clear_on_submit=True):
    date = st.date_input("日付", datetime.date.today())
    item = st.text_input("内容")
    amount = st.number_input("金額", step=100)
    submitted = st.form_submit_button("登録")

    if submitted:
        # 新しいデータを作る
        new_data = pd.DataFrame({
            "日付": [date.strftime("%Y-%m-%d")],
            "内容": [item],
            "金額": [int(amount)],
            "年月": [date.strftime("%Y-%m")] # 年月もここで作っちゃいます
        })

        # 結合して保存
        df_combined = pd.concat([df_current, new_data], ignore_index=True)
        save_data(sheet, df_combined)
        
        st.success("スプレッドシートに登録しました！")
        st.rerun() # リロードして最新データを表示

# --- データの表示・編集エリア ---
st.divider()
st.subheader("📝 データの確認・修正")

if not df_current.empty:
    # データがあれば表示処理
    # (日付変換などは load_data で済んでいるので楽ちん！)
    
    # 年月リスト作成
    if "年月" not in df_current.columns:
        # もし昔のデータで「年月」列がなかったら、日付から作る
        df_current["年月"] = pd.to_datetime(df_current["日付"]).dt.strftime("%Y-%m")
        
    month_list = df_current["年月"].unique()
    # 新しい月が上に来るように逆順ソート
    month_list = sorted(month_list, reverse=True) 
    
    target_month = st.selectbox("表示する月を選んでください", month_list)

    # フィルタリング
    df_filtered = df_current[df_current["年月"] == target_month]

    # 編集画面
    df_edited = st.data_editor(df_filtered, num_rows="dynamic", key="editor_filtered")

    if st.button("修正内容を保存する"):
        try:
            # 1. 元データから該当月のデータを削除（除外）
            df_current = df_current[df_current["年月"] != target_month]
            
            # 2. 編集後のデータを結合
            # (編集画面で追加した行には「年月」が入っていないことがあるので補完する)
            if not df_edited.empty:
                # 日付列から再度「年月」を作り直してあげるのが安全
                df_edited["年月"] = pd.to_datetime(df_edited["日付"]).dt.strftime("%Y-%m")
            
            df_current = pd.concat([df_current, df_edited], ignore_index=True)
            
            # 3. 日付順に並べ替え
            df_current = df_current.sort_values("日付")
            
            # 4. スプレッドシートに書き込み
            save_data(sheet, df_current)
            
            st.success("データを更新しました！")
            st.rerun()
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

    # --- グラフ表示 ---
    st.divider()
    st.subheader(f"📊 {target_month} の支出分析")
    
    # 集計（金額を数値型にしておく念入れ）
    df_filtered["金額"] = df_filtered["金額"].astype(int)
    df_grouped = df_filtered.groupby("内容")[["金額"]].sum()
    st.bar_chart(df_grouped)

else:
    st.info("まだデータがありません。")