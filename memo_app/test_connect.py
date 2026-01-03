import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# 1. 認証の設定
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
client = gspread.authorize(creds)

# 2. スプレッドシートを開く
# ★ここを書き換える！(URLの /d/ と /edit の間の文字列)
SPREADSHEET_KEY = '14rdBOuqlwEwJwTXrGAMr2DRCIgYwEjOUjVQ54LuNau4' 

try:
    # シートを開く
    sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
    
    # 3. 書き込みテスト
    # A1セルに現在時刻を書き込んでみます
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sheet.update_cell(1, 1, f"接続テスト成功！: {now}")
    
    print("✅ 書き込み成功！スプレッドシートのA1セルを見てみてね！")
    
    # 4. 読み込みテスト
    val = sheet.cell(1, 1).value
    print(f"📖 読み込んだ値: {val}")

except Exception as e:
    print(f"❌ エラーが発生しました: {e}")