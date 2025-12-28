import yfinance as yf

# トヨタ自動車(7203.T)を例にする
ticker = yf.Ticker("7203.T")

# 損益計算書（Income Statement）を取得
df_income = ticker.income_stmt

print("=== 取得できる項目一覧 (Index) ===")
for item in df_income.index:
    print(item)

print("\n=== 最新のデータ例 ===")
# "Total Revenue" (売上高) と "Net Income" (純利益) を表示
print(df_income.loc[["Total Revenue", "Net Income"]])