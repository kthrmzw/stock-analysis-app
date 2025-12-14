import pandas as pd
import yfinance as yf
import time
import os

def load_tickers_from_text(file_path: str) -> list[str]:
    if not os.path.exists(file_path):
        return []
    processed_tickers = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            code = line.strip()
            if code.isdigit() and len(code) == 4:
                processed_tickers.append(f"{code}.T")
    return processed_tickers

def fetch_financial_metrics(tickers: list[str]) -> pd.DataFrame:
    results = []
    print(f"全{len(tickers)}銘柄の指標データを取得します...")

    for code in tickers:
        print(f"取得中: {code} ... ", end="")
        try:
            ticker_info = yf.Ticker(code)
            info = ticker_info.info
            data = {
                "コード": code,
                "会社名": info.get("longName","不明"),
                "現在値": info.get("currentPrice", 0),
                "PER(予)": info.get("forwardPE", None),
                "PBR": info.get("priceToBook", None),
                "ROE": info.get("returnOnEquity", None),
                "配当利回り": info.get("dividendYield", 0),
                "時価総額": info.get("marketCap", 0)
            }
            results.append(data)
            print("OK")
            time.sleep(1)
        except Exception as e:
            print(f"エラーが発生しました: {e}")
        time.sleep(1)
    return pd.DataFrame(results)

if __name__ == "__main__":
    input_file = "tickers.txt"
    my_tickers = load_tickers_from_text(input_file)

    if my_tickers:
        df_metrics = fetch_financial_metrics(my_tickers)

        if "配当利回り" in df_metrics.columns:
            df_metrics["配当利回り"] = df_metrics["配当利回り"] * 100
        
        print("\n--- 取得結果 ---")
        print(df_metrics.head())

        df_metrics.to_excel("financial_metrics.xlsx", index=False)
        print("Excelファイルに保存しました")
    else:
        print("銘柄リストが読み込めませんでした")