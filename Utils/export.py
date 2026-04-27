import json
import pandas as pd


def save_json(data, path="result.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def save_csv(data, path="result.csv"):
    df = pd.DataFrame(data)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def save_xlsx(data, path="result.xlsx"):
    df = pd.DataFrame(data)
    df.to_excel(path, index=False)