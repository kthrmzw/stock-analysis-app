import yfinance as yf
import pandas as pd
from datetime import datetime

def fetch_and_export_stock_data(tickers: list[str], file_name: str) -> None:
    print(f"データ取得を開始します:{tickers}")

    try:
        df = yf.download(tickers, period="1mo", group_by='ticker')

        if df.empty:
            print("データが取得できませんでした。ネット接続やコードを確認してください。")
            return
        
        print("\n--- 取得データの先頭(5行) ---")
        print(df.head())

        df.to_excel(file_name)

        print(f"\n成功: '{file_name}'にデータを保存しました。")

    except PermissionError:
        print(f"エラー: '{file_name}' を開いていませんか？ファイルを閉じてから再実行してください。")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    target_tickers = ["7203.T", "6758.T", "9227.T"]

    today_str = datetime.now().strftime("%Y%m%d")
    output_file = f"stock_prices_{today_str}.xlsx"

    fetch_and_export_stock_data(target_tickers, output_file)