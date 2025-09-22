from __future__ import annotations

import re
from typing import Dict, Optional

import numpy as np
import pandas as pd
from io import BytesIO


CANONICAL_COLS = {
    "timestamp": "timestamp",
    "rider_name": "rider_name",
    "team_name": "team_name",
    "distance_km": "distance_km",
    "duration_sec": "duration_sec",
    "power_watts": "power_watts",
    "heart_rate_bpm": "heart_rate_bpm",
    "elevation_gain_m": "elevation_gain_m",
}


def _safe_to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", utc=True).dt.tz_convert(None)


def _safe_to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _normalized_columns(df: pd.DataFrame) -> Dict[str, str]:
    norm = {c: re.sub(r"[^a-z0-9]+", "_", c.strip().lower()).strip("_") for c in df.columns}
    return norm


def _auto_guess_mapping(df: pd.DataFrame) -> Dict[str, str]:
    norm = _normalized_columns(df)
    inv = {}
    for original, normalized in norm.items():
        inv[normalized] = original

    guesses = {}

    def pick(candidates):
        for cand in candidates:
            if cand in inv:
                return inv[cand]
        return None

    guesses["timestamp"] = pick(["timestamp", "time", "date", "datetime", "start_time", "start"])
    guesses["rider_name"] = pick(["rider", "rider_name", "athlete", "athlete_name", "name"])
    guesses["team_name"] = pick(["team", "team_name", "club"])
    guesses["distance_km"] = pick(["distance_km", "distance", "km"])
    guesses["duration_sec"] = pick(["duration_sec", "seconds", "time_s", "elapsed_time", "moving_time"])
    guesses["power_watts"] = pick(["power", "avg_power", "power_watts", "np", "normalized_power"])
    guesses["heart_rate_bpm"] = pick(["hr", "bpm", "heart_rate", "heart_rate_bpm"])
    guesses["elevation_gain_m"] = pick(["elevation", "elevation_gain", "elev_gain_m", "ascent", "total_ascent"])

    return {k: v for k, v in guesses.items() if v is not None}


def load_data(
    source: str | bytes,
    uploaded_mime: Optional[str] = None,
    user_mapping: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    if isinstance(source, (bytes, bytearray)):
        # Try by mime
        excel_mimes = {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
        }
        if uploaded_mime and ("excel" in uploaded_mime or uploaded_mime in excel_mimes):
            try:
                df = pd.read_excel(BytesIO(source), engine="openpyxl")
            except Exception as exc:
                raise ValueError("Bad file format") from exc
        else:
            # Try CSV first
            try:
                df = pd.read_csv(BytesIO(source))
            except Exception:
                try:
                    df = pd.read_excel(BytesIO(source), engine="openpyxl")
                except Exception as exc:
                    raise ValueError("Bad file format") from exc
    else:
        # path string
        if source.lower().endswith((".xlsx", ".xls")):
            try:
                df = pd.read_excel(source, engine="openpyxl")
            except Exception as exc:
                raise ValueError("Bad file format") from exc
        else:
            try:
                df = pd.read_csv(source)
            except Exception as exc:
                raise ValueError("Bad file format") from exc

    # Build mapping: canonical -> existing column name
    auto_map = _auto_guess_mapping(df)
    mapping: Dict[str, str] = {**auto_map, **(user_mapping or {})}

    # Create a working copy with canonical names as present
    rename_map = {mapping[k]: k for k in CANONICAL_COLS.keys() if k in mapping}
    work = df.rename(columns=rename_map).copy()

    # Coerce types for known columns
    if "timestamp" in work:
        work["timestamp"] = _safe_to_datetime(work["timestamp"])

    for num_col in ["distance_km", "duration_sec", "power_watts", "heart_rate_bpm", "elevation_gain_m"]:
        if num_col in work:
            work[num_col] = _safe_to_numeric(work[num_col])

    # Ensure essential identification columns exist
    if "rider_name" not in work:
        work["rider_name"] = "Unknown"
    if "team_name" not in work:
        work["team_name"] = "Unknown"

    # Drop rows with no timestamp if timestamp exists
    if "timestamp" in work:
        work = work.dropna(subset=["timestamp"])

    # Derive useful fields
    if "duration_sec" in work and "distance_km" in work:
        with np.errstate(divide="ignore", invalid="ignore"):
            work["speed_kmh"] = np.where(
                work["duration_sec"] > 0,
                (work["distance_km"] / (work["duration_sec"] / 3600.0)),
                np.nan,
            )
    else:
        work["speed_kmh"] = np.nan

    return work


def add_time_granularities(df: pd.DataFrame) -> pd.DataFrame:
    if "timestamp" not in df:
        # Create placeholders so grouping still works; treat all data as one day/year
        df["timestamp"] = pd.Timestamp("1970-01-01")

    df = df.copy()
    ts = pd.to_datetime(df["timestamp"], errors="coerce")

    df["hour"] = ts.dt.floor("h")
    df["day"] = ts.dt.date.astype("datetime64[ns]")
    df["week"] = ts.dt.to_period("W").apply(lambda p: p.start_time)
    df["month"] = ts.dt.to_period("M").apply(lambda p: p.start_time)
    df["quarter"] = ts.dt.to_period("Q").apply(lambda p: p.start_time)
    df["year"] = ts.dt.to_period("Y").apply(lambda p: p.start_time)
    return df


def aggregate_by_period(
    df: pd.DataFrame,
    period: str,
    group_levels: list[str],
    metric: str,
    agg_func: str = "sum",
) -> pd.DataFrame:
    if period not in ["hour", "day", "week", "month", "quarter", "year"]:
        raise ValueError("Invalid period")

    if period not in df.columns:
        df = add_time_granularities(df)

    groupers = [period] + group_levels
    agg = df.groupby(groupers, dropna=False, as_index=False).agg({metric: agg_func})
    agg = agg.sort_values(by=[period] + [metric], ascending=[True] + [False])
    return agg
