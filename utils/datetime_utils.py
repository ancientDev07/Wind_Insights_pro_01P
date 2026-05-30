# import pandas as pd
# from models.scada_utils import detect_timestamp_column as find_timestamp_column_new

# def get_datetime_info(df):

#     if df.empty:
#         return None, None, None, None, None  
        
#     timestamp_col = find_timestamp_column(df)
#     if not timestamp_col or timestamp_col not in df.columns:
#         return "", "", "", "", None
    
#     try:
#         dates = pd.to_datetime(df[timestamp_col], errors='coerce')
#         valid_dates = dates.dropna()
#         if valid_dates.empty:
#             return "", "", "", "", timestamp_col
        
#         min_datetime = valid_dates.min()
#         max_datetime = valid_dates.max()
#         min_date = min_datetime.strftime('%d-%m-%Y')
#         max_date = max_datetime.strftime('%d-%m-%Y')
#         min_time = min_datetime.strftime('%H:%M')
#         max_time = max_datetime.strftime('%H:%M')
#         return min_date, max_date, min_time, max_time, timestamp_col
#     except Exception as e:
#         print(f"Date parsing error: {e}")
#         return "", "", "", "", timestamp_col

# # def find_timestamp_column(df):
# #     """
# #     Identify the timestamp column in a DataFrame.
# #     Args:
# #         df: pandas DataFrame
# #     Returns:
# #         str or None: Name of the timestamp column
# #     """
# #     timestamp_keywords = ['timestamp', 'datetime', 'date_time', 'time', 'date', 'created_at', 'updated_at']
# #     lower_columns = {col.lower(): col for col in df.columns}
# #     for keyword in timestamp_keywords:
# #         if keyword in lower_columns:
# #             return lower_columns[keyword]
# #     for col in df.columns:
# #         col_lower = col.lower()
# #         if any(keyword in col_lower for keyword in timestamp_keywords):
# #             return col
# #     for col in df.columns:
# #         if df[col].dtype.name.startswith('datetime'):
# #             return col
# #     return None

# # NEW:
# def find_timestamp_column(df):
#     """
#     Identify the timestamp column in a DataFrame.
#     Args:
#         df: pandas DataFrame
#     Returns:
#         str or None: Name of the timestamp column
#     """
#     from models.scada_utils import detect_timestamp_column
#     return detect_timestamp_column(df)

import re
import pandas as pd
from models.scada_utils import detect_timestamp_column

# ─────────────────────────────────────────────────────────────────
# STEP 1 — Read raw timestamp values as strings (no auto-parsing)
# ─────────────────────────────────────────────────────────────────
def _read_as_string(series: pd.Series) -> pd.Series:
    """
    Step 1: Force every value to plain string.
    Handles cases where Excel already parsed them as datetime objects —
    convert back to string so we control the format detection ourselves.
    Preserves NaN/NaT positions exactly (no row shift).
    """
    def _val_to_str(val):
        if pd.isna(val) if not isinstance(val, str) else False:
            return None
        if isinstance(val, pd.Timestamp):
            # Excel pre-parsed — reformat to DD-MM-YYYY HH:MM so step 2 can read it
            return val.strftime('%d-%m-%Y %H:%M:%S')
        return str(val).strip()

    return series.apply(_val_to_str)


# ─────────────────────────────────────────────────────────────────
# STEP 2 — Check the format of each raw string value
# ─────────────────────────────────────────────────────────────────
_SEP = r'[-/\.]'
_DATE_RE = re.compile(
    r'^(\d{1,2})' + _SEP + r'(\d{1,2})' + _SEP + r'(\d{4})'
)

def _classify_row(val: str):
    """
    Step 2: Classify a single timestamp string.

    Rule 2a: first_part > 12  → must be DD  → format is DD-MM-YYYY
    Rule 2b: second_part > 12 → must be MM  → format is MM-DD-YYYY
    Rule 2c: both <= 12       → ambiguous    → needs sequence check (Step 3)

    Returns: 'DD-MM' | 'MM-DD' | 'ambiguous' | 'unknown'
    """
    if not val:
        return 'unknown'
    m = _DATE_RE.match(val)
    if not m:
        return 'unknown'
    first, second = int(m.group(1)), int(m.group(2))

    if first > 12:
        return 'DD-MM'       # 2a: day > 12, unambiguous
    if second > 12:
        return 'MM-DD'       # 2b: month > 12 impossible, so first must be MM
    return 'ambiguous'       # 2c: both <= 12, need sequence scoring


# ─────────────────────────────────────────────────────────────────
# STEP 3 — Score & resolve ambiguous rows via sequence continuity
# ─────────────────────────────────────────────────────────────────
_MAX_GAP_MINUTES = 7 * 24 * 60   # 7 days — covers maintenance/data skips

def _score_sequence(str_series: pd.Series, dayfirst: bool) -> float:
    """
    Step 3: Parse the sample with a given dayfirst assumption,
    then score how many consecutive pairs are:
      - strictly increasing  (time moves forward)
      - gap <= 7 days        (rules out format-flip jumps, allows real skips)

    Score = good_pairs / total_pairs  →  0.0 to 1.0
    Higher score = this format interpretation is more likely correct.

    Example — data: 02-01-2023, 02-02-2023, 01-03-2023
      dayfirst=True  → 1-Feb, 2-Feb, 1-Mar  → gaps: +1d, +27d  → score 1.0  ✓
      dayfirst=False → 2-Jan, 2-Feb, 3-Jan  → gaps: +31d, -30d → score 0.5  ✗
    """
    parsed = pd.to_datetime(str_series, dayfirst=dayfirst, errors='coerce')
    valid = parsed.dropna()
    if len(valid) < 2:
        return 0.0
    delta_min = valid.diff().dropna().dt.total_seconds() / 60
    good = ((delta_min > 0) & (delta_min <= _MAX_GAP_MINUTES)).sum()
    return good / len(delta_min)


def _detect_dayfirst(str_series: pd.Series) -> bool:
    """
    Step 3 (continued): Full format decision.

    Priority order:
      1. If unambiguous votes (>12 rule) clearly dominate → use that
      2. Otherwise → score both formats on sequence continuity
      3. Tie → DD-MM wins (Indian SCADA standard)
    """
    sample = str_series.dropna().head(300)

    dd_mm_votes = 0
    mm_dd_votes = 0

    for val in sample:
        result = _classify_row(val)
        if result == 'DD-MM':
            dd_mm_votes += 1
        elif result == 'MM-DD':
            mm_dd_votes += 1
        # 'ambiguous' and 'unknown' → go to sequence scoring

    # Unambiguous votes are strong — if one side has clear majority, trust it
    total_votes = dd_mm_votes + mm_dd_votes
    if total_votes > 0:
        if dd_mm_votes > mm_dd_votes:
            return True   # DD-MM confirmed by unambiguous rows
        if mm_dd_votes > dd_mm_votes:
            return False  # MM-DD confirmed by unambiguous rows

    # All rows ambiguous (all parts <= 12) → use sequence scoring
    score_dd = _score_sequence(sample, dayfirst=True)
    score_mm = _score_sequence(sample, dayfirst=False)
    return score_dd >= score_mm   # DD-MM wins on tie


# ─────────────────────────────────────────────────────────────────
# STEP 4 — Parse to standard DD-MM-YYYY, store as ISO for DB
# ─────────────────────────────────────────────────────────────────
def parse_and_normalize_timestamps(series: pd.Series) -> pd.Series:
    """
    Step 4: Full pipeline — detect format → parse → return pd.Timestamp series.

    IMPORTANT — data alignment guarantee:
      - Output series has IDENTICAL index and length as input
      - Rows that were NaN/NaT/missing → remain NaT (not dropped, not shifted)
      - Only the timestamp column values change, nothing else moves

    Pass 1: Bulk parse entire column with detected format
    Pass 2: Row-level fallback for any remaining NaT (mixed rows)
    Pass 3: Still NaT → genuine missing data → kept as NaT → saved as NULL in DB
    """
    if series.empty:
        return series

    # Already proper datetime (e.g. ISO strings from DB on reload) — done
    if pd.api.types.is_datetime64_any_dtype(series):
        return series

    # Step 1: normalise to strings, preserving index
    str_series = _read_as_string(series)

    # Steps 2+3: detect correct format
    dayfirst = _detect_dayfirst(str_series.dropna())

    # Step 4 Pass 1: bulk parse — fast, vectorised
    parsed = pd.to_datetime(str_series, dayfirst=dayfirst, errors='coerce')

    # Step 4 Pass 2: row-level fallback for NaT rows only
    # (handles genuinely mixed rows without touching correctly parsed rows)
    nat_mask = parsed.isna() & series.notna()
    if nat_mask.any():
        parsed[nat_mask] = pd.to_datetime(
            str_series[nat_mask], dayfirst=not dayfirst, errors='coerce'
        )

    # Result: pd.Timestamp per row, NaT for missing — index unchanged
    return parsed


def to_iso_string(series: pd.Series) -> pd.Series:
    """
    Converts parsed Timestamp series → ISO 8601 strings for DB storage.
    NaT → None (stored as NULL in SQLite).
    Called in _save_turbine_data before executemany.
    """
    return series.apply(
        lambda v: v.strftime('%Y-%m-%dT%H:%M:%S') if pd.notna(v) else None
    )


# ─────────────────────────────────────────────────────────────────
# Public helpers used by rest of app
# ─────────────────────────────────────────────────────────────────
def get_datetime_info(df):
    """Returns (min_date, max_date, min_time, max_time, col_name) in DD-MM-YYYY."""
    if df.empty:
        return None, None, None, None, None

    timestamp_col = find_timestamp_column(df)
    if not timestamp_col or timestamp_col not in df.columns:
        return "", "", "", "", None

    try:
        dates = parse_and_normalize_timestamps(df[timestamp_col]).dropna()
        if dates.empty:
            return "", "", "", "", timestamp_col
        return (
            dates.min().strftime('%d-%m-%Y'),
            dates.max().strftime('%d-%m-%Y'),
            dates.min().strftime('%H:%M'),
            dates.max().strftime('%H:%M'),
            timestamp_col
        )
    except Exception as e:
        print(f"Date parsing error: {e}")
        return "", "", "", "", timestamp_col


def find_timestamp_column(df):
    return detect_timestamp_column(df)