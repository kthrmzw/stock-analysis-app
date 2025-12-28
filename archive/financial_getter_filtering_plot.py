import pandas as pd
import yfinance as yf
import time
import os
import matplotlib.pyplot as plt
import japanize_matplotlib
import matplotlib.ticker as ticker

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

def visualize_market_cap(df, output_file="market_cap_graph.png"):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(df["会社名"], df["時価総額"], color="skyblue")

    ax.set_title("割安・高配当銘柄の時価総額比較", fontsize=16)
    ax.set_xlabel("銘柄名", fontsize=12)
    ax.set_ylabel("時価総額", fontsize=12)

    def trillion_formatter(x, pos):
        return f'{x / 1_000_000_000_000:.1f}兆円'

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(trillion_formatter))

    ax.grid(axis='y', linestyle='--', alpha=0.7)

    print(f"グラフを画像として保存します:{output_file}")
    plt.savefig(output_file, bbox_inches='tight', dpi=100)
#   plt.show()
    plt.close(fig)


if __name__ == "__main__":
    input_file = "tickers.txt"
    my_tickers = load_tickers_from_text(input_file)

    if my_tickers:
        df_metrics = fetch_financial_metrics(my_tickers)
        
        

#       if "配当利回り" in df_metrics.columns:
#           df_metrics["配当利回り"] = df_metrics["配当利回り"].fillna(0)
#           df_metrics["配当利回り"] = df_metrics["配当利回り"] * 100
        
        df_filtered = df_metrics[
            (df_metrics["時価総額"] >= 1000000000000)
        ]

        print("\n--- お宝銘柄候補 ---")
        if not df_filtered.empty:
            print(df_filtered[["コード", "会社名", "PER(予)", "配当利回り", "時価総額"]])
            visualize_market_cap(df_filtered, "my_portfolio_analysis.png")
            print("グラフを保存しました")
        else:
            print("候補が見つかりませんでした")

        df_filtered.to_excel("filtered_financial_metrics.xlsx", index=False)
        print("Excelファイルに保存しました")
    else:
        print("銘柄リストが読み込めませんでした")