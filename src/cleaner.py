import re
import numpy as np
import pandas as pd

DEFAULT_CONFIG = {
    "remove_duplicates": True,
    "missing_strategy": "median",  # "none", "median", "mean", "drop"
    "trim_whitespace": True,
    "case_mode": "none",           # "none", "sentence", "lower", "upper", "capitalize_each_word", "toggle"
    "case_columns": None,          # None = semua kolom teks; atau list nama kolom tertentu
}

CASE_MODE_LABELS = {
    "none": "None (Keep original)",
    "sentence": "Sentence case",
    "lower": "lowercase",
    "upper": "UPPERCASE",
    "capitalize_each_word": "Capitalize Each Word",
    "toggle": "tOGGLE cASE",
}


def trim_text_series(s: pd.Series, collapse_inner_spaces: bool = True) -> pd.Series:
    """Membersihkan spasi di awal/akhir dan merapikan spasi berlebih di dalam teks."""
    def _clean_str(val):
        if pd.isna(val):
            return val
        text = str(val).strip()
        if collapse_inner_spaces:
            text = re.sub(r"\s+", " ", text)
        return text

    return s.apply(_clean_str)


def _to_sentence_case(text: str) -> str:
    """Mengkapitalisasi huruf pertama setiap kalimat (setelah awal teks atau tanda ., !, ?)."""
    lowered = text.lower()
    lowered = re.sub(r"^\s*([a-z])", lambda m: m.group(0).upper(), lowered)
    lowered = re.sub(r"([.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), lowered)
    return lowered


def _to_capitalize_each_word(text: str) -> str:
    """Kapitalisasi awal kata tanpa merusak kata ber-apostrof seperti don't -> Don't."""
    def _cap_token(token: str) -> str:
        if not token:
            return token
        if "'" in token:
            parts = token.split("'")
            parts[0] = parts[0][:1].upper() + parts[0][1:].lower() if parts[0] else ""
            for i in range(1, len(parts)):
                parts[i] = parts[i].lower()
            return "'".join(parts)
        return token[:1].upper() + token[1:].lower()

    return re.sub(r"\S+", lambda m: _cap_token(m.group(0)), text)


def apply_text_case(s: pd.Series, case_mode: str | None) -> pd.Series:
    """Menerapkan mode huruf: none, sentence, lower, upper, capitalize_each_word, toggle."""
    if not case_mode or case_mode == "none":
        return s

    def _transform(val):
        if pd.isna(val):
            return val
        text = str(val)
        if case_mode == "sentence":
            return _to_sentence_case(text)
        if case_mode == "lower":
            return text.lower()
        if case_mode == "upper":
            return text.upper()
        if case_mode == "capitalize_each_word":
            return _to_capitalize_each_word(text)
        if case_mode == "toggle":
            return text.swapcase()
        raise ValueError(f"Unsupported case_mode: {case_mode}")

    return s.apply(_transform)


def clean_dataset(df: pd.DataFrame, config: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """Menjalankan pipeline pembersihan data dan mengembalikan (df_cleaned, summary)."""
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    work_df = df.copy()

    initial_rows, initial_cols = work_df.shape
    initial_missing = int(work_df.isna().sum().sum())
    initial_duplicates = int(work_df.duplicated().sum())

    # 1. Trim whitespace
    if cfg["trim_whitespace"]:
        text_cols = work_df.select_dtypes(include=["object", "string"]).columns
        for col in text_cols:
            work_df[col] = trim_text_series(work_df[col], collapse_inner_spaces=True)

    # 2. Advanced text case
    case_mode = cfg["case_mode"]
    if case_mode and case_mode != "none":
        if cfg["case_columns"]:
            target_cols = [c for c in cfg["case_columns"] if c in work_df.columns]
        else:
            target_cols = list(work_df.select_dtypes(include=["object", "string"]).columns)

        for col in target_cols:
            work_df[col] = apply_text_case(work_df[col], case_mode)

    # 3. Remove exact duplicates
    removed_duplicates = 0
    if cfg["remove_duplicates"]:
        before_dup = len(work_df)
        work_df = work_df.drop_duplicates().reset_index(drop=True)
        removed_duplicates = before_dup - len(work_df)

    # 4. Handle missing values
    strategy = cfg["missing_strategy"]
    rows_dropped_missing = 0
    numeric_filled_cells = 0

    if strategy == "drop":
        before_drop = len(work_df)
        work_df = work_df.dropna().reset_index(drop=True)
        rows_dropped_missing = before_drop - len(work_df)
    elif strategy in ("median", "mean"):
        num_cols = work_df.select_dtypes(include=[np.number]).columns
        for col in num_cols:
            na_count = int(work_df[col].isna().sum())
            if na_count > 0:
                fill_val = work_df[col].median() if strategy == "median" else work_df[col].mean()
                if pd.notna(fill_val):
                    work_df[col] = work_df[col].fillna(fill_val)
                    numeric_filled_cells += na_count

    final_rows, final_cols = work_df.shape
    final_missing = int(work_df.isna().sum().sum())
    final_duplicates = int(work_df.duplicated().sum())

    summary = {
        "initial_rows": initial_rows,
        "final_rows": final_rows,
        "initial_cols": initial_cols,
        "final_cols": final_cols,
        "initial_duplicates": initial_duplicates,
        "final_duplicates": final_duplicates,
        "removed_duplicates": removed_duplicates,
        "initial_missing": initial_missing,
        "final_missing": final_missing,
        "numeric_filled_cells": numeric_filled_cells,
        "rows_dropped_missing": rows_dropped_missing,
        "applied_config": cfg,
    }

    return work_df, summary