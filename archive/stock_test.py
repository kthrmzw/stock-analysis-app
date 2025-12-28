import yfinance as yf

# トヨタ自動車の証券コード（日本の銘柄は数字の後に .T をつけるルールです）
ticker_symbol = "7203.T"

# データ取得
print(f"{ticker_symbol} のデータを取得中...")
stock = yf.Ticker(ticker_symbol)

# 直近の株価情報を取得
current_price = stock.history(period="1d")['Close'].iloc[-1]

# 結果を表示
print("--------------------------------------------------")
print(f"トヨタ自動車の現在の株価: {current_price} 円")
print("--------------------------------------------------")
