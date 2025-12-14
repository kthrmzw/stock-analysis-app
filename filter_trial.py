import pandas as pd

def filter_promising_stocks(df: pd.DataFrame) -> pd.DataFrame:
    clean_df=df.dropna(subset=["PER", "配当利回り%"])
    condition_per = clean_df["PER"] <= 15.0
    condition_yield = clean_df["配当利回り%"] >= 3.0
    filtered_df = clean_df[condition_per & condition_yield]
    return filtered_df

if __name__ == "__main__":
    data = {
        "コード": ["7203.T", "6758.T", "8058.T", "9434.T", "9984.T"],
        "社名": ["トヨタ", "ソニーG", "三菱商事", "ソフトバンク", "SBG"],
        "PER": [10.5, 18.2, 11.0, 14.5, 12.0],  # PER(倍)
        "配当利回り%": [2.8, 0.6, 3.5, 5.2, 0.5] # 利回り(%)
    }
    df_test = pd.DataFrame(data)

    print("--- 元のリスト ---")
    print(df_test)

    result = filter_promising_stocks(df_test)

    print("\n--- スクリーニング結果(PER<=15 & 利回り>=3% ---")
    print(result)