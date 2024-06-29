import json
import os
import pandas as pd
import html
import re

from py_logger import get_logger

logger = get_logger(__name__)


def save_to_json(data: list, filepath: str):
    """Save data to json file"""
    with open(filepath, "w") as fh:
        json.dump(data, fh, indent=4, ensure_ascii=False)


def load_from_json(filepath: str) -> list:
    """Load data from json file"""
    with open(filepath, "r") as fh:
        data = json.load(fh)
    return data


def save_to_csv(data: list, filepath: str):
    """Save data to csv file"""
    df = pd.json_normalize(data)
    df.to_csv(filepath, index=False)


def load_from_csv(filepath: str) -> pd.DataFrame:
    """Load data from csv file"""
    with open(filepath, "r") as fh:
        data = pd.read_csv(fh)
    return data


def load_data_to_excel(data: dict, filepath: str, sheet_name: str):
    """Save data to Excel file"""
    df = pd.DataFrame(data)
    with pd.ExcelWriter(filepath, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        logger.info(f"Updated file {filepath}")


def drop_columns(data: list, columns: list) -> list:
    """Drop columns from data"""
    df = pd.DataFrame(data)
    df.drop(columns, axis=1, inplace=True)
    return df.to_dict(orient="records")


def clean_html(data: list, columns: list) -> list:
    """Clean HTML tags from data"""
    df = pd.DataFrame(data)

    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column {col} is empty.")
            continue

        # Use apply to apply functions to each element in the Series
        df[col] = df[col].apply(lambda x: html.unescape(x) if isinstance(x, str) else x)
        df[col] = df[col].apply(lambda x: re.sub('<[^<]+?>', '', x) if isinstance(x, str) else x)
        df[col] = df[col].apply(lambda x: x.replace('&nbsp;', ' ') if isinstance(x, str) else x)

    return df.to_dict(orient="records")