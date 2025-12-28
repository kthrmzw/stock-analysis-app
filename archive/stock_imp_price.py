import yfinance as yf
import pandas as pd
import os
import time

def load_tickers_from_text(file_path: str) -> list[str]:
    if not os.path.exists(file_path):
        print(f"エラー: '{file_path}' が見つかりません。")
        return []
    processed_tickers = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            code = line.strip()

            if not code:
                continue

            if code.isdigit() and len(code) == 4:
                formatted_code = f"{code}.T"
                processed_tickers.append(formatted_code)
            else:
                print(f"スキップしました(形式不備): {code}")
        return processed_tickers

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
    input_file = "tickers.txt"

#    with open(input_file, "w", encoding="utf-8") as f:
#        f.write("7203\n6758\n9227\n")
#        print(f"確認: '{input_file}' を作成しました。")

    my_tickers = load_tickers_from_text(input_file)

    print("\n--- 変換結果 ---")
    print(f"読み込んだリスト: {my_tickers}")

    result_df = fetch_stock_data_in_batches(my_tickers, batch_size=3)

    if not result_df.empty:
        print("\n--- 全データの取得完了 ---")
        print(result_df.head())

        result_df.to_excel("all_stock.xlsx")