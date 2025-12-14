import yfinance as yf
import pandas as pd
import time

def fetch_stock_data_in_batches(tickers: list[str], batch_size: int = 3) -> pd.DataFrame:
    data_frames = []

    for i in range(0, len(tickers), batch_size):
        batch_tickers = tickers[i:i + batch_size]

        print(f"処理中: {batch_tickers} のデータを取得しています…")

        try:
            df_batch = yf.download(batch_tickers, period="1mo", group_by='ticker')

            if not df_batch.empty:
                data_frames.append(df_batch)

        except Exception as e:
            print(f"エラー発生({batch_tickers}): {e}")

        print("待機中(1秒)...")
        time.sleep(1)

    if data_frames:
        final_df = pd.concat(data_frames, axis=1)
        return final_df
    else:
        return pd.DataFrame()

if __name__ == "__main__":
    
    my_tickers = [
        "7203.T", "6758.T", "9227.T",
        "7974.T", "8035.T", "6861.T",
        "6098.T", "4063.T", "4502.T",
        ]
    
    result_df = fetch_stock_data_in_batches(my_tickers, batch_size=3)

    if not result_df.empty:
        print("\n--- 全データの取得完了 ---")
        print(result_df.head())

        result_df.to_excel("all_stock.xlsx")