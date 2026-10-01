import streamlit as st
import pandas as pd
import numpy as np
import logging
import traceback
import html
import io
import json
import os
from urllib.request import urlopen
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Today's Projection",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# STYLING
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root {
    --ink: #172033;
    --muted: #6b7280;
    --line: #e7eaf0;
    --surface: #ffffff;
    --surface-soft: #f7f8fb;
    --gold: #d99a17;
    --gold-2: #f3c64f;
    --gold-soft: #fff8e6;
    --blue: #2563eb;
    --blue-soft: #eff6ff;
    --green: #15803d;
    --green-soft: #ecfdf3;
    --red: #b91c1c;
    --red-soft: #fef2f2;
    --shadow: 0 8px 30px rgba(23,32,51,.07);
    --shadow-sm: 0 3px 14px rgba(23,32,51,.055);
}

.stApp {
    background:
        radial-gradient(circle at 8% 0%, rgba(243,198,79,.12), transparent 25rem),
        radial-gradient(circle at 92% 4%, rgba(37,99,235,.055), transparent 22rem),
        #f5f7fa;
}
.main .block-container {
    max-width: 1440px;
    padding: 1.25rem 2rem 3rem;
}
[data-testid="stHeader"] {
    background: rgba(245,247,250,.78);
}
[data-testid="stAppViewContainer"] {
    background: transparent;
}

html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
                 "Segoe UI", sans-serif;
}
h1, h2, h3, h4 {
    color: var(--ink) !important;
    letter-spacing: -.025em;
}
p, .stCaption {
    color: var(--muted);
}
hr {
    border: 0 !important;
    border-top: 1px solid var(--line) !important;
    margin: 1.35rem 0 !important;
}

.app-header {
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px 24px;
    margin: 0 0 20px;
    border: 1px solid rgba(217,154,23,.22);
    border-radius: 20px;
    background: linear-gradient(135deg, #fffdf7 0%, #ffffff 55%, #f8fafc 100%);
    box-shadow: var(--shadow);
}
.app-header:after {
    content: "";
    position: absolute;
    width: 220px;
    height: 220px;
    right: -90px;
    top: -120px;
    border-radius: 50%;
    background: rgba(243,198,79,.14);
}
.app-header-icon {
    position: relative;
    z-index: 1;
    display: grid;
    place-items: center;
    width: 54px;
    height: 54px;
    flex: 0 0 54px;
    border-radius: 16px;
    background: linear-gradient(135deg,#f9d66f,#d99a17);
    box-shadow: 0 7px 18px rgba(217,154,23,.22);
    font-size: 1.65rem;
}
.app-header-copy { position: relative; z-index: 1; }
.app-header-title {
    margin: 0;
    color: var(--ink);
    font-size: 1.65rem;
    font-weight: 850;
    line-height: 1.1;
}
.app-header-subtitle {
    margin: 6px 0 0;
    color: #697386;
    font-size: .9rem;
    line-height: 1.45;
}

.section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 20px 0 7px;
}
.section-title .accent {
    width: 5px;
    height: 28px;
    flex: 0 0 5px;
    border-radius: 999px;
    background: linear-gradient(180deg,#f4c11a,#d99a17);
}
.section-title .text {
    font-size: 1.12rem;
    font-weight: 800;
    color: var(--ink);
}
.section-title .layer {
    margin-left: 4px;
    padding: 4px 9px;
    border-radius: 999px;
    font-size: .64rem;
    font-weight: 800;
    letter-spacing: .06em;
    text-transform: uppercase;
}
.layer.l1 { color:#1d4ed8; background:#eff6ff; border:1px solid #bfdbfe; }
.layer.l2 { color:#9a6700; background:#fff8e6; border:1px solid #f3d38b; }
.layer.l3 { color:#166534; background:#ecfdf3; border:1px solid #bbf7d0; }

.callout {
    border-radius: 14px;
    padding: 13px 16px;
    margin: 10px 0 16px;
    font-size: .86rem;
    line-height: 1.5;
    box-shadow: 0 2px 10px rgba(23,32,51,.025);
}
.callout-info { background:#f0f7ff; border:1px solid #cfe3ff; border-left:4px solid #3b82f6; color:#174a86; }
.callout-warn { background:#fff9eb; border:1px solid #f3dfaa; border-left:4px solid #d99a17; color:#765100; }
.callout-ok   { background:#effbf3; border:1px solid #c7edd2; border-left:4px solid #22a35a; color:#176331; }
.callout-bad  { background:#fff3f3; border:1px solid #f2cccc; border-left:4px solid #dc2626; color:#8c2020; }

div[data-testid="stMetric"] {
    min-height: 108px;
    padding: 16px 18px;
    border: 1px solid var(--line);
    border-radius: 16px;
    background: rgba(255,255,255,.92);
    box-shadow: var(--shadow-sm);
    transition: transform .18s ease, box-shadow .18s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(23,32,51,.09);
}
div[data-testid="stMetric"] label {
    color: #7a8495 !important;
    font-size: .67rem !important;
    font-weight: 750 !important;
    text-transform: uppercase;
    letter-spacing: .08em;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: var(--ink) !important;
    font-weight: 850 !important;
    font-size: 1.75rem !important;
    letter-spacing: -.035em;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#ffffff 0%,#f7f8fb 100%);
    border-right: 1px solid var(--line);
}
section[data-testid="stSidebar"] > div {
    padding: 1rem .9rem 1.5rem;
}
section[data-testid="stSidebar"] [data-testid="stExpander"] {
    border: 1px solid var(--line);
    border-radius: 14px;
    background: #fff;
    margin: 8px 0;
    box-shadow: 0 2px 10px rgba(23,32,51,.035);
}
section[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    font-weight: 750;
}
.sidebar-brand {
    padding: 8px 6px 14px;
}
.sidebar-brand .title {
    font-size: 1rem;
    font-weight: 850;
    color: var(--ink);
}
.sidebar-brand .sub {
    margin-top: 3px;
    color: #8a93a3;
    font-size: .72rem;
}

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
[data-testid="stDateInput"] input {
    border-radius: 10px !important;
    border-color: #dfe3ea !important;
}
div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="select"] > div:focus-within {
    border-color: #d7a52a !important;
    box-shadow: 0 0 0 2px rgba(217,154,23,.10) !important;
}
label {
    font-weight: 650 !important;
    color: #465166 !important;
}

.stButton > button,
.stDownloadButton > button {
    border-radius: 10px !important;
    min-height: 42px;
    font-weight: 750 !important;
    border: 1px solid #dfe3ea !important;
    background: #fff !important;
    color: #273248 !important;
    box-shadow: 0 2px 8px rgba(23,32,51,.04);
    transition: all .18s ease;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: #d5a72d !important;
    color: #8a6100 !important;
    transform: translateY(-1px);
    box-shadow: 0 5px 14px rgba(23,32,51,.08);
}
button[kind="primary"] {
    background: linear-gradient(135deg,#e7b52d,#c98a0e) !important;
    color: #fff !important;
    border-color: #c98a0e !important;
}

button[data-baseweb="tab"] {
    font-weight: 750 !important;
    font-size: .88rem !important;
    color: #697386 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #8a6100 !important;
}
div[data-baseweb="tab-highlight"] {
    background: linear-gradient(90deg,#e8b52c,#d99a17) !important;
    height: 3px !important;
    border-radius: 999px;
}

div[data-testid="stDataFrame"] {
    border: 1px solid var(--line);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
}

.hero-card {
    background: linear-gradient(135deg,#ffffff 0%,#fafbfd 100%);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 20px 22px;
    margin: 12px 0 18px;
    box-shadow: var(--shadow);
}
.hero-card .metal-title { font-size:1.08rem; font-weight:800; color:var(--ink); margin-bottom:4px; }
.hero-card .rate-line { font-size:.86rem; color:#70798a; margin-bottom:13px; }
.hero-card .arrow-up { color:#15803d; font-weight:850; }
.hero-card .arrow-down { color:#b91c1c; font-weight:850; }
.hero-card .arrow-flat { color:#2563eb; font-weight:850; }

.rel-high,.rel-med,.rel-low,.rel-rough {
    display:inline-block; padding:5px 11px; border-radius:999px;
    font-size:.72rem; font-weight:800; border:1px solid transparent;
}
.rel-high { background:#ecfdf3; color:#166534; border-color:#bbf7d0; }
.rel-med { background:#eff6ff; color:#1d4ed8; border-color:#bfdbfe; }
.rel-low { background:#fff8e6; color:#8a6100; border-color:#f3d38b; }
.rel-rough { background:#fef2f2; color:#991b1b; border-color:#fecaca; }

.range-chip {
    display:inline-block; background:#f6f7fa; border:1px dashed #cdd3de;
    color:#4b5563; padding:4px 10px; border-radius:999px;
    font-size:.73rem; font-weight:700; margin-top:6px;
}
.metric-label {
    font-size:.68rem; color:#7a8495; text-transform:uppercase;
    letter-spacing:.07em; font-weight:750; margin-bottom:4px;
}
.metric-value { font-size:1.85rem; font-weight:850; color:var(--ink); line-height:1.1; }
.pill {
    display:inline-block; padding:4px 9px; border-radius:999px;
    font-size:.68rem; font-weight:800; margin-right:5px; margin-bottom:4px;
}
.pill-ok { background:#ecfdf3; color:#166534; border:1px solid #bbf7d0; }
.pill-warn { background:#fff8e6; color:#8a6100; border:1px solid #f3d38b; }
.pill-info { background:#eff6ff; color:#1d4ed8; border:1px solid #bfdbfe; }

.rate-step {
    display:inline-block; padding:5px 10px; margin:3px 4px 3px 0;
    border-radius:9px; font-size:.78rem; font-weight:750;
    background:#f7f8fa; border:1px solid #dde2ea;
}
.rate-step.up { background:#ecfdf3; border-color:#bbf7d0; color:#166534; }
.rate-step.down { background:#fef2f2; border-color:#fecaca; color:#991b1b; }
.rate-step.start { background:#eff6ff; border-color:#bfdbfe; color:#1d4ed8; }

.step-card {
    border:1px solid var(--line); border-radius:15px; padding:15px 17px;
    margin:10px 0; background:#fff; box-shadow:var(--shadow-sm);
}
.step-card.step-first { border-left:5px solid #3b82f6; }
.step-card.step-up { border-left:5px solid #22a35a; }
.step-card.step-down { border-left:5px solid #dc2626; }
.step-card.step-flat { border-left:5px solid #9ca3af; }
.step-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }
.step-badge {
    display:inline-block; padding:3px 9px; border-radius:999px;
    font-size:.65rem; font-weight:850; letter-spacing:.06em; text-transform:uppercase;
}
.step-badge.start { background:#eff6ff; color:#1d4ed8; }
.step-badge.up { background:#ecfdf3; color:#166534; }
.step-badge.down { background:#fef2f2; color:#991b1b; }
.step-badge.flat { background:#f3f4f6; color:#4b5563; }
.step-rate { font-size:1.35rem; font-weight:850; color:var(--ink); }
.step-delta { font-size:.86rem; font-weight:800; margin-left:7px; }
.step-delta.up { color:#166534; } .step-delta.down { color:#991b1b; } .step-delta.flat { color:#6b7280; }
.step-time { font-size:.8rem; color:#70798a; font-weight:650; }
.step-metrics {
    display:grid; grid-template-columns:repeat(7,minmax(0,1fr));
    gap:8px; margin-top:10px;
}
.step-metric { background:#f8f9fb; border:1px solid #edf0f4; border-radius:9px; padding:8px 9px; }
.step-metric .lab { font-size:.61rem; color:#7a8495; text-transform:uppercase; letter-spacing:.04em; font-weight:800; }
.step-metric .val { font-size:1rem; font-weight:850; color:var(--ink); margin-top:2px; }
.step-metric .rng { font-size:.66rem; color:#7a8495; margin-top:2px; }
.behavior-insight {
    padding:10px 13px; background:#f8faff; border:1px solid #e4ecfb;
    border-left:3px solid #3b82f6; border-radius:9px; margin:6px 0;
    font-size:.84rem; color:#26364f; line-height:1.5;
}
.layer-badge {
    display:inline-block; padding:3px 9px; border-radius:999px;
    font-size:.64rem; font-weight:850; letter-spacing:.05em; margin-left:7px; text-transform:uppercase;
}
.layer-badge.l1 { background:#eff6ff; color:#1d4ed8; border:1px solid #bfdbfe; }
.layer-badge.l2 { background:#fff8e6; color:#8a6100; border:1px solid #f3d38b; }
.layer-badge.l3 { background:#ecfdf3; color:#166534; border:1px solid #bbf7d0; }

[data-testid="stExpander"] {
    border-color: var(--line) !important;
    border-radius: 14px !important;
    background: rgba(255,255,255,.85) !important;
}

div[data-testid="stAlert"] { border-radius: 12px; }

@media (max-width: 1000px) {
    .main .block-container { padding-left:1rem; padding-right:1rem; }
    .step-metrics { grid-template-columns:repeat(4,minmax(0,1fr)); }
}
@media (max-width: 700px) {
    .app-header { padding:16px; border-radius:15px; }
    .app-header-title { font-size:1.3rem; }
    .app-header-subtitle { font-size:.8rem; }
    .step-metrics { grid-template-columns:repeat(2,minmax(0,1fr)); }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { font-size:1.45rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-header-icon">🥇</div>
    <div class="app-header-copy">
        <div class="app-header-title">Today's Projection</div>
        <div class="app-header-subtitle">
            Context-aware customer behaviour model · rate movements → customer response → today's projection
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────
REQUIRED_COLS = [
    "Date", "Metal Type", "Metal Rate",
    "Saved Amount", "Installment number",
]

NUMERIC_COLS = [
    "Metal Rate", "Saved Amount", "Reward Amount",
    "Benefit Metal Amount", "Refunded Amount",
    "Saved Metal Weight", "Rewards Metal Weight",
    "Benefit Metal Weight", "Benefit Metal Percentage",
    "Installment number",
]

FLAT_TOLERANCE = 0.01
EXACT_RUPEE_TOLERANCE = 0.01
MORNING_RATE_START = pd.Timestamp("09:30:00").time()

DEFAULT_START_TIME = "12:00 am"
DEFAULT_EOD_TIME = "11:59 pm"

DEFAULT_MATCH_TOLERANCE_RS = 5.0
MAX_PATTERN_MATCHES = None
MIN_DAYS_APART = 0
MIN_WINDOW_DAYS = 1
PATTERN_WINDOW = 5
OUTCOME_OFFSET = 0

RECENCY_WEIGHT = 0.30
RECENCY_DECAY_DAYS = 60.0
RECENT_BASELINE_DAYS = 7
SCALE_MIN, SCALE_MAX = 0.5, 2.0
CUST_METRICS = ["Enrolment", "Enrolment Amount", "Collection Count",
                "Collection", "Saved Weight", "Reward Weight", "Total Weight"]

INTRADAY_EXPECTED_MIN = 1
INTRADAY_EXPECTED_MAX = 3

MAX_DAILY_CHANGES = 5

# ─────────────────────────────────────────────────────────────
# DEFAULT DATA SOURCE
# ─────────────────────────────────────────────────────────────
DEFAULT_DATA_PATH = Path(__file__).resolve().parent / "transaction_data.xlsx"
DEFAULT_DATA_URL = (
    "https://raw.githubusercontent.com/corpedp2024-pixel/"
    "RatePulse/main/transaction_data.xlsx"
)

# ─────────────────────────────────────────────────────────────
# PERSISTENT RATE STORAGE
# ─────────────────────────────────────────────────────────────
RATE_STORE_PATH = Path(__file__).parent / "rate_timelines.json"


def _load_rate_store():
    """Load the whole persistent rate store from disk."""
    if not RATE_STORE_PATH.exists():
        return {}
    try:
        with open(RATE_STORE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_rate_store(store):
    """Persist the whole rate store to disk atomically."""
    try:
        tmp = RATE_STORE_PATH.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2, ensure_ascii=False)
        os.replace(tmp, RATE_STORE_PATH)
    except OSError as exc:
        logger.warning("Could not persist rate store: %s", exc)


def _store_key(metal, projection_date):
    return f"{metal}::{pd.Timestamp(projection_date).strftime('%Y-%m-%d')}"


def load_saved_timeline(metal, projection_date):
    """
    Return the saved list of {id, time, rate} for this (metal, date),
    or None if nothing has been saved yet.
    """
    store = _load_rate_store()
    key = _store_key(metal, projection_date)
    rows = store.get(key)
    if not isinstance(rows, list) or not rows:
        return None
    cleaned = []
    for i, r in enumerate(rows):
        try:
            cleaned.append({
                "id": i,
                "time": str(r.get("time", "12:00 am")),
                "rate": float(r.get("rate", 0.0)),
            })
        except (TypeError, ValueError):
            continue
    return cleaned or None


def save_timeline(metal, projection_date, rows):
    """Persist the given rows for this (metal, date)."""
    store = _load_rate_store()
    key = _store_key(metal, projection_date)
    store[key] = [
        {"time": str(r.get("time", "")), "rate": float(r.get("rate", 0.0))}
        for r in rows
    ]
    _save_rate_store(store)


def has_saved_timeline(metal, projection_date):
    store = _load_rate_store()
    key = _store_key(metal, projection_date)
    rows = store.get(key)
    return isinstance(rows, list) and len(rows) > 0


# ─────────────────────────────────────────────────────────────
# CUSTOMER REACTION (Layer ①)
# ─────────────────────────────────────────────────────────────
CUSTOMER_REACTION_DAYS = 30
CUSTOMER_REACTION_DAYS_OPTIONS = [7, 15, 30, 60, 90]

REACTION_METRICS = [
    "Enrolment",
    "Enrolment Amount",
    "Collection Count",
    "Collection",
    "Saved Weight",
    "Reward Weight",
    "Total Weight",
]

RATE_MAGNITUDE_BUCKETS = [
    (0,   50,  "₹1–50"),
    (51,  100, "₹51–100"),
    (101, 200, "₹101–200"),
    (201, 1e9, "₹201+"),
]

REACTION_MIN_GROUP_DAYS = 3

# ─────────────────────────────────────────────────────────────
# BEHAVIOUR-DRIVEN PROJECTION (Context-Aware)
# ─────────────────────────────────────────────────────────────
BEHAVIOR_MODEL_DAYS = 30
BEHAVIOR_BASELINE_DAYS = 14
BEHAVIOR_MIN_BUCKET_DAYS = 3
BEHAVIOR_CONFIDENCE_HIGH = 8
BEHAVIOR_CONFIDENCE_MED = 4

BEHAVIOR_CONTEXT_LOOKBACK = 3
BEHAVIOR_RECENCY_HALFLIFE = 5.0
BEHAVIOR_TREND_BOOST = 0.30
BEHAVIOR_SPIKE_THRESHOLD = 1.8
BEHAVIOR_SPIKE_DECAY = 0.50
ACTIVE_RATE_BUCKET_RS = 50.0

CUMULATIVE_MOVE_BUCKETS = [
    (0,   50,   "₹0–50"),
    (51,  100,  "₹51–100"),
    (101, 300,  "₹101–300"),
    (301, 600,  "₹301–600"),
    (601, 1e9,  "₹601+"),
]

# ─────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gold_silver_app")


# ─────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────
def load_data(file_bytes, filename):
    if not file_bytes:
        return None
    buffer = io.BytesIO(file_bytes)
    if str(filename).lower().endswith(".csv"):
        return pd.read_csv(buffer)
    return pd.read_excel(buffer)


def _normalize_metal(x):
    s = str(x).strip().lower()
    if "gold" in s:
        return "Gold"
    if "silver" in s:
        return "Silver"
    return str(x).strip().title()


def _detect_time_column(df):
    for c in ["Time", "time", "TIME", "Transaction Time", "Timestamp",
              "timestamp", "DateTime", "Datetime"]:
        if c in df.columns:
            return c
    for c in df.columns:
        if "time" in c.lower():
            return c
    return None


def _combine_date_time(df, time_col):
    raw_t = df[time_col].astype(str).str.strip()
    as_dt = pd.to_datetime(raw_t, errors="coerce")
    padded = raw_t.where(raw_t.str.count(":") == 2, raw_t + ":00")
    date_text = df["Date"].dt.strftime("%Y-%m-%d")
    combined = pd.to_datetime(
        date_text + " " + padded,
        errors="coerce",
    )
    fallback_time = as_dt.dt.strftime("%H:%M:%S")
    fallback = pd.to_datetime(date_text + " " + fallback_time, errors="coerce")
    return combined.fillna(fallback).fillna(df["Date"])


# ─────────────────────────────────────────────────────────────
# PREPROCESS
# ─────────────────────────────────────────────────────────────
def preprocess(df):
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    stats = {
        "invalid_dates_dropped": 0,
        "invalid_time_rows": 0,
        "time_column_used": None,
        "invalid_numeric_values": {},
        "file_order": "unknown",
    }

    df["_file_row"] = np.arange(len(df))

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(
            df["Date"], errors="coerce", dayfirst=True
        )
        stats["invalid_dates_dropped"] = int(df["Date"].isna().sum())
        df = df.dropna(subset=["Date"]).copy()

    tcol = _detect_time_column(df)
    if tcol is not None and tcol != "Date":
        stats["time_column_used"] = tcol
        merged = _combine_date_time(df, tcol)
        midnight = merged.dt.time == pd.Timestamp("00:00:00").time()
        non_empty_time = (
            df[tcol].astype(str).str.strip().ne("") & df[tcol].notna()
        )
        stats["invalid_time_rows"] = int((midnight & non_empty_time).sum())
        df["Date"] = merged

    if "Metal Type" in df.columns:
        df["Metal Type"] = df["Metal Type"].map(_normalize_metal)

    for col in NUMERIC_COLS:
        if col in df.columns:
            cleaned = (
                df[col].astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("₹", "", regex=False)
                .str.replace("g", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.strip()
            )
            coerced = pd.to_numeric(cleaned, errors="coerce")
            had = cleaned.replace(
                {"": np.nan, "nan": np.nan, "None": np.nan}
            ).notna()
            n_inv = int((coerced.isna() & had).sum())
            if n_inv > 0:
                stats["invalid_numeric_values"][col] = n_inv
            df[col] = coerced.fillna(0)

    if not df.empty:
        earliest_row = int(df.loc[df["Date"].idxmin(), "_file_row"])
        latest_row = int(df.loc[df["Date"].idxmax(), "_file_row"])
        stats["file_order"] = (
            "descending (newest first)"
            if earliest_row > latest_row
            else "ascending (oldest first)"
        )

    df = df.sort_values("_file_row", kind="stable").reset_index(drop=True)
    df = df.drop(columns=["_file_row"])
    return df, stats


@st.cache_data(show_spinner=False)
def load_and_preprocess(file_bytes, filename):
    if not file_bytes:
        return None, None
    df = load_data(file_bytes, filename)
    if df is None or df.empty:
        return None, None
    return preprocess(df)


# ─────────────────────────────────────────────────────────────
# DAILY RATE
# ─────────────────────────────────────────────────────────────
DAILY_RATE_COLS = [
    "Date", "Metal Rate", "Rate Set At",
    "Day Close Rate", "Day Close At",
    "Intraday Changes", "Intraday Path", "Intraday Range ₹",
]


def build_daily_rate_series(data, metal):
    d = data[data["Metal Type"] == metal].copy()
    d = d.dropna(subset=["Date"])
    if d.empty or "Metal Rate" not in d.columns:
        return pd.DataFrame(columns=DAILY_RATE_COLS)

    d = d[d["Metal Rate"] > 0]
    if d.empty:
        return pd.DataFrame(columns=DAILY_RATE_COLS)

    d = d.sort_values("Date", kind="stable").copy()
    d["_day"] = d["Date"].dt.normalize()
    d["_rate_changed"] = d["Metal Rate"].ne(d["Metal Rate"].shift())

    rows = []
    carry_rate = None
    carry_set_at = pd.NaT
    for day, grp in d.groupby("_day", sort=True):
        grp = grp.reset_index(drop=True)
        events = grp[grp["_rate_changed"]]
        morning = events[events["Date"].dt.time >= MORNING_RATE_START]
        if not morning.empty:
            daily_row = morning.iloc[0]
            daily_rate = float(daily_row["Metal Rate"])
            daily_set_at = daily_row["Date"]
        elif carry_rate is not None:
            daily_rate = carry_rate
            daily_set_at = carry_set_at
        else:
            daily_rate = float(grp.iloc[0]["Metal Rate"])
            daily_set_at = grp.iloc[0]["Date"]

        close_row = grp.iloc[-1]
        path = grp.loc[
            grp["Metal Rate"].ne(grp["Metal Rate"].shift()), "Metal Rate"
        ].tolist()
        n_changes = max(len(path) - 1, 0)
        intraday_range = (max(path) - min(path)) if path else 0.0

        rows.append({
            "Date": day,
            "Metal Rate": daily_rate,
            "Rate Set At": daily_set_at,
            "Day Close Rate": float(close_row["Metal Rate"]),
            "Day Close At": close_row["Date"],
            "Intraday Changes": int(n_changes),
            "Intraday Path": path,
            "Intraday Range ₹": float(intraday_range),
        })
        carry_rate = float(close_row["Metal Rate"])
        carry_set_at = close_row["Date"]

    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(columns=DAILY_RATE_COLS)
    return out.sort_values("Date").reset_index(drop=True)


# ─────────────────────────────────────────────────────────────
# CUSTOMER SERIES
# ─────────────────────────────────────────────────────────────
CUST_SERIES_COLS = [
    "Date", "Enrolment", "Enrolment Amount",
    "Collection Count", "Collection",
    "Saved Weight", "Reward Weight", "Total Weight",
]


def build_daily_customer_series(data, metal, collection_col="Saved Amount"):
    d = data[data["Metal Type"] == metal].copy()
    if d.empty:
        return pd.DataFrame(columns=CUST_SERIES_COLS)

    d["_day"] = d["Date"].dt.normalize()
    rows = []
    for day, grp in d.groupby("_day", sort=True):
        enrol = grp[grp["Installment number"] == 1]
        coll = grp[grp["Installment number"] > 1]
        enr_amt = float(enrol["Saved Amount"].sum()) if "Saved Amount" in enrol else 0.0
        coll_amt = float(coll[collection_col].sum()) if collection_col in coll else 0.0
        sw = float(grp["Saved Metal Weight"].sum()) if "Saved Metal Weight" in grp.columns else 0.0
        rw = float(grp["Rewards Metal Weight"].sum()) if "Rewards Metal Weight" in grp.columns else 0.0
        rows.append({
            "Date": day,
            "Enrolment": int(len(enrol)),
            "Enrolment Amount": enr_amt,
            "Collection Count": int(len(coll)),
            "Collection": coll_amt,
            "Saved Weight": sw,
            "Reward Weight": rw,
            "Total Weight": sw + rw,
        })
    return pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)


RATE_WINDOW_COLS = [
    "Date", "Window Start", "Window End", "Window Hours",
    "Active Rate", "Rate Change ₹", "Rate Change %",
    "Daily Rate Change ₹",
    "Intraday Changes", "Intraday Range ₹",
] + CUST_SERIES_COLS[1:]


def build_rate_window_customer_series(data, metal, daily_rate):
    d = data[data["Metal Type"] == metal].copy()
    d = d.dropna(subset=["Date"])
    if d.empty or "Metal Rate" not in d.columns:
        return pd.DataFrame(columns=RATE_WINDOW_COLS)

    d = d[d["Metal Rate"] > 0].sort_values("Date", kind="stable")
    if d.empty:
        return pd.DataFrame(columns=RATE_WINDOW_COLS)

    d["_day"] = d["Date"].dt.normalize()
    daily = daily_rate.copy()
    daily["Date"] = pd.to_datetime(daily["Date"]).dt.normalize()
    daily = daily.sort_values("Date").reset_index(drop=True)
    daily["Daily Rate Change ₹"] = (
        daily["Day Close Rate"].diff().fillna(0.0)
    )
    daily_move_by_date = daily.set_index("Date")["Daily Rate Change ₹"]
    rows = []

    for day, group in d.groupby("_day", sort=True):
        prior = daily[daily["Date"] < day]
        opening_rate = (
            float(prior.iloc[-1]["Day Close Rate"])
            if not prior.empty else float(group.iloc[0]["Metal Rate"])
        )
        opening_delta = 0.0
        active_rate = opening_rate
        events = []

        for _, transaction in group.iterrows():
            transaction_rate = float(transaction["Metal Rate"])
            if abs(transaction_rate - active_rate) <= FLAT_TOLERANCE:
                continue
            event_time = pd.Timestamp(transaction["Date"])
            rate_delta = transaction_rate - active_rate
            if event_time <= day:
                opening_rate = transaction_rate
                opening_delta += rate_delta
            else:
                events.append((event_time, transaction_rate, rate_delta))
            active_rate = transaction_rate

        boundaries = [(day, opening_rate, opening_delta)] + events
        day_end = day + pd.Timedelta(days=1)
        intraday_changes = len(events) + int(abs(opening_delta) > FLAT_TOLERANCE)
        daily_row = daily[daily["Date"] == day]
        intraday_range = (
            float(daily_row.iloc[0].get("Intraday Range ₹", 0.0))
            if not daily_row.empty else 0.0
        )

        for index, (start, rate, rate_delta) in enumerate(boundaries):
            end = (boundaries[index + 1][0]
                   if index + 1 < len(boundaries) else day_end)
            hours = (end - start).total_seconds() / 3600.0
            if hours <= 0:
                continue

            transactions = group[
                (group["Date"] >= start) & (group["Date"] < end)
            ]
            enrol = transactions[
                transactions["Installment number"] == 1
            ] if "Installment number" in transactions else transactions.iloc[0:0]
            coll = transactions[
                transactions["Installment number"] > 1
            ] if "Installment number" in transactions else transactions.iloc[0:0]

            enrol_amount = (
                float(enrol["Saved Amount"].sum())
                if "Saved Amount" in enrol else 0.0
            )
            collection = (
                float(coll["Saved Amount"].sum())
                if "Saved Amount" in coll else 0.0
            )
            saved_weight = (
                float(transactions["Saved Metal Weight"].sum())
                if "Saved Metal Weight" in transactions else 0.0
            )
            reward_weight = (
                float(transactions["Rewards Metal Weight"].sum())
                if "Rewards Metal Weight" in transactions else 0.0
            )
            previous_rate = rate - rate_delta

            rows.append({
                "Date": day,
                "Window Start": start,
                "Window End": end,
                "Window Hours": hours,
                "Active Rate": float(rate),
                "Rate Change ₹": float(rate_delta),
                "Rate Change %": (
                    rate_delta / previous_rate * 100.0
                    if previous_rate > 0 else 0.0
                ),
                "Daily Rate Change ₹": float(
                    daily_move_by_date.get(day, 0.0)
                ),
                "Intraday Changes": intraday_changes,
                "Intraday Range ₹": intraday_range,
                "Enrolment": int(len(enrol)),
                "Enrolment Amount": enrol_amount,
                "Collection Count": int(len(coll)),
                "Collection": collection,
                "Saved Weight": saved_weight,
                "Reward Weight": reward_weight,
                "Total Weight": saved_weight + reward_weight,
            })

    return pd.DataFrame(rows, columns=RATE_WINDOW_COLS).reset_index(drop=True)


def build_rate_window_features(rate_windows):
    if rate_windows is None or rate_windows.empty:
        return pd.DataFrame()

    features = rate_windows.copy()
    features["Date"] = pd.to_datetime(features["Date"]).dt.normalize()
    features["Metal Rate"] = features["Active Rate"].astype(float)
    features["Rate Δ₹"] = features["Rate Change ₹"].astype(float)
    features["Rate Δ%"] = features["Rate Change %"].astype(float)

    exposure_scale = (
        24.0 / pd.to_numeric(features["Window Hours"], errors="coerce")
    ).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    for metric in CUST_METRICS:
        if metric in features.columns:
            features[metric] = (
                pd.to_numeric(features[metric], errors="coerce")
                .fillna(0.0) * exposure_scale
            )

    return features.sort_values(
        ["Date", "Window Start"], kind="stable"
    ).reset_index(drop=True)


def build_pattern_features(daily_rate, daily_cust):
    if daily_rate.empty:
        return pd.DataFrame()

    df = daily_rate[["Date", "Metal Rate"]].copy()

    for c in ["Intraday Changes", "Intraday Range ₹",
              "Day Close Rate", "Day Close At"]:
        if c in daily_rate.columns:
            df[c] = daily_rate[c].values
        else:
            df[c] = 0.0 if "₹" in c or "Changes" in c else pd.NaT

    if not daily_cust.empty:
        df = df.merge(daily_cust, on="Date", how="left")
    else:
        for c in CUST_METRICS:
            df[c] = 0.0

    for c in CUST_METRICS:
        if c not in df.columns:
            df[c] = 0.0
        df[c] = df[c].fillna(0.0)

    df["Intraday Changes"] = df["Intraday Changes"].fillna(0)
    df["Intraday Range ₹"] = df["Intraday Range ₹"].fillna(0.0)

    df = df.sort_values("Date").reset_index(drop=True)

    df["Rate Δ₹"] = df["Metal Rate"].diff()
    df["Rate Δ%"] = df["Metal Rate"].pct_change() * 100.0

    for c in ["Enrolment", "Enrolment Amount", "Collection Count",
              "Collection", "Total Weight"]:
        df[f"{c} Δ"] = df[c].diff()

    for c in ["Metal Rate", "Enrolment", "Collection", "Total Weight"]:
        df[f"{c} MA7"] = df[c].rolling(7, min_periods=1).mean()

    return df


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def _magnitude_bucket(move_rs):
    if pd.isna(move_rs):
        return None
    m = abs(float(move_rs))
    for lo, hi, label in RATE_MAGNITUDE_BUCKETS:
        if lo <= m <= hi:
            return label
    return None


def _cumulative_bucket(move_rs):
    if pd.isna(move_rs):
        return "₹0–50"
    m = abs(float(move_rs))
    for lo, hi, label in CUMULATIVE_MOVE_BUCKETS:
        if lo <= m <= hi:
            return label
    return "₹601+"


def _intraday_bucket(n):
    n = int(n or 0)
    if n == 0:
        return "0"
    if n == 1:
        return "1"
    if n == 2:
        return "2"
    return "3+"


def _recency_weighted_mean(values, half_life=BEHAVIOR_RECENCY_HALFLIFE):
    vals = np.asarray(values, dtype=float)
    if vals.size == 0:
        return 0.0
    ages = np.arange(vals.size - 1, -1, -1)
    weights = 0.5 ** (ages / float(half_life))
    w_sum = weights.sum()
    if w_sum <= 0:
        return float(np.mean(vals))
    return float(np.sum(vals * weights) / w_sum)


def _recent_baseline_weighted(daily_cust, days=BEHAVIOR_BASELINE_DAYS):
    if daily_cust is None or daily_cust.empty:
        return {m: 0.0 for m in REACTION_METRICS}
    tail = daily_cust.tail(int(days))
    out = {}
    for m in REACTION_METRICS:
        if m in tail.columns:
            out[m] = _recency_weighted_mean(tail[m].values)
        else:
            out[m] = 0.0
    return out


# ─────────────────────────────────────────────────────────────
# LAYER ①: CUSTOMER REACTION ANALYSIS
# ─────────────────────────────────────────────────────────────
def build_customer_reaction_analysis(
    daily_rate,
    daily_cust,
    recent_days=CUSTOMER_REACTION_DAYS,
):
    if daily_rate is None or daily_rate.empty:
        return {"status": "NO_DATA", "recent_days": recent_days}
    if daily_cust is None or daily_cust.empty:
        return {"status": "NO_DATA", "recent_days": recent_days}

    rate = daily_rate[
        ["Date", "Metal Rate", "Intraday Changes", "Intraday Range ₹"]
    ].copy()
    cust = daily_cust.copy()

    rate["Date"] = pd.to_datetime(rate["Date"]).dt.normalize()
    cust["Date"] = pd.to_datetime(cust["Date"]).dt.normalize()

    df = rate.merge(cust, on="Date", how="left")

    for c in REACTION_METRICS:
        if c not in df.columns:
            df[c] = 0.0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    df = df.sort_values("Date").reset_index(drop=True)

    df["Rate Change ₹"] = df["Metal Rate"].diff()
    df["Rate Change %"] = df["Metal Rate"].pct_change() * 100.0

    df["Rate Direction"] = np.select(
        [
            df["Rate Change ₹"] > FLAT_TOLERANCE,
            df["Rate Change ₹"] < -FLAT_TOLERANCE,
        ],
        ["Increase", "Decrease"],
        default="Flat",
    )

    df["Magnitude"] = df["Rate Change ₹"].apply(_magnitude_bucket)

    for c in REACTION_METRICS:
        df[f"Prev {c}"] = df[c].shift(1)
        df[f"Next {c}"] = df[c].shift(-1)

    cutoff = df["Date"].max() - pd.Timedelta(days=int(recent_days) - 1)
    recent = df[df["Date"] >= cutoff].copy()

    if recent.empty:
        return {"status": "NO_RECENT_DATA", "recent_days": recent_days}

    summary_rows = []
    for direction in ["Increase", "Decrease", "Flat"]:
        g = recent[recent["Rate Direction"] == direction]
        if g.empty:
            continue
        row = {
            "Rate Direction": direction,
            "Days": int(len(g)),
            "Avg Rate Change ₹": float(g["Rate Change ₹"].mean()),
            "Avg Rate Change %": float(g["Rate Change %"].mean()),
        }
        for m in REACTION_METRICS:
            row[f"{m} Same Day"] = float(g[m].mean())
            nxt = g[f"Next {m}"].dropna()
            row[f"{m} Next Day"] = (
                float(nxt.mean()) if not nxt.empty else np.nan
            )
        summary_rows.append(row)

    summary = pd.DataFrame(summary_rows)

    flat = recent[recent["Rate Direction"] == "Flat"]
    baseline = {}
    for m in REACTION_METRICS:
        baseline[m] = float(flat[m].mean()) if not flat.empty else np.nan

    comparison_rows = []
    for direction in ["Increase", "Decrease"]:
        g = recent[recent["Rate Direction"] == direction]
        if g.empty:
            continue
        row = {
            "Rate Direction": direction,
            "Days": int(len(g)),
            "Avg Rate Change ₹": float(g["Rate Change ₹"].mean()),
        }
        for m in REACTION_METRICS:
            same = float(g[m].mean())
            base = baseline.get(m, np.nan)
            row[f"{m} Same Day"] = same
            row[f"{m} Same Day vs Flat %"] = (
                ((same - base) / base) * 100.0
                if pd.notna(base) and abs(base) > 1e-9 else np.nan
            )
            nxt = g[f"Next {m}"].dropna()
            if not nxt.empty:
                next_avg = float(nxt.mean())
                row[f"{m} Next Day"] = next_avg
                row[f"{m} Next Day vs Flat %"] = (
                    ((next_avg - base) / base) * 100.0
                    if pd.notna(base) and abs(base) > 1e-9 else np.nan
                )
            else:
                row[f"{m} Next Day"] = np.nan
                row[f"{m} Next Day vs Flat %"] = np.nan
        comparison_rows.append(row)

    comparison = pd.DataFrame(comparison_rows)

    magnitude_rows = []
    for direction in ["Increase", "Decrease"]:
        for lo, hi, label in RATE_MAGNITUDE_BUCKETS:
            g = recent[
                (recent["Rate Direction"] == direction)
                & (recent["Magnitude"] == label)
            ]
            if len(g) < REACTION_MIN_GROUP_DAYS:
                continue
            row = {
                "Rate Direction": direction,
                "Magnitude": label,
                "Days": int(len(g)),
                "Avg Rate Change ₹": float(g["Rate Change ₹"].mean()),
            }
            for m in ["Enrolment", "Collection", "Total Weight"]:
                same = float(g[m].mean())
                base = baseline.get(m, np.nan)
                row[f"{m}"] = same
                row[f"{m} vs Flat %"] = (
                    ((same - base) / base) * 100.0
                    if pd.notna(base) and abs(base) > 1e-9 else np.nan
                )
            magnitude_rows.append(row)

    magnitude = pd.DataFrame(magnitude_rows)

    elasticity = {}
    valid = recent.dropna(subset=["Rate Change %"])
    if len(valid) >= 3 and valid["Rate Change %"].std() > 1e-9:
        for m in ["Enrolment", "Collection", "Total Weight"]:
            s = valid[m].astype(float)
            if s.std() < 1e-9:
                elasticity[m] = 0.0
                continue
            pct_metric = s.pct_change().replace([np.inf, -np.inf], np.nan)
            pair = pd.DataFrame({
                "m": pct_metric.values,
                "r": valid["Rate Change %"].values,
            }).dropna()
            if len(pair) >= 3 and pair["r"].abs().mean() > 1e-6:
                slope = np.polyfit(pair["r"], pair["m"], 1)[0]
                elasticity[m] = float(slope) * 100.0
            else:
                elasticity[m] = 0.0
    else:
        elasticity = {m: 0.0 for m in
                      ["Enrolment", "Collection", "Total Weight"]}

    intraday_rows = []
    for label, cond in [
        ("0 changes", recent["Intraday Changes"] == 0),
        ("1 change", recent["Intraday Changes"] == 1),
        ("2 changes", recent["Intraday Changes"] == 2),
        ("3+ changes", recent["Intraday Changes"] >= 3),
    ]:
        g = recent[cond]
        if len(g) < REACTION_MIN_GROUP_DAYS:
            continue
        intraday_rows.append({
            "Intraday Pattern": label,
            "Days": int(len(g)),
            "Avg Enrolment": float(g["Enrolment"].mean()),
            "Avg Collection ₹": float(g["Collection"].mean()),
            "Avg Total Weight g": float(g["Total Weight"].mean()),
        })
    intraday = pd.DataFrame(intraday_rows)

    detail_cols = [
        "Date", "Metal Rate", "Rate Change ₹", "Rate Change %",
        "Rate Direction", "Magnitude",
        "Intraday Changes", "Intraday Range ₹",
    ] + REACTION_METRICS
    detail = recent[detail_cols].copy()

    insights = []
    if not comparison.empty:
        for _, r in comparison.iterrows():
            direction = r["Rate Direction"]
            enr = r.get("Enrolment Same Day vs Flat %", np.nan)
            col = r.get("Collection Same Day vs Flat %", np.nan)
            wt = r.get("Total Weight Same Day vs Flat %", np.nan)
            enr_next = r.get("Enrolment Next Day vs Flat %", np.nan)

            word = "increased" if direction == "Increase" else "decreased"
            effects = []
            if pd.notna(enr):
                effects.append(f"enrolments **{enr:+.1f}%**")
            if pd.notna(col):
                effects.append(f"collection **{col:+.1f}%**")
            if pd.notna(wt):
                effects.append(f"total weight **{wt:+.1f}%**")
            if effects:
                insights.append(
                    f"When rates **{word}**, same-day " +
                    ", ".join(effects) +
                    f" vs flat-rate days ({int(r['Days'])} day(s))."
                )
            if pd.notna(enr_next) and abs(enr_next) >= 3:
                lag = "higher" if enr_next > 0 else "lower"
                insights.append(
                    f"👉 The following day, enrolments were "
                    f"**{abs(enr_next):.1f}% {lag}** than flat-rate days "
                    f"— a possible delayed reaction."
                )

    if not magnitude.empty:
        for _, r in magnitude.iterrows():
            enr = r.get("Enrolment vs Flat %", np.nan)
            if pd.notna(enr) and abs(enr) >= 5:
                insights.append(
                    f"⚠️ **{r['Rate Direction']} {r['Magnitude']}** moves "
                    f"are associated with **{enr:+.1f}%** enrolment vs flat "
                    f"({int(r['Days'])} day(s))."
                )

    if not intraday.empty and len(intraday) >= 2:
        calm = intraday[intraday["Intraday Pattern"] == "0 changes"]
        choppy = intraday[intraday["Intraday Pattern"].str.startswith("3")]
        if not calm.empty and not choppy.empty:
            calm_enr = float(calm["Avg Enrolment"].iloc[0])
            choppy_enr = float(choppy["Avg Enrolment"].iloc[0])
            if calm_enr > 0:
                diff = (choppy_enr - calm_enr) / calm_enr * 100.0
                insights.append(
                    f"🔀 Days with **3+ intraday rate changes** show "
                    f"**{diff:+.1f}%** enrolment vs calm days — choppy "
                    f"pricing appears to affect engagement."
                )

    if not insights:
        insights.append(
            "No strong rate-driven behavioural pattern detected in the "
            "recent window. Customer activity looks broadly stable."
        )

    return {
        "status": "OK",
        "recent_days": int(recent_days),
        "summary": summary,
        "comparison": comparison,
        "magnitude": magnitude,
        "intraday": intraday,
        "elasticity": elasticity,
        "baseline": baseline,
        "detail": detail,
        "insights": insights,
    }


def _customer_reaction_interpretation(analysis, metal):
    if analysis.get("status") != "OK":
        return f"Not enough recent customer-reaction data for {metal}."

    comp = analysis.get("comparison")
    if comp is None or comp.empty:
        return (
            f"The recent {analysis['recent_days']}-day window has no "
            f"usable rate-change days for a behavioural comparison."
        )

    parts = []
    for direction in ["Increase", "Decrease"]:
        rows = comp[comp["Rate Direction"] == direction]
        if rows.empty:
            continue
        r = rows.iloc[0]
        word = "increased" if direction == "Increase" else "decreased"
        effects = []
        for label, col in [
            ("enrolments", "Enrolment Same Day vs Flat %"),
            ("collection", "Collection Same Day vs Flat %"),
            ("total weight", "Total Weight Same Day vs Flat %"),
        ]:
            v = r.get(col, np.nan)
            if pd.notna(v):
                effects.append(f"{label} {v:+.1f}%")
        if effects:
            parts.append(
                f"When rates <b>{word}</b>: " + ", ".join(effects) +
                " vs flat-rate days."
            )

    if not parts:
        return f"Recent {analysis['recent_days']}-day data has no usable pattern."

    return "<br>".join(parts)


# ─────────────────────────────────────────────────────────────
# BEHAVIOUR MODEL (Context-Aware, Primary Engine)
# ─────────────────────────────────────────────────────────────
def build_behavior_model(features, recent_days=BEHAVIOR_MODEL_DAYS,
                         baseline_days=BEHAVIOR_BASELINE_DAYS,
                         baseline=None):
    if features is None or features.empty:
        return {"status": "NO_DATA"}

    df = features.copy().reset_index(drop=True)
    df["Date"] = pd.to_datetime(df["Date"])
    sort_cols = ["Date"]
    if "Window Start" in df.columns:
        sort_cols.append("Window Start")
    df = df.sort_values(sort_cols, kind="stable").reset_index(drop=True)

    baseline = (baseline if baseline is not None
                else _recent_baseline_weighted(df, baseline_days))

    active_rates = pd.to_numeric(
        df.get("Active Rate", df.get("Metal Rate", 0.0)), errors="coerce"
    ).fillna(0.0)
    df["Rate Level Bucket"] = np.floor(
        active_rates / ACTIVE_RATE_BUCKET_RS
    ).astype(int)

    daily_moves = (
        df.groupby("Date")["Daily Rate Change ₹"].first().sort_index()
        if "Daily Rate Change ₹" in df.columns
        else df.groupby("Date")["Rate Δ₹"].first().sort_index()
    )
    prior_day_moves = daily_moves.shift(1).fillna(0.0)
    cumulative_day_moves = daily_moves.rolling(
        BEHAVIOR_CONTEXT_LOOKBACK, min_periods=1
    ).sum()

    cutoff = df["Date"].max() - pd.Timedelta(days=int(recent_days) - 1)
    win = df[df["Date"] >= cutoff].copy()

    if win.empty:
        return {"status": "NO_RECENT_DATA", "baseline": baseline}

    if "Rate Δ₹" not in win.columns:
        win["Rate Δ₹"] = win["Metal Rate"].diff()
    if "Rate Δ%" not in win.columns:
        win["Rate Δ%"] = win["Metal Rate"].pct_change() * 100.0

    win["Direction"] = np.select(
        [
            win["Rate Δ₹"] > FLAT_TOLERANCE,
            win["Rate Δ₹"] < -FLAT_TOLERANCE,
        ],
        ["Increase", "Decrease"],
        default="Flat",
    )
    win["Magnitude"] = win["Rate Δ₹"].apply(_magnitude_bucket)
    win["Magnitude"] = win["Magnitude"].fillna("Flat")
    win["Intraday Bucket"] = win["Intraday Changes"].apply(_intraday_bucket)

    win["Prior Day Move ₹"] = win["Date"].map(prior_day_moves).fillna(0.0)
    win["Prior Direction"] = np.select(
        [win["Prior Day Move ₹"] > FLAT_TOLERANCE,
         win["Prior Day Move ₹"] < -FLAT_TOLERANCE],
        ["Increase", "Decrease"], default="Flat",
    )
    win["Prior Magnitude"] = win["Prior Day Move ₹"].apply(
        lambda value: _magnitude_bucket(value) or "Flat"
    )

    win["Cumulative Move ₹"] = win["Date"].map(
        cumulative_day_moves
    ).fillna(0.0)
    win["Cumulative Direction"] = np.select(
        [
            win["Cumulative Move ₹"] > FLAT_TOLERANCE,
            win["Cumulative Move ₹"] < -FLAT_TOLERANCE,
        ],
        ["Increase", "Decrease"],
        default="Flat",
    )
    win["Cumulative Bucket"] = win["Cumulative Move ₹"].apply(
        _cumulative_bucket
    )

    def _multipliers(sub):
        out = {}
        for m in REACTION_METRICS:
            base = baseline.get(m, 0.0)
            if base > 1e-9:
                if "Window Hours" in sub.columns:
                    hours = pd.to_numeric(
                        sub["Window Hours"], errors="coerce"
                    ).clip(lower=0.0)
                    valid = hours > 0
                    daily_values = (
                        (sub.loc[valid, m] * hours[valid])
                        .groupby(sub.loc[valid, "Date"]).sum()
                        / hours[valid].groupby(
                            sub.loc[valid, "Date"]
                        ).sum()
                    )
                    out[m] = float(daily_values.mean()) / base
                else:
                    out[m] = float(sub[m].mean()) / base
            else:
                out[m] = 1.0
        return out

    model = {
        "baseline": baseline,
        "rate_bucket_size": ACTIVE_RATE_BUCKET_RS,
        "exact": {},
        "context": {},
        "rate_coarse": {},
        "coarse": {},
        "trend": {},
        "broad": {},
        "global": {},
        "counts": {},
    }

    for _, row in win.iterrows():
        direction = row["Direction"]
        mag = row["Magnitude"]
        ib = row["Intraday Bucket"]
        pd_ = row["Prior Direction"]
        pm = row["Prior Magnitude"]
        cd = row["Cumulative Direction"]
        rate_bucket = int(row["Rate Level Bucket"])

        model["exact"].setdefault(
            (direction, mag, ib, pd_, pm, cd, rate_bucket), []
        ).append(row)
        model["context"].setdefault(
            (direction, mag, pd_, cd, rate_bucket), []
        ).append(row)
        model["rate_coarse"].setdefault(
            (direction, mag, rate_bucket), []
        ).append(row)
        model["coarse"].setdefault((direction, mag), []).append(row)
        model["trend"].setdefault((direction, pd_), []).append(row)
        model["broad"].setdefault((direction,), []).append(row)
        model["global"].setdefault(("all",), []).append(row)

    for key, rows in model["exact"].items():
        sub = pd.DataFrame(rows)
        model["exact"][key] = _multipliers(sub)
        model["counts"][("exact",) + key] = int(sub["Date"].nunique())

    for key, rows in model["context"].items():
        sub = pd.DataFrame(rows)
        model["context"][key] = _multipliers(sub)
        model["counts"][("context",) + key] = int(sub["Date"].nunique())

    for key, rows in model["rate_coarse"].items():
        sub = pd.DataFrame(rows)
        model["rate_coarse"][key] = _multipliers(sub)
        model["counts"][("rate_coarse",) + key] = int(
            sub["Date"].nunique()
        )

    for key, rows in model["coarse"].items():
        sub = pd.DataFrame(rows)
        model["coarse"][key] = _multipliers(sub)
        model["counts"][("coarse",) + key] = int(sub["Date"].nunique())

    for key, rows in model["trend"].items():
        sub = pd.DataFrame(rows)
        model["trend"][key] = _multipliers(sub)
        model["counts"][("trend",) + key] = int(sub["Date"].nunique())

    for key, rows in model["broad"].items():
        sub = pd.DataFrame(rows)
        model["broad"][key] = _multipliers(sub)
        model["counts"][("broad",) + key] = int(sub["Date"].nunique())

    for key, rows in model["global"].items():
        sub = pd.DataFrame(rows)
        model["global"][key] = _multipliers(sub)
        model["counts"][("global",) + key] = int(sub["Date"].nunique())

    model["status"] = "OK"
    model["recent_days"] = int(recent_days)
    model["baseline_days"] = int(baseline_days)

    distributions = {}
    group_cols = ["Direction", "Magnitude", "Rate Level Bucket"]
    for (direction, mag, rate_bucket), m_grp in win.groupby(
            group_cols, sort=False, observed=True):
        dist = {}
        for metric in ["Enrolment", "Collection", "Total Weight"]:
            vals = m_grp[metric].dropna().values
            if m_grp["Date"].nunique() >= BEHAVIOR_MIN_BUCKET_DAYS:
                dist[metric] = {
                    "p10": float(np.percentile(vals, 10)),
                    "p50": float(np.percentile(vals, 50)),
                    "p90": float(np.percentile(vals, 90)),
                    "n": int(m_grp["Date"].nunique()),
                }
        if dist:
            distributions[(direction, mag, int(rate_bucket))] = dist
    model["distributions"] = distributions

    if len(df) >= 2:
        last_row = df.iloc[-1]
        model["last_day_actuals"] = {
            m: float(last_row.get(m, 0.0)) for m in REACTION_METRICS
        }
        model["last_day_move"] = float(last_row.get("Rate Δ₹", 0.0) or 0.0)
        model["last_day_intraday"] = int(
            last_row.get("Intraday Changes", 0) or 0
        )
    else:
        model["last_day_actuals"] = {}
        model["last_day_move"] = 0.0
        model["last_day_intraday"] = 0

    return model


def _select_behavior_multipliers(model, direction, magnitude,
                                 intraday_changes,
                                 prior_direction="None",
                                 prior_magnitude="Flat",
                                 cumulative_direction="Flat",
                                 active_rate=None):
    if model.get("status") != "OK":
        return None, "unavailable", 0

    ib = _intraday_bucket(int(intraday_changes))
    rate_bucket_size = float(
        model.get("rate_bucket_size", ACTIVE_RATE_BUCKET_RS)
    )
    rate_bucket = int(np.floor(float(active_rate or 0.0) / rate_bucket_size))

    exact_key = (direction, magnitude, ib,
                 prior_direction, prior_magnitude, cumulative_direction,
                 rate_bucket)
    if (exact_key in model["exact"]
            and model["counts"].get(
                ("exact",) + exact_key, 0
            ) >= BEHAVIOR_MIN_BUCKET_DAYS):
        return (
            model["exact"][exact_key],
            "exact",
            model["counts"][("exact",) + exact_key],
        )

    ctx_key = (direction, magnitude, prior_direction, cumulative_direction,
               rate_bucket)
    if (ctx_key in model["context"]
            and model["counts"].get(
                ("context",) + ctx_key, 0
            ) >= BEHAVIOR_MIN_BUCKET_DAYS):
        return (
            model["context"][ctx_key],
            "context",
            model["counts"][("context",) + ctx_key],
        )

    coarse_key = (direction, magnitude)
    rate_key = (direction, magnitude, rate_bucket)
    if (rate_key in model["rate_coarse"]
            and model["counts"].get(("rate_coarse",) + rate_key, 0)
            >= BEHAVIOR_MIN_BUCKET_DAYS):
        return (
            model["rate_coarse"][rate_key],
            "rate-level",
            model["counts"][("rate_coarse",) + rate_key],
        )

    if (coarse_key in model["coarse"]
            and model["counts"].get(
                ("coarse",) + coarse_key, 0
            ) >= BEHAVIOR_MIN_BUCKET_DAYS):
        return (
            model["coarse"][coarse_key],
            "coarse",
            model["counts"][("coarse",) + coarse_key],
        )

    trend_key = (direction, prior_direction)
    if (trend_key in model["trend"]
            and model["counts"].get(
                ("trend",) + trend_key, 0
            ) >= BEHAVIOR_MIN_BUCKET_DAYS):
        return (
            model["trend"][trend_key],
            "trend",
            model["counts"][("trend",) + trend_key],
        )

    broad_key = (direction,)
    if (broad_key in model["broad"]
            and model["counts"].get(
                ("broad",) + broad_key, 0
            ) >= BEHAVIOR_MIN_BUCKET_DAYS):
        return (
            model["broad"][broad_key],
            "broad",
            model["counts"][("broad",) + broad_key],
        )

    if ("all",) in model["global"]:
        return (
            model["global"][("all",)],
            "global",
            model["counts"].get(("global", "all"), 0),
        )

    return None, "unavailable", 0


def _select_behavior_distribution(model, direction, magnitude,
                                  active_rate=None):
    if model.get("status") != "OK":
        return None
    d = model.get("distributions", {})
    rate_bucket_size = float(
        model.get("rate_bucket_size", ACTIVE_RATE_BUCKET_RS)
    )
    rate_bucket = int(np.floor(float(active_rate or 0.0) / rate_bucket_size))
    return d.get((direction, magnitude, rate_bucket),
                 d.get((direction, magnitude)))


def project_from_behavior(baseline, multipliers):
    proj = {}
    for m in REACTION_METRICS:
        base = float(baseline.get(m, 0.0))
        mult = float(multipliers.get(m, 1.0))
        proj[m] = base * mult
    proj["Enrolment"] = int(round(proj.get("Enrolment", 0.0)))
    proj["Collection Count"] = int(round(proj.get("Collection Count", 0.0)))
    return proj


def _coherence_parameters(baseline):
    baseline_enrolment = float(baseline.get("Enrolment", 0.0))
    baseline_enrolment_amount = float(baseline.get("Enrolment Amount", 0.0))
    baseline_saved_weight = float(baseline.get("Saved Weight", 0.0))
    baseline_reward_weight = float(baseline.get("Reward Weight", 0.0))

    average_ticket = (
        baseline_enrolment_amount / baseline_enrolment
        if baseline_enrolment > 1e-9 else 0.0
    )
    reward_ratio = (
        baseline_reward_weight / baseline_saved_weight
        if baseline_saved_weight > 1e-9 else 0.0
    )
    return average_ticket, reward_ratio


def enforce_coherence(proj, baseline, rate):
    if rate is None or float(rate) <= 1e-9:
        return dict(proj)

    proj = dict(proj)
    rate = float(rate)
    average_ticket, reward_ratio = _coherence_parameters(baseline)
    enrolment = float(proj.get("Enrolment", 0.0))
    enrolment_amount = enrolment * average_ticket
    collection = float(proj.get("Collection", 0.0))
    saved_weight = (enrolment_amount + collection) / rate
    reward_weight = saved_weight * reward_ratio

    proj["Enrolment"] = int(round(enrolment))
    proj["Collection Count"] = int(round(
        proj.get("Collection Count", 0.0)
    ))
    proj["Enrolment Amount"] = enrolment_amount
    proj["Saved Weight"] = saved_weight
    proj["Reward Weight"] = reward_weight
    proj["Total Weight"] = saved_weight + reward_weight
    return proj


def enforce_coherence_on_range(rng, proj, rate, baseline):
    if not rng or rate is None or float(rate) <= 1e-9:
        return rng

    rng = dict(rng)
    rate = float(rate)
    average_ticket, reward_ratio = _coherence_parameters(baseline)

    def _with_point(low, point, high):
        point = float(point)
        return (min(float(low), point), point, max(float(high), point))

    enrolment_range = rng.get(
        "Enrolment", (proj["Enrolment"],) * 3
    )
    collection_range = rng.get(
        "Collection", (proj["Collection"],) * 3
    )
    enrolment_amount_range = _with_point(
        enrolment_range[0] * average_ticket,
        proj["Enrolment Amount"],
        enrolment_range[2] * average_ticket,
    )
    collection_range = _with_point(
        collection_range[0], proj["Collection"], collection_range[2]
    )

    saved_range = _with_point(
        (enrolment_amount_range[0] + collection_range[0]) / rate,
        proj["Saved Weight"],
        (enrolment_amount_range[2] + collection_range[2]) / rate,
    )
    reward_range = _with_point(
        saved_range[0] * reward_ratio,
        proj["Reward Weight"],
        saved_range[2] * reward_ratio,
    )
    total_range = _with_point(
        saved_range[0] + reward_range[0],
        proj["Total Weight"],
        saved_range[2] + reward_range[2],
    )

    rng["Enrolment Amount"] = enrolment_amount_range
    rng["Collection"] = collection_range
    rng["Saved Weight"] = saved_range
    rng["Reward Weight"] = reward_range
    rng["Total Weight"] = total_range
    return rng


def _behavior_reliability(n_days, source):
    if source == "exact" and n_days >= BEHAVIOR_CONFIDENCE_HIGH:
        return "HIGH"
    if source in ("exact", "coarse", "context", "rate-level") and n_days >= BEHAVIOR_CONFIDENCE_MED:
        return "MEDIUM"
    if source in ("coarse", "broad", "context", "trend", "rate-level") and n_days >= BEHAVIOR_MIN_BUCKET_DAYS:
        return "LOW"
    return "ROUGH"


# ─────────────────────────────────────────────────────────────
# SUPPORTING EVIDENCE (secondary)
# ─────────────────────────────────────────────────────────────
def find_supporting_matches(features, move_rs, direction,
                            tolerance_rs=DEFAULT_MATCH_TOLERANCE_RS,
                            top_n=10):
    if features is None or features.empty:
        return pd.DataFrame()

    df = features.reset_index(drop=True).copy()
    move_column = (
        "Rate Δ₹" if "Rate Δ₹" in df.columns else "Rate Change ₹"
    )
    rows = []
    for i in range(1, len(df)):
        m = df.iloc[i].get(move_column, np.nan)
        if pd.isna(m):
            continue
        if direction == "Increase" and m <= FLAT_TOLERANCE:
            continue
        if direction == "Decrease" and m >= -FLAT_TOLERANCE:
            continue
        if direction == "Flat" and abs(m) > FLAT_TOLERANCE:
            continue
        if abs(m - move_rs) > tolerance_rs:
            continue
        record = {
            "Date": pd.Timestamp(df.iloc[i]["Date"]).strftime("%d-%m-%Y"),
            "Match Move ₹": round(float(m), 2),
            "Move Diff ₹": round(float(m) - move_rs, 2),
            "Intraday Changes": int(df.iloc[i].get("Intraday Changes", 0) or 0),
            "Enrolment": round(float(df.iloc[i].get("Enrolment", 0.0)), 1),
            "Collection ₹": round(float(df.iloc[i].get("Collection", 0.0)), 0),
            "Total Weight g": round(
                float(df.iloc[i].get("Total Weight", 0.0)), 3),
        }
        if "Active Rate" in df.columns:
            record["Active Rate ₹"] = float(df.iloc[i]["Active Rate"])
        if "Window Start" in df.columns:
            start = pd.Timestamp(df.iloc[i]["Window Start"])
            end = pd.Timestamp(df.iloc[i]["Window End"])
            record["Window Start"] = start.strftime(
                "%H:%M:%S" if start.second else "%H:%M"
            )
            record["Window End"] = end.strftime(
                "%H:%M:%S" if end.second else "%H:%M"
            )
        rows.append(record)

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows).sort_values(
        "Move Diff ₹", key=lambda s: s.abs()
    ).reset_index(drop=True)
    return out.head(int(top_n))


# ─────────────────────────────────────────────────────────────
# PRIMARY PROJECTION ENTRYPOINT
# ─────────────────────────────────────────────────────────────
def run_behavior_projection(features, recent_baseline, prev_rate, curr_rate,
                            projection_date, metal="",
                            today_changes=0, today_range=None,
                            today_path=None, today_morning=None,
                            prev_day_changes=0, prev_day_range=0.0,
                            prev_date=None,
                            model=None,
                            model_days=BEHAVIOR_MODEL_DAYS,
                            prior_day_move=0.0,
                            prior_day_direction="None",
                            prior_day_magnitude="Flat",
                            cumulative_move=0.0,
                            cumulative_direction="Flat",
                            calendar_prev_rate=None,
                            rate_at_midnight=None,
                            rate_timeline=None,
                            previous_day_rate_timeline=None,
                            behavior_features=None,
                            supporting_windows=None,
                            spike_decay=BEHAVIOR_SPIKE_DECAY,
                            trend_boost=BEHAVIOR_TREND_BOOST):
    projection_date = pd.Timestamp(projection_date).normalize()
    move_rs = round(float(curr_rate) - float(prev_rate), 4)
    move_pct = (round(move_rs / prev_rate * 100.0, 4)
                if prev_rate > 0 else 0.0)
    direction = ("Increase" if move_rs > FLAT_TOLERANCE
                 else "Decrease" if move_rs < -FLAT_TOLERANCE
                 else "Flat")
    magnitude = _magnitude_bucket(move_rs) or "Flat"

    base_meta = {
        "metal": metal,
        "projection_date": projection_date,
        "prev_rate": float(prev_rate),
        "previous_calendar_day_rate": float(
            prev_rate if calendar_prev_rate is None else calendar_prev_rate
        ),
        "rate_at_midnight": float(
            curr_rate if rate_at_midnight is None else rate_at_midnight
        ),
        "Rate Timeline": list(rate_timeline or []),
        "Previous Day Rate Timeline": list(previous_day_rate_timeline or []),
        "prev_date": prev_date,
        "manual_curr_rate": float(curr_rate),
        "today_move_rs": move_rs,
        "today_move_pct": move_pct,
        "direction": direction,
        "magnitude": magnitude,
        "Prior Day Direction": prior_day_direction,
        "Prior Day Magnitude": prior_day_magnitude,
        "Prior Day Move ₹": float(prior_day_move),
        "Cumulative Direction": cumulative_direction,
        "Cumulative Move ₹": float(cumulative_move),
        "Today Intraday Changes": int(today_changes),
        "Today Intraday Range ₹": float(today_range or abs(move_rs)),
        "Today Intraday Path": list(today_path or [float(curr_rate)]),
        "Rate at 12:00 AM": float(today_morning or curr_rate),
        "Prev Day Intraday Changes": int(prev_day_changes),
        "Prev Day Intraday Range ₹": float(prev_day_range),
        "Is_Flat_Reference": direction == "Flat",
        "method": "BEHAVIOR_DRIVEN_CONTEXT_AWARE",
        "Model Days": int(model_days),
        "Match Tolerance ₹": float(DEFAULT_MATCH_TOLERANCE_RS),
        "Horizon_Days": int(OUTCOME_OFFSET),
        "Spike Decay Used": float(spike_decay),
        "Trend Boost Used": float(trend_boost),
    }

    if model is None or model.get("status") != "OK":
        return {**base_meta, "status": "NO_BEHAVIOR_MODEL"}

    multipliers, source, n_days = _select_behavior_multipliers(
        model, direction, magnitude, today_changes,
        prior_direction=prior_day_direction,
        prior_magnitude=prior_day_magnitude,
        cumulative_direction=cumulative_direction,
        active_rate=curr_rate,
    )
    if multipliers is None:
        return {**base_meta, "status": "NO_USABLE_BUCKET"}

    momentum_note = None
    last_actuals = model.get("last_day_actuals", {})
    if last_actuals and recent_baseline:
        boost = {}
        for m in ["Enrolment", "Collection", "Total Weight"]:
            base = recent_baseline.get(m, 0.0)
            yest = float(last_actuals.get(m, 0.0))
            if base > 1e-9:
                ratio = yest / base
                if ratio >= BEHAVIOR_SPIKE_THRESHOLD:
                    carry = 1.0 + (ratio - 1.0) * float(spike_decay)
                    boost[m] = carry
                else:
                    boost[m] = 1.0
            else:
                boost[m] = 1.0

        if any(v != 1.0 for v in boost.values()):
            for m, b in boost.items():
                if m in multipliers:
                    multipliers[m] = multipliers[m] * b
            momentum_note = {
                "Reason": "Yesterday's activity was a spike vs baseline",
                "Yesterday vs Baseline":
                    {m: round(last_actuals.get(m, 0.0)
                              / max(recent_baseline.get(m, 1.0), 1e-9), 2)
                     for m in ["Enrolment", "Collection", "Total Weight"]},
                "Carry Factor": {m: round(v, 3) for m, v in boost.items()},
                "Spike Decay": float(spike_decay),
            }

    if (abs(cumulative_move) > abs(prior_day_move)
            and cumulative_direction == direction
            and abs(cumulative_move) > FLAT_TOLERANCE):
        trend_factor = 1.0 + (float(trend_boost) *
                              min(abs(cumulative_move) / 500.0, 1.0))
        for m in ["Enrolment", "Collection", "Total Weight"]:
            if m in multipliers:
                multipliers[m] = multipliers[m] * trend_factor
        if momentum_note is None:
            momentum_note = {}
        momentum_note["Trend"] = (
            f"Multi-day move in same direction as today "
            f"(₹{cumulative_move:+.2f} over "
            f"{BEHAVIOR_CONTEXT_LOOKBACK} days)"
        )
        momentum_note["Trend Factor"] = round(trend_factor, 3)

    behavior_proj = project_from_behavior(recent_baseline, multipliers)
    proj = enforce_coherence(behavior_proj, recent_baseline, curr_rate)

    dist = _select_behavior_distribution(
        model, direction, magnitude, active_rate=curr_rate
    )

    def _range(metric, point, as_int=False):
        if dist and metric in dist:
            lo = float(dist[metric]["p10"])
            hi = float(dist[metric]["p90"])
            lo = min(lo, float(point))
            hi = max(hi, float(point))
        else:
            lo = float(point) * 0.75
            hi = float(point) * 1.25
        if as_int:
            return (int(round(lo)), int(round(point)), int(round(hi)))
        return (lo, float(point), hi)

    rng = {
        "Enrolment": _range("Enrolment", proj.get("Enrolment", 0), True),
        "Enrolment Amount": _range(
            "Enrolment Amount", proj.get("Enrolment Amount", 0.0)),
        "Collection Count": _range(
            "Collection Count", proj.get("Collection Count", 0), True),
        "Collection": _range("Collection", proj.get("Collection", 0.0)),
        "Saved Weight": _range(
            "Saved Weight", proj.get("Saved Weight", 0.0)),
        "Reward Weight": _range(
            "Reward Weight", proj.get("Reward Weight", 0.0)),
        "Total Weight": _range(
            "Total Weight", proj.get("Total Weight", 0.0)),
    }
    rng = enforce_coherence_on_range(
        rng, proj, curr_rate, recent_baseline
    )

    reliability = _behavior_reliability(n_days, source)

    supporting = find_supporting_matches(
        (supporting_windows if supporting_windows is not None
         else behavior_features if behavior_features is not None
         else features),
        move_rs, direction,
        tolerance_rs=DEFAULT_MATCH_TOLERANCE_RS,
        top_n=10,
    )

    return {
        **base_meta,
        "status": "OK",
        "Projection": proj,
        "Range": rng,
        "Behavior Projection": behavior_proj,
        "Multipliers": multipliers,
        "Baseline": recent_baseline,
        "Bucket Source": source,
        "Bucket Days": int(n_days),
        "Reliability": reliability,
        "Distribution": dist,
        "Supporting Matches": supporting,
        "N_Matches": len(supporting) if supporting is not None else 0,
        "N_Exact": 0,
        "Momentum Adjustment": momentum_note,
    }


def project_step_wise_behavior(features, daily_cust, daily, steps,
                               projection_date, metal,
                               model_days=BEHAVIOR_MODEL_DAYS,
                               baseline_days=BEHAVIOR_BASELINE_DAYS,
                               spike_decay=BEHAVIOR_SPIKE_DECAY,
                               trend_boost=BEHAVIOR_TREND_BOOST,
                               rate_windows=None):
    prev_rate = float(daily["Day Close Rate"].iloc[-1])
    prev_date = daily["Date"].iloc[-1]
    prev_changes = int(daily["Intraday Changes"].iloc[-1])
    prev_range = float(daily["Intraday Range ₹"].iloc[-1])

    if len(daily) >= 2:
        prior_day_move = float(daily["Day Close Rate"].iloc[-1]
                               - daily["Day Close Rate"].iloc[-2])
    else:
        prior_day_move = 0.0

    prior_day_direction = (
        "Increase" if prior_day_move > FLAT_TOLERANCE
        else "Decrease" if prior_day_move < -FLAT_TOLERANCE
        else "Flat"
    )
    prior_day_magnitude = _magnitude_bucket(prior_day_move) or "Flat"

    recent_baseline = _recent_baseline_weighted(
        daily_cust, baseline_days
    )
    behavior_features = build_rate_window_features(rate_windows)
    model = build_behavior_model(
        behavior_features if not behavior_features.empty else features,
        recent_days=model_days,
        baseline_days=baseline_days,
        baseline=recent_baseline,
    )

    previous_day_rate_timeline = []
    if rate_windows is not None and not rate_windows.empty:
        window_dates = pd.to_datetime(rate_windows["Date"]).dt.normalize()
        prior_windows = rate_windows[window_dates == pd.Timestamp(prev_date).normalize()]
        for _, window in prior_windows.iterrows():
            previous_day_rate_timeline.append({
                "time": pd.Timestamp(window["Window Start"]).strftime(
                    "%H:%M:%S" if pd.Timestamp(
                        window["Window Start"]
                    ).second else "%H:%M"
                ),
                "rate": float(window["Active Rate"]),
                "delta": float(window["Rate Change ₹"]),
            })

    results = []
    path = []
    last_step_rate = prev_rate
    midnight_rate = float(steps[0]["rate"]) if steps else prev_rate
    changes_so_far = 0

    for i, step in enumerate(steps):
        curr = float(step["rate"])
        kind = step.get("kind", "start")
        if kind != "start" and abs(curr - last_step_rate) < FLAT_TOLERANCE:
            continue
        if kind in {"up", "down"}:
            changes_so_far += 1
        path.append(curr)

        step_delta = curr - last_step_rate
        step_pct = (step_delta / last_step_rate * 100.0
                    if last_step_rate > 0 else 0.0)
        net_move = curr - midnight_rate

        cumulative_move = prior_day_move + net_move
        cumulative_direction = (
            "Increase" if cumulative_move > FLAT_TOLERANCE
            else "Decrease" if cumulative_move < -FLAT_TOLERANCE
            else "Flat"
        )

        try:
            res = run_behavior_projection(
                features=features,
                recent_baseline=recent_baseline,
                prev_rate=last_step_rate,
                curr_rate=curr,
                projection_date=projection_date,
                metal=metal,
                today_changes=changes_so_far,
                today_range=float(max(path) - min(path)),
                today_path=list(path),
                today_morning=float(path[0]),
                prev_day_changes=prev_changes,
                prev_day_range=prev_range,
                prev_date=prev_date,
                model=model,
                model_days=model_days,
                prior_day_move=prior_day_move,
                prior_day_direction=prior_day_direction,
                prior_day_magnitude=prior_day_magnitude,
                cumulative_move=cumulative_move,
                cumulative_direction=cumulative_direction,
                calendar_prev_rate=prev_rate,
                rate_at_midnight=midnight_rate,
                rate_timeline=steps,
                previous_day_rate_timeline=previous_day_rate_timeline,
                behavior_features=behavior_features,
                supporting_windows=rate_windows,
                spike_decay=spike_decay,
                trend_boost=trend_boost,
            )
        except Exception as exc:
            logger.exception("Behaviour projection failed at step %s", i)
            res = {"status": "STEP_ERROR",
                   "error": f"{type(exc).__name__}: {exc}"}

        results.append({
            "step_index": i,
            "time": step.get("time"),
            "rate": curr,
            "kind": kind,
            "delta_from_prev": step_delta,
            "delta_pct": step_pct,
            "net_vs_midnight": net_move,
            "status": res.get("status", "UNKNOWN"),
            "result": res,
        })
        last_step_rate = curr

    return results


# ─────────────────────────────────────────────────────────────
# FULL-DAY BEHAVIOUR PROJECTION
# ─────────────────────────────────────────────────────────────
def project_full_day_behavior(features, daily_cust, daily, timeline,
                              projection_date, metal,
                              model_days=BEHAVIOR_MODEL_DAYS,
                              baseline_days=BEHAVIOR_BASELINE_DAYS,
                              spike_decay=BEHAVIOR_SPIKE_DECAY,
                              trend_boost=BEHAVIOR_TREND_BOOST,
                              rate_windows=None):
    prev_rate = float(daily["Day Close Rate"].iloc[-1])
    prev_date = daily["Date"].iloc[-1]
    prev_changes = int(daily["Intraday Changes"].iloc[-1])
    prev_range = float(daily["Intraday Range ₹"].iloc[-1])

    if len(daily) >= 2:
        prior_day_move = float(
            daily["Day Close Rate"].iloc[-1] - daily["Day Close Rate"].iloc[-2]
        )
    else:
        prior_day_move = 0.0

    prior_day_direction = (
        "Increase" if prior_day_move > FLAT_TOLERANCE
        else "Decrease" if prior_day_move < -FLAT_TOLERANCE
        else "Flat"
    )
    prior_day_magnitude = _magnitude_bucket(prior_day_move) or "Flat"

    if len(daily) >= 2:
        lookback = min(BEHAVIOR_CONTEXT_LOOKBACK, len(daily) - 1)
        prior_days = daily.iloc[-(lookback + 1):-1]
        prior_day_moves = prior_days["Day Close Rate"].diff().dropna()
        prior_cumulative_move = (
            float(prior_day_moves.sum()) if len(prior_day_moves) else 0.0
        )
    else:
        prior_cumulative_move = 0.0

    prior_cumulative_direction = (
        "Increase" if prior_cumulative_move > FLAT_TOLERANCE
        else "Decrease" if prior_cumulative_move < -FLAT_TOLERANCE
        else "Flat"
    )

    recent_baseline = _recent_baseline_weighted(
        daily_cust, baseline_days
    )
    behavior_features = build_rate_window_features(rate_windows)
    model = build_behavior_model(
        behavior_features if not behavior_features.empty else features,
        recent_days=model_days,
        baseline_days=baseline_days,
        baseline=recent_baseline,
    )

    steps = timeline.get("steps", [])
    path = timeline.get("path", [])
    opening_rate = float(path[0]) if path else prev_rate
    closing_rate = float(path[-1]) if path else prev_rate
    intraday_changes = int(timeline.get("changes", 0))
    intraday_range = float(timeline.get("intraday_rng", 0.0))
    intraday_net_move = float(timeline.get("net_move", 0.0))
    total_abs_move = float(sum(
        abs(s.get("delta", 0.0)) for s in steps
        if s.get("kind") in ("up", "down")
    ))

    combined_cumulative_move = prior_cumulative_move + intraday_net_move
    combined_cumulative_direction = (
        "Increase" if combined_cumulative_move > FLAT_TOLERANCE
        else "Decrease" if combined_cumulative_move < -FLAT_TOLERANCE
        else "Flat"
    )

    previous_day_rate_timeline = []
    if rate_windows is not None and not rate_windows.empty:
        window_dates = pd.to_datetime(rate_windows["Date"]).dt.normalize()
        prior_windows = rate_windows[
            window_dates == pd.Timestamp(prev_date).normalize()
        ]
        for _, window in prior_windows.iterrows():
            previous_day_rate_timeline.append({
                "time": pd.Timestamp(window["Window Start"]).strftime(
                    "%H:%M:%S" if pd.Timestamp(
                        window["Window Start"]
                    ).second else "%H:%M"
                ),
                "rate": float(window["Active Rate"]),
                "delta": float(window["Rate Change ₹"]),
            })

    try:
        result = run_behavior_projection(
            features=features,
            recent_baseline=recent_baseline,
            prev_rate=opening_rate,
            curr_rate=closing_rate,
            projection_date=projection_date,
            metal=metal,
            today_changes=intraday_changes,
            today_range=intraday_range,
            today_path=list(path),
            today_morning=opening_rate,
            prev_day_changes=prev_changes,
            prev_day_range=prev_range,
            prev_date=prev_date,
            model=model,
            model_days=model_days,
            prior_day_move=prior_day_move,
            prior_day_direction=prior_day_direction,
            prior_day_magnitude=prior_day_magnitude,
            cumulative_move=combined_cumulative_move,
            cumulative_direction=combined_cumulative_direction,
            calendar_prev_rate=prev_rate,
            rate_at_midnight=opening_rate,
            rate_timeline=steps,
            previous_day_rate_timeline=previous_day_rate_timeline,
            behavior_features=behavior_features,
            supporting_windows=rate_windows,
            spike_decay=spike_decay,
            trend_boost=trend_boost,
        )
    except Exception as exc:
        logger.exception("Full-day behaviour projection failed")
        return {"status": "STEP_ERROR",
                "error": f"{type(exc).__name__}: {exc}"}

    if result.get("status") != "OK":
        return result

    result["Full-Day Context"] = {
        "Opening Rate (12:00 AM)": opening_rate,
        "Closing Rate": closing_rate,
        "Intraday Net Move ₹": intraday_net_move,
        "Intraday Net Move Direction": (
            "Increase" if intraday_net_move > FLAT_TOLERANCE
            else "Decrease" if intraday_net_move < -FLAT_TOLERANCE
            else "Flat"
        ),
        "Intraday Cumulative Movement ₹": intraday_net_move,
        "Total Absolute Intraday Movement ₹": total_abs_move,
        "Intraday Changes": intraday_changes,
        "Intraday Range ₹": intraday_range,
        "Prior Completed Days Cumulative Move ₹": prior_cumulative_move,
        "Prior Completed Days Direction": prior_cumulative_direction,
        "Combined Cumulative Move ₹": combined_cumulative_move,
        "Combined Cumulative Direction": combined_cumulative_direction,
    }

    result["Cumulative Direction"] = combined_cumulative_direction
    result["Cumulative Move ₹"] = combined_cumulative_move
    result["Intraday Cumulative Direction"] = (
        "Increase" if intraday_net_move > FLAT_TOLERANCE
        else "Decrease" if intraday_net_move < -FLAT_TOLERANCE
        else "Flat"
    )
    result["Intraday Cumulative Move ₹"] = intraday_net_move
    return result


# ─────────────────────────────────────────────────────────────
# BACKTEST
# ─────────────────────────────────────────────────────────────
def _rebuild_timeline_from_windows(rate_windows, target_date):
    if rate_windows is None or rate_windows.empty:
        return None

    target_date = pd.Timestamp(target_date).normalize()
    dates = pd.to_datetime(rate_windows["Date"]).dt.normalize()
    day_windows = rate_windows[dates == target_date].copy()
    if day_windows.empty:
        return None

    day_windows = day_windows.sort_values("Window Start")

    steps = []
    last_rate = None
    for _, w in day_windows.iterrows():
        start = pd.Timestamp(w["Window Start"])
        rate = float(w["Active Rate"])
        t_str = start.strftime("%I:%M %p").lstrip("0") or "12:00 am"

        if last_rate is None:
            steps.append({
                "time": t_str, "rate": rate, "delta": 0.0, "kind": "start",
            })
            last_rate = rate
        else:
            delta = rate - last_rate
            if abs(delta) < FLAT_TOLERANCE:
                continue
            steps.append({
                "time": t_str,
                "rate": rate,
                "delta": delta,
                "kind": "up" if delta > 0 else "down",
            })
            last_rate = rate

    if not steps:
        return None

    if str(steps[-1]["time"]).strip().lower() != "11:59 pm":
        steps.append({
            "time": "11:59 pm",
            "rate": float(steps[-1]["rate"]),
            "delta": 0.0,
            "kind": "flat",
        })

    path = [s["rate"] for s in steps]
    changes = len([s for s in steps if s["kind"] in ("up", "down")])
    return {
        "path": path,
        "changes": changes,
        "intraday_rng": float(max(path) - min(path)),
        "latest_rate": float(path[-1]),
        "morning_rate": float(path[0]),
        "net_move": float(path[-1] - path[0]),
        "valid": True,
        "errors": [],
        "steps": steps,
    }


def backtest_previous_date(df, metal, target_date,
                           model_days=BEHAVIOR_MODEL_DAYS,
                           baseline_days=BEHAVIOR_BASELINE_DAYS,
                           spike_decay=BEHAVIOR_SPIKE_DECAY,
                           trend_boost=BEHAVIOR_TREND_BOOST):
    target_date = pd.Timestamp(target_date).normalize()
    out = {
        "status": "NO_DATA",
        "target_date": target_date,
        "metal": metal,
        "model_days": int(model_days),
        "baseline_days": int(baseline_days),
    }

    hist = df[df["Date"].dt.normalize() < target_date].copy()
    if hist.empty:
        out["status"] = "NO_HISTORY"
        return out

    daily_hist = build_daily_rate_series(hist, metal)
    if daily_hist.empty or len(daily_hist) < 10:
        out["status"] = "NOT_ENOUGH_HISTORY"
        out["history_days"] = len(daily_hist)
        return out

    rate_windows_hist = build_rate_window_customer_series(
        hist, metal, daily_hist
    )

    full_daily = build_daily_rate_series(df, metal)
    full_windows = build_rate_window_customer_series(
        df, metal, full_daily
    )
    timeline = _rebuild_timeline_from_windows(full_windows, target_date)
    if timeline is None:
        out["status"] = "NO_RATE_PATH"
        return out
    out["timeline"] = timeline

    actual_daily = build_daily_customer_series(df, metal)
    actual_daily["Date"] = pd.to_datetime(actual_daily["Date"]).dt.normalize()
    actual_row = actual_daily[actual_daily["Date"] == target_date]
    if actual_row.empty:
        out["status"] = "NO_ACTUALS"
        return out

    actual = actual_row.iloc[0].to_dict()
    out["actual"] = actual

    hist_cust = build_daily_customer_series(hist, metal)
    recent_baseline = _recent_baseline_weighted(hist_cust, baseline_days)
    out["baseline"] = recent_baseline

    features_hist = build_pattern_features(daily_hist, hist_cust)

    try:
        result = project_full_day_behavior(
            features=features_hist,
            daily_cust=hist_cust,
            daily=daily_hist,
            timeline=timeline,
            projection_date=target_date,
            metal=metal,
            model_days=model_days,
            baseline_days=baseline_days,
            spike_decay=spike_decay,
            trend_boost=trend_boost,
            rate_windows=rate_windows_hist,
        )
    except Exception as exc:
        logger.exception("Backtest projection failed for %s %s",
                         metal, target_date)
        out["status"] = "PROJECTION_ERROR"
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out

    if result.get("status") != "OK":
        out["status"] = result.get("status", "NO_PROJECTION")
        out["projection_result"] = result
        return out

    out["status"] = "OK"
    out["projection_result"] = result
    out["projection"] = result["Projection"]
    out["range"] = result["Range"]

    metric_defs = [
        ("Enrolment", "Enrolment", 0),
        ("Enrolment Amount", "Enrolment Amount", 0),
        ("Collection Count", "Collection Count", 0),
        ("Collection", "Collection", 0),
        ("Saved Weight", "Saved Weight", 3),
        ("Reward Weight", "Reward Weight", 3),
        ("Total Weight", "Total Weight", 3),
    ]
    variance_rows = []
    for label, key, decimals in metric_defs:
        p = float(result["Projection"].get(key, 0.0))
        a = float(actual.get(key, 0.0))
        diff = p - a
        pct = (diff / a * 100.0) if abs(a) > 1e-9 else np.nan
        rng = result["Range"].get(key)
        in_range = (
            (rng[0] <= a <= rng[2]) if rng is not None else False
        )
        variance_rows.append({
            "Metric": label,
            "Projected": round(p, decimals),
            "Actual": round(a, decimals),
            "Difference": round(diff, decimals),
            "Diff %": round(pct, 2) if pd.notna(pct) else np.nan,
            "Projected Range Low": round(rng[0], decimals) if rng else np.nan,
            "Projected Range High": round(rng[2], decimals) if rng else np.nan,
            "Actual in Range": "✅" if in_range else "❌",
        })
    out["variance"] = pd.DataFrame(variance_rows)

    return out


def _render_backtest_panel(df, metal, daily_rate_all, cfg):
    st.markdown("---")
    st.markdown(
        '<div class="section-title"><span class="accent"></span>'
        '<span class="text">4️⃣ 🧾 Previous day — projection vs actuals'
        '<span class="layer-badge l3">Validation</span>'
        '</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Pick any past date and see what the **same engine** would have "
        "projected for it (using only data available before that day), "
        "compared against the actual observed outcome."
    )

    if daily_rate_all is None or daily_rate_all.empty:
        st.info("No rate history available for backtesting.")
        return

    model_days = int(cfg.get("_reaction_window", BEHAVIOR_MODEL_DAYS))
    baseline_days = cfg.get("baseline_days", BEHAVIOR_BASELINE_DAYS)
    spike_decay = cfg.get("spike_decay", BEHAVIOR_SPIKE_DECAY)
    trend_boost = cfg.get("trend_boost", BEHAVIOR_TREND_BOOST)

    dates = pd.to_datetime(
        daily_rate_all["Date"]
    ).dt.normalize().sort_values().unique()
    if len(dates) < 11:
        st.info(
            "Not enough rate history to backtest yet "
            "(need at least 10 prior days)."
        )
        return

    selectable = [d for d in dates
                  if (pd.Timestamp(d) - pd.Timedelta(days=10)) >= dates[0]]
    if not selectable:
        st.info(
            "Not enough rate history to backtest yet "
            "(need at least 10 prior days)."
        )
        return

    default_date = pd.Timestamp(selectable[-1])

    bc1, bc2 = st.columns([1.2, 3])
    with bc1:
        chosen = st.date_input(
            "Previous date",
            value=default_date.date(),
            min_value=pd.Timestamp(selectable[0]).date(),
            max_value=pd.Timestamp(selectable[-1]).date(),
            key=f"backtest_date_{metal}",
        )
    chosen = pd.Timestamp(chosen).normalize()

    with st.spinner("Re-running the projection as of that date..."):
        bt = backtest_previous_date(
            df=df,
            metal=metal,
            target_date=chosen,
            model_days=model_days,
            baseline_days=baseline_days,
            spike_decay=spike_decay,
            trend_boost=trend_boost,
        )

    reason_map = {
        "NO_HISTORY": "No history before that date.",
        "NOT_ENOUGH_HISTORY":
            "Not enough prior rate history (need ≥ 10 days).",
        "NO_RATE_PATH":
            "No rate-change path recorded for that date.",
        "NO_ACTUALS":
            "No customer transactions recorded for that date.",
        "NO_BEHAVIOR_MODEL":
            "Behaviour model could not be built from prior data.",
        "NO_USABLE_BUCKET":
            "No usable behavioural bucket for that day's rate move.",
        "PROJECTION_ERROR": "The projection engine raised an error.",
    }
    if bt.get("status") != "OK":
        st.warning(
            f"⚠️ Cannot backtest **{chosen.strftime('%d-%m-%Y')}** — "
            f"{reason_map.get(bt.get('status'), bt.get('status'))}"
        )
        if bt.get("error"):
            with st.expander("Technical details", expanded=False):
                st.code(bt["error"])
        return

    proj = bt["projection"]
    actual = bt["actual"]
    variance = bt["variance"]
    result = bt["projection_result"]
    timeline = bt["timeline"]

    icon = "🟡" if metal == "Gold" else "⚪"
    st.markdown(
        f'<div class="callout callout-info">'
        f'{icon} <b>{metal}</b> · '
        f'Backtest date: <b>{chosen.strftime("%d-%m-%Y")}</b> · '
        f"Rate path: {timeline['changes']} change(s) · "
        f"opening ₹{timeline['path'][0]:,.2f} → "
        f"closing ₹{timeline['path'][-1]:,.2f} · "
        f"Bucket: <b>{result.get('Bucket Source', '—')}</b> "
        f"({result.get('Bucket Days', 0)} days) · "
        f"Reliability: <b>{result.get('Reliability', '—')}</b>"
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        _render_timeline_preview(timeline),
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)

    def _kpi(col, label, key, decimals, prefix="", suffix=""):
        p = float(proj.get(key, 0.0))
        a = float(actual.get(key, 0.0))
        diff = p - a
        pct = (diff / a * 100.0) if abs(a) > 1e-9 else np.nan
        if decimals == 0:
            p_s = f"{prefix}{int(round(p)):,}{suffix}"
            a_s = f"{prefix}{int(round(a)):,}{suffix}"
            d_s = f"{prefix}{int(round(diff)):+,}{suffix}"
        else:
            p_s = f"{prefix}{p:,.{decimals}f}{suffix}"
            a_s = f"{prefix}{a:,.{decimals}f}{suffix}"
            d_s = f"{prefix}{diff:+,.{decimals}f}{suffix}"
        pct_s = f"{pct:+.1f}%" if pd.notna(pct) else "—"

        col.markdown(
            f'<div class="metric-label">{label}</div>'
            f'<div class="metric-value">{p_s}</div>'
            f'<div style="font-size:0.85rem; color:#6b7280; '
            f'margin-top:6px;">'
            f'Actual: <b>{a_s}</b> · '
            f'Diff: <b>{d_s}</b> ({pct_s})'
            f'</div>',
            unsafe_allow_html=True,
        )

    _kpi(c1, "👥 Enrolments", "Enrolment", 0)
    _kpi(c2, "💰 Collection (₹)", "Collection", 0, prefix="₹")
    _kpi(c3, "⚖️ Total Weight (g)", "Total Weight", 3)

    st.markdown("##### 📊 Full projection vs actuals")

    styled = variance.style.format({
        "Projected": "{:,.3f}",
        "Actual": "{:,.3f}",
        "Difference": "{:+,.3f}",
        "Diff %": "{:+.2f}%",
        "Projected Range Low": "{:,.3f}",
        "Projected Range High": "{:,.3f}",
    }, na_rep="—")

    st.dataframe(styled, hide_index=True, use_container_width=True)

    if not variance.empty:
        valid_pct = variance["Diff %"].dropna()
        in_range_count = int((variance["Actual in Range"] == "✅").sum())
        total = int(len(variance))
        mape = (
            float(valid_pct.abs().mean()) if not valid_pct.empty else np.nan
        )
        bias = float(valid_pct.mean()) if not valid_pct.empty else np.nan

        s1, s2, s3 = st.columns(3)
        s1.metric(
            "Metrics in projected range",
            f"{in_range_count}/{total}",
        )
        s2.metric(
            "Mean abs error % (MAPE)",
            f"{mape:.1f}%" if pd.notna(mape) else "—",
        )
        s3.metric(
            "Bias (avg signed error)",
            f"{bias:+.1f}%" if pd.notna(bias) else "—",
            help="Positive = model over-projects on average.",
        )

    with st.expander("🔬 Backtest context details", expanded=False):
        st.markdown("**Rate timeline used for the projection**")
        st.dataframe(
            pd.DataFrame(timeline["steps"]).style.format({
                "rate": "₹{:,.2f}",
                "delta": "₹{:+,.2f}",
            }),
            hide_index=True,
            use_container_width=True,
        )

        st.markdown("**Baseline used (recency-weighted)**")
        st.dataframe(
            pd.DataFrame([
                {"Metric": k, "Baseline": round(v, 3)}
                for k, v in bt["baseline"].items()
            ]),
            hide_index=True,
            use_container_width=True,
        )

        st.markdown("**Multipliers applied**")
        st.dataframe(
            pd.DataFrame([
                {"Metric": k, "Multiplier": round(v, 4)}
                for k, v in result.get("Multipliers", {}).items()
            ]),
            hide_index=True,
            use_container_width=True,
        )

    out = variance.copy()
    out.insert(0, "Date", chosen.strftime("%d-%m-%Y"))
    out.insert(1, "Metal", metal)
    st.download_button(
        "⬇️ Download backtest CSV",
        data=out.to_csv(index=False).encode("utf-8-sig"),
        mime="text/csv",
        file_name=(
            f"{metal.lower()}_backtest_{chosen.date()}.csv"
        ),
        key=f"bt_dl_{metal}_{chosen.date()}",
        use_container_width=False,
    )


# ─────────────────────────────────────────────────────────────
# TODAY TIMELINE
# ─────────────────────────────────────────────────────────────
def _parse_time(t):
    if t is None:
        return None
    s = str(t).strip().lower()
    if not s:
        return None
    for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p", "%I %p", "%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            continue
    return None


def build_today_timeline(timeline_inputs):
    clean = []
    for row in timeline_inputs:
        try:
            r = float(row.get("rate", 0) or 0)
        except (TypeError, ValueError):
            r = 0.0
        if r > 0:
            clean.append((row.get("time"), r))

    empty = {
        "path": [], "changes": 0, "intraday_rng": 0.0,
        "latest_rate": 0.0, "morning_rate": 0.0, "net_move": 0.0,
        "valid": False, "errors": ["No valid rates entered."], "steps": [],
    }
    if not clean:
        return empty

    parsed = [(_parse_time(t), t, r) for t, r in clean]
    if all(p[0] is not None for p in parsed):
        parsed.sort(key=lambda x: x[0])

    steps = []
    last = None
    for _, t_str, r in parsed:
        if last is None:
            steps.append({"time": t_str, "rate": float(r),
                          "delta": 0.0, "kind": "start"})
            last = float(r)
        else:
            d = float(r) - last
            if abs(d) < FLAT_TOLERANCE:
                continue
            steps.append({"time": t_str, "rate": float(r), "delta": d,
                          "kind": "up" if d > 0 else "down"})
            last = float(r)

    if steps and str(steps[-1]["time"]).strip().lower() != "11:59 pm":
        steps.append({
            "time": "11:59 pm",
            "rate": float(steps[-1]["rate"]),
            "delta": 0.0,
            "kind": "flat",
        })

    path = [s["rate"] for s in steps]
    changes = len([s for s in steps if s["kind"] in ["up", "down"]])
    errors = []
    if changes > INTRADAY_EXPECTED_MAX:
        errors.append(
            f"{changes} changes exceeds your business maximum of "
            f"{INTRADAY_EXPECTED_MAX}."
        )

    return {
        "path": path,
        "changes": changes,
        "intraday_rng": float(max(path) - min(path)),
        "latest_rate": float(path[-1]),
        "morning_rate": float(path[0]),
        "net_move": float(path[-1] - path[0]),
        "valid": True,
        "errors": errors,
        "steps": steps,
    }


# ─────────────────────────────────────────────────────────────
# PDF EXPORT
# ─────────────────────────────────────────────────────────────
def _fmt_money(v, decimals=0):
    try:
        return f"Rs.{float(v):,.{decimals}f}"
    except (TypeError, ValueError):
        return "-"


def _fmt_num(v, decimals=2):
    try:
        return f"{float(v):,.{decimals}f}"
    except (TypeError, ValueError):
        return "-"


def _fmt_int(v):
    try:
        return f"{int(round(float(v))):,}"
    except (TypeError, ValueError):
        return "-"


def _fmt_range(rng_tuple, decimals=0, prefix="", suffix=""):
    try:
        lo, _mid, hi = rng_tuple
        if decimals == 0:
            return f"{prefix}{int(round(lo)):,} - {prefix}{int(round(hi)):,}{suffix}"
        return (f"{prefix}{float(lo):,.{decimals}f} - "
                f"{prefix}{float(hi):,.{decimals}f}{suffix}")
    except (TypeError, ValueError):
        return "-"


def _build_projection_pdf(metal, projection_date, full_day_result,
                          step_results, model_days, baseline_days):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"{metal} Projection - {projection_date.strftime('%d %b %Y')}",
        author="Today's Projection App",
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"],
        fontSize=18, leading=22, textColor=colors.HexColor("#111827"),
        spaceAfter=4,
    )
    h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=13, leading=17, textColor=colors.HexColor("#111827"),
        spaceBefore=12, spaceAfter=6,
    )
    h3 = ParagraphStyle(
        "H3", parent=styles["Heading3"],
        fontSize=11, leading=14, textColor=colors.HexColor("#1f2937"),
        spaceBefore=8, spaceAfter=4,
    )
    body = ParagraphStyle(
        "Body", parent=styles["BodyText"],
        fontSize=9, leading=12, textColor=colors.HexColor("#374151"),
    )
    small = ParagraphStyle(
        "Small", parent=styles["BodyText"],
        fontSize=8, leading=10, textColor=colors.HexColor("#6b7280"),
    )
    label_style = ParagraphStyle(
        "Label", parent=styles["BodyText"],
        fontSize=7.5, leading=9, textColor=colors.HexColor("#6b7280"),
    )
    value_lg = ParagraphStyle(
        "ValueLg", parent=styles["BodyText"],
        fontSize=15, leading=17, textColor=colors.HexColor("#111827"),
        fontName="Helvetica-Bold",
    )

    accent = colors.HexColor("#2b7cd3")
    soft_bg = colors.HexColor("#f7f7fb")
    border = colors.HexColor("#e6e8ef")

    story = []

    story.append(Paragraph(f"{metal} - Today's Projection", h1))
    story.append(Paragraph(
        f"Projection date: <b>{projection_date.strftime('%d %B %Y')}</b> | "
        f"Behaviour model: last <b>{model_days} days</b> | "
        f"Baseline: last <b>{baseline_days} days</b>",
        body,
    ))
    story.append(Spacer(1, 6))

    if full_day_result.get("status") != "OK":
        story.append(Paragraph(
            "No full-day projection available for this configuration.",
            body,
        ))
        doc.build(story)
        return buffer.getvalue()

    fdr = full_day_result
    proj = fdr.get("Projection", {})
    rng = fdr.get("Range", {})

    story.append(Paragraph("1. Rate context", h2))

    prev_close = fdr.get("previous_calendar_day_rate", 0.0)
    midnight = fdr.get("rate_at_midnight", 0.0)
    curr = fdr.get("manual_curr_rate", 0.0)
    move_rs = fdr.get("today_move_rs", 0.0)
    move_pct = fdr.get("today_move_pct", 0.0)
    direction = fdr.get("direction", "-")
    magnitude = fdr.get("magnitude", "-")

    ctx_data = [
        ["Previous calendar-day close", _fmt_money(prev_close, 2)],
        ["Rate at 12:00 AM", _fmt_money(midnight, 2)],
        ["Current active rate", _fmt_money(curr, 2)],
        ["Current move vs previous step",
         f"{_fmt_money(move_rs, 2)} ({move_pct:+.2f}%)"],
        ["Direction / Magnitude", f"{direction} / {magnitude}"],
        ["Intraday changes", f"{fdr.get('Today Intraday Changes', 0)}"],
        ["Intraday range",
         _fmt_money(fdr.get("Today Intraday Range", 0.0), 2)],
        ["Prior day direction / move",
         f"{fdr.get('Prior Day Direction', '-')} / "
         f"{_fmt_money(fdr.get('Prior Day Move', 0.0), 2)}"],
        ["Combined cumulative direction / move",
         f"{fdr.get('Cumulative Direction', '-')} / "
         f"{_fmt_money(fdr.get('Cumulative Move', 0.0), 2)}"],
        ["Bucket used / days",
         f"{fdr.get('Bucket Source', '-')} / "
         f"{fdr.get('Bucket Days', 0)}"],
        ["Reliability", fdr.get("Reliability", "-")],
    ]
    ctx_table = Table(ctx_data, colWidths=[70 * mm, 105 * mm])
    ctx_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), soft_bg),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#374151")),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#111827")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.3, border),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(ctx_table)

    story.append(Paragraph("2. Projected metrics", h2))

    metrics = [
        ("New Enrolments", _fmt_int(proj.get("Enrolment")),
         _fmt_range(rng.get("Enrolment"), 0)),
        ("Collection", _fmt_money(proj.get("Collection")),
         _fmt_range(rng.get("Collection"), 0, prefix="Rs.")),
        ("Total Weight (g)", _fmt_num(proj.get("Total Weight"), 3),
         _fmt_range(rng.get("Total Weight"), 3)),
        ("Enrolment Amount", _fmt_money(proj.get("Enrolment Amount")),
         _fmt_range(rng.get("Enrolment Amount"), 0, prefix="Rs.")),
        ("Collection Count", _fmt_int(proj.get("Collection Count")),
         _fmt_range(rng.get("Collection Count"), 0)),
        ("Saved Weight (g)", _fmt_num(proj.get("Saved Weight"), 3),
         _fmt_range(rng.get("Saved Weight"), 3)),
        ("Reward Weight (g)", _fmt_num(proj.get("Reward Weight"), 3),
         _fmt_range(rng.get("Reward Weight"), 3)),
        ("Enrolment metal (g)",
         _fmt_num((proj.get("Enrolment Amount", 0.0) / max(curr, 1e-9)), 3),
         "-"),
        ("Collection metal (g)",
         _fmt_num((proj.get("Collection", 0.0) / max(curr, 1e-9)), 3),
         "-"),
    ]

    rows = []
    for i in range(0, len(metrics), 3):
        chunk = metrics[i:i + 3]
        row_cells = []
        for name, val, rngtxt in chunk:
            cell_table = Table(
                [[Paragraph(name, label_style)],
                 [Paragraph(val, value_lg)],
                 [Paragraph(f"Range: {rngtxt}", small)]],
                colWidths=[56 * mm],
            )
            cell_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), soft_bg),
                ("BOX", (0, 0), (0, -1), 0.4, border),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            row_cells.append(cell_table)
        while len(row_cells) < 3:
            row_cells.append(Spacer(1, 1))
        rows.append(row_cells)

    grid = Table(rows, colWidths=[58 * mm] * 3)
    grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(grid)

    story.append(Paragraph("3. How the projection was derived", h2))

    baseline = fdr.get("Baseline", {})
    multipliers = fdr.get("Multipliers", {})
    behavior_proj = fdr.get("Behavior Projection", proj)

    calc_rows = [["Metric", "Baseline", "Multiplier", "Raw projection"]]
    for m in ["Enrolment", "Enrolment Amount", "Collection Count",
              "Collection", "Saved Weight", "Reward Weight",
              "Total Weight"]:
        calc_rows.append([
            m,
            _fmt_num(baseline.get(m, 0.0), 3),
            f"x{float(multipliers.get(m, 1.0)):.3f}",
            _fmt_num(behavior_proj.get(m, 0.0), 3),
        ])
    calc_table = Table(calc_rows, colWidths=[55 * mm, 40 * mm, 35 * mm, 45 * mm])
    calc_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), accent),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.3, border),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(calc_table)

    story.append(Paragraph("Business-rule coherence checks", h3))
    saved_weight = float(proj.get("Saved Weight", 0.0))
    reward_weight = float(proj.get("Reward Weight", 0.0))
    total_weight = float(proj.get("Total Weight", 0.0))
    enrol = float(proj.get("Enrolment", 0.0))
    enrol_amt = float(proj.get("Enrolment Amount", 0.0))
    collection = float(proj.get("Collection", 0.0))

    checks = [
        ["Saved Weight = (Enrol Amt + Collection) / rate",
         f"{saved_weight:.2f} g",
         "OK" if curr > 1e-9 else "N/A"],
        ["Reward Weight = Saved Weight x reward ratio",
         f"{reward_weight:.2f} g", "OK"],
        ["Total Weight = Saved + Reward",
         f"{total_weight:.2f} g", "OK"],
        ["Enrolment Amount = Enrolment x avg ticket",
         f"{_fmt_money(enrol_amt, 2)}", "OK"],
    ]
    check_table = Table(
        [["Rule", "Projected value", "Status"]] + checks,
        colWidths=[90 * mm, 45 * mm, 40 * mm],
    )
    check_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), accent),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.3, border),
        ("ALIGN", (1, 0), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(check_table)

    momentum = fdr.get("Momentum Adjustment")
    if momentum:
        story.append(Paragraph("Context adjustments applied", h3))
        for k, v in momentum.items():
            if isinstance(v, dict):
                inner = "; ".join(f"{kk}: {vv}" for kk, vv in v.items())
                story.append(Paragraph(f"<b>{k}</b> - {inner}", small))
            else:
                story.append(Paragraph(f"<b>{k}</b>: {v}", small))

    fd_ctx = fdr.get("Full-Day Context")
    if fd_ctx:
        story.append(Paragraph("4. Full-day intraday context", h2))
        ctx_rows = [["Field", "Value"]]
        for k, v in fd_ctx.items():
            if isinstance(v, float):
                ctx_rows.append([k, _fmt_num(v, 2)])
            else:
                ctx_rows.append([k, str(v)])
        fd_table = Table(ctx_rows, colWidths=[90 * mm, 85 * mm])
        fd_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), accent),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.3, border),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(fd_table)

    supporting = fdr.get("Supporting Matches")
    if supporting is not None and not supporting.empty:
        story.append(PageBreak())
        story.append(Paragraph("5. Supporting historical evidence", h2))
        story.append(Paragraph(
            f"Closest historical windows with similar rate moves "
            f"(tolerance Rs.{DEFAULT_MATCH_TOLERANCE_RS:.0f}).",
            small,
        ))
        story.append(Spacer(1, 4))
        cols = list(supporting.columns)
        data = [cols]
        for _, row in supporting.iterrows():
            data.append([
                str(row[c]) if not isinstance(row[c], float)
                else f"{row[c]:,.2f}"
                for c in cols
            ])
        n = len(cols)
        cw = [180 * mm / n] * n
        sup_table = Table(data, colWidths=cw, repeatRows=1)
        sup_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), accent),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.25, border),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(sup_table)

    if step_results:
        story.append(PageBreak())
        story.append(Paragraph("6. Step-wise projections", h2))
        story.append(Paragraph(
            "Each row is an alternative full-day-equivalent snapshot at "
            "that moment in the day.",
            small,
        ))
        story.append(Spacer(1, 4))

        step_cols = [
            "Step", "Time", "Rate", "Delta", "Move vs midnight",
            "Enrolments", "Collection", "Total Weight",
            "Bucket", "Reliability",
        ]
        data = [step_cols]
        for i, s in enumerate(step_results, start=1):
            r = s.get("result") or {}
            p = r.get("Projection", {}) or {}
            data.append([
                str(i),
                str(s.get("time", "-")),
                _fmt_num(s.get("rate", 0.0), 2),
                _fmt_num(s.get("delta_from_prev", 0.0), 2),
                _fmt_num(s.get("net_vs_midnight", 0.0), 2),
                _fmt_int(p.get("Enrolment")),
                _fmt_money(p.get("Collection")),
                _fmt_num(p.get("Total Weight"), 3),
                str(r.get("Bucket Source", "-")),
                str(r.get("Reliability", "-")),
            ])

        step_table = Table(
            data,
            colWidths=[12 * mm, 20 * mm, 20 * mm, 16 * mm, 22 * mm,
                       20 * mm, 25 * mm, 22 * mm, 18 * mm, 20 * mm],
            repeatRows=1,
        )
        step_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), accent),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.25, border),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (0, 0), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(step_table)

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d-%m-%Y %H:%M:%S')} | "
        f"Context-aware behaviour model | "
        f"Baseline {baseline_days}d | Model {model_days}d",
        small,
    ))

    doc.build(story)
    return buffer.getvalue()


# ─────────────────────────────────────────────────────────────
# DATA SOURCE (default file + optional override)
# ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl="1h")
def _download_default_data():
    with urlopen(DEFAULT_DATA_URL, timeout=60) as response:
        file_bytes = response.read()
    if not file_bytes:
        raise OSError("The GitHub workbook was empty.")
    return file_bytes


def render_data_source_sidebar():
    """
    Prefer an explicit upload, then the local default, then the GitHub copy.
    """
    st.sidebar.markdown("##### 📁 Data source")

    default_exists = DEFAULT_DATA_PATH.exists()
    if default_exists:
        st.sidebar.caption(
            f"✅ Default file loaded:\n`{DEFAULT_DATA_PATH}`"
        )
    else:
        st.sidebar.caption(
            f"ℹ️ Local default file not found:\n`{DEFAULT_DATA_PATH}`\n"
            "Trying the GitHub copy."
        )

    with st.sidebar.expander("📤 Override with upload (optional)",
                             expanded=False):
        uploaded = st.file_uploader(
            "Upload transaction file",
            type=["csv", "xlsx", "xls"],
            key="data_source_upload",
        )
        if uploaded is not None:
            return {
                "bytes": uploaded.getvalue(),
                "name": uploaded.name,
                "source": "upload",
            }

    if default_exists:
        try:
            with open(DEFAULT_DATA_PATH, "rb") as f:
                return {
                    "bytes": f.read(),
                    "name": DEFAULT_DATA_PATH.name,
                    "source": "default",
                }
        except OSError as exc:
            st.sidebar.error(f"❌ Could not read default file: {exc}")
            return None

    try:
        return {
            "bytes": _download_default_data(),
            "name": "transaction_data.xlsx",
            "source": "github",
        }
    except OSError as exc:
        st.sidebar.error(f"❌ Could not download the default file from GitHub: {exc}")
        st.sidebar.caption(
            "Upload a transaction file using the sidebar override."
        )
        return None


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
def _debug_last_close(df, metal):
    sub = df[df["Metal Type"] == metal]
    if sub.empty:
        return None
    daily = build_daily_rate_series(df, metal)
    if daily.empty:
        return None
    last = daily.iloc[-1]
    return {
        "date": last["Date"],
        "rate": float(last["Metal Rate"]),
        "set_at": last.get("Rate Set At", pd.NaT),
        "day_close_rate": float(last.get("Day Close Rate", last["Metal Rate"])),
        "day_close_at": last.get("Day Close At", pd.NaT),
        "intraday_changes": int(last.get("Intraday Changes", 0)),
        "intraday_range": float(last.get("Intraday Range ₹", 0.0)),
    }


def render_sidebar():
    st.sidebar.markdown("""
    <div class="sidebar-brand">
        <div class="title">⚙️ Projection Setup</div>
        <div class="sub">Data source · date · model controls</div>
    </div>
    """, unsafe_allow_html=True)

    selected = render_data_source_sidebar()

    df, data_quality = None, None
    if selected is not None:
        try:
            df, data_quality = load_and_preprocess(
                selected["bytes"], selected["name"]
            )
            if selected.get("source") == "default":
                st.sidebar.success(
                    f"📂 Loaded default file: **{selected['name']}**"
                )
            elif selected.get("source") == "upload":
                st.sidebar.success(
                    f"📤 Loaded uploaded file: **{selected['name']}**"
                )
            elif selected.get("source") == "github":
                st.sidebar.success(
                    f"📂 Loaded default file from GitHub: **{selected['name']}**"
                )
        except Exception as exc:
            st.sidebar.error("❌ Could not read this file.")
            st.sidebar.caption(f"Details: {exc}")

    if df is not None and not df.empty:
        with st.sidebar.expander("🔍 Verify last close", expanded=False):
            for metal in ["Gold", "Silver"]:
                info = _debug_last_close(df, metal)
                if info:
                    set_at = (
                        info["set_at"].strftime("%d-%m-%Y %H:%M:%S")
                        if pd.notna(info["set_at"]) else "—"
                    )
                    st.caption(
                        f"**{metal}**: morning ₹{info['rate']:,.2f} "
                        f"(set {set_at}) · "
                        f"close ₹{info['day_close_rate']:,.2f} · "
                        f"intraday changes: {info['intraday_changes']} "
                        f"(range ₹{info['intraday_range']:,.2f})"
                    )

        if data_quality:
            with st.sidebar.expander("ℹ️ Data notes", expanded=False):
                if data_quality.get("file_order"):
                    st.caption(f"📄 File order: {data_quality['file_order']}")
                if data_quality.get("time_column_used"):
                    st.caption(
                        f"✅ Time column `{data_quality['time_column_used']}` merged"
                    )
                if data_quality.get("invalid_dates_dropped", 0) > 0:
                    st.caption(
                        f"⚠️ {data_quality['invalid_dates_dropped']:,} "
                        f"bad-Date rows dropped"
                    )
                for col, n in data_quality.get(
                    "invalid_numeric_values", {}
                ).items():
                    st.caption(f"⚠️ {n:,} bad numeric in `{col}` → 0")

    if df is not None and not df.empty:
        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing:
            return {"df": df, "error": missing}

    projection_date = None
    if df is not None and not df.empty:
        last_date = df["Date"].dt.normalize().max()
        next_day = last_date + pd.Timedelta(days=1)

        with st.sidebar.expander("📅 Today's Date", expanded=True):
            projection_date = st.date_input(
                "Project for",
                value=next_day.date(),
                key="proj_date_input",
            )
            projection_date = pd.Timestamp(projection_date).normalize()

            prev_date_key = st.session_state.get("_last_proj_date")
            this_date_key = str(projection_date.date())
            if prev_date_key != this_date_key:
                for k in list(st.session_state.keys()):
                    if k.startswith("timeline_today_"):
                        del st.session_state[k]
                st.session_state["_last_proj_date"] = this_date_key

            st.markdown(
                f"""
                <div style="font-size:0.82rem; color:#374151; padding:6px 0;">
                    Last data: <b>{last_date.strftime('%d-%m-%Y')}</b><br>
                    Projecting: <b>{projection_date.strftime('%d-%m-%Y')}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.sidebar.expander("🧠 Behaviour model settings",
                                 expanded=False):
            st.caption(
                "The **model window** is set in Section 2 "
                "(🧠 How customers reacted recently) so the reaction "
                "diagnostics and the projection always stay aligned. "
                "The controls below only affect the projection."
            )
            st.number_input(
                "Baseline window (days)",
                min_value=3, max_value=60,
                value=BEHAVIOR_BASELINE_DAYS, step=1,
                key="behavior_baseline_days_input",
                help=(
                    "Days used to compute the 'normal' daily activity level "
                    "that multipliers are applied to."
                ),
            )
            st.number_input(
                "Spike decay",
                min_value=0.0, max_value=1.0,
                value=BEHAVIOR_SPIKE_DECAY, step=0.05,
                key="behavior_spike_decay_input",
                help=(
                    "How much of yesterday's spike carries into today. "
                    "0 = no carry, 1 = full carry."
                ),
            )
            st.number_input(
                "Trend boost",
                min_value=0.0, max_value=1.0,
                value=BEHAVIOR_TREND_BOOST, step=0.05,
                key="behavior_trend_boost_input",
                help=(
                    "Extra boost when today continues the multi-day trend."
                ),
            )

    return {
        "df": df,
        "uploaded": selected,
        "projection_date": projection_date,
        "baseline_days": st.session_state.get(
            "behavior_baseline_days_input", BEHAVIOR_BASELINE_DAYS
        ),
        "spike_decay": st.session_state.get(
            "behavior_spike_decay_input", BEHAVIOR_SPIKE_DECAY
        ),
        "trend_boost": st.session_state.get(
            "behavior_trend_boost_input", BEHAVIOR_TREND_BOOST
        ),
    }


# ─────────────────────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────────────────────
def _reliability_badge(level):
    cls = {
        "HIGH": "rel-high", "MEDIUM": "rel-med",
        "LOW": "rel-low", "ROUGH": "rel-rough",
    }.get(level, "rel-rough")

    meaning = {
        "HIGH": "Strong bucket — trust this projection.",
        "MEDIUM": "Decent bucket size — use the range.",
        "LOW": "Sparse bucket — treat as a rough guide.",
        "ROUGH": "Very few observations — soft signal only.",
    }.get(level, "")

    return (
        f'<span class="{cls}">Reliability: {level}</span>'
        f'<div style="font-size:0.85rem; color:#6b7280; margin-top:6px;">'
        f'{meaning}</div>'
    )


def _render_timeline_preview(timeline):
    if not timeline or not timeline.get("path"):
        return ""
    path = timeline["path"]
    chips = []
    for i, r in enumerate(path):
        if i == 0:
            cls = "start"
            prefix = "Start"
        else:
            diff = r - path[i - 1]
            cls = "up" if diff > 0 else "down" if diff < 0 else ""
            prefix = f"{'+' if diff >= 0 else ''}{diff:,.0f}"
        chips.append(
            f'<span class="rate-step {cls}">'
            f'₹{r:,.2f} <small style="opacity:0.7">({prefix})</small>'
            f'</span>'
        )
    summary = (
        f'<div style="font-size:0.82rem; color:#6b7280; margin-top:6px;">'
        f'<b>Net move:</b> ₹{timeline["net_move"]:+,.2f} · '
        f'<b>Changes:</b> {timeline["changes"]} · '
        f'<b>Intraday range:</b> ₹{timeline["intraday_rng"]:,.2f}'
        f'</div>'
    )
    return (
        '<div style="margin-top:8px; padding:10px 12px; '
        'background:#fbfbfd; border:1px solid #e6e8ef; border-radius:10px;">'
        + "".join(chips) + summary + "</div>"
    )


def _intraday_pills(result):
    pills = []

    today_changes = result.get("Today Intraday Changes")
    today_range = result.get("Today Intraday Range ₹")
    if today_changes is not None:
        in_band = INTRADAY_EXPECTED_MIN <= today_changes <= INTRADAY_EXPECTED_MAX
        cls = "pill-ok" if in_band else "pill-warn"
        rng_str = f", range ₹{today_range:,.2f}" if today_range is not None else ""
        pills.append(
            f'<span class="pill {cls}">Today: {today_changes} '
            f'change(s){rng_str}</span>'
        )

    prev_changes = result.get("Prev Day Intraday Changes", 0)
    if prev_changes:
        pills.append(
            f'<span class="pill pill-info">Prev day: {prev_changes} '
            f'change(s), ₹{result.get("Prev Day Intraday Range ₹", 0.0):,.2f} '
            f'range</span>'
        )

    if not pills:
        return ""
    return '<div style="margin-top:10px;">' + "".join(pills) + "</div>"


def _hero_card(metal, result, projection_date):
    icon = "🟡" if metal == "Gold" else "⚪"
    curr = result["manual_curr_rate"]
    mv_rs = result["today_move_rs"]
    mv_pct = result["today_move_pct"]
    direction = result.get("direction", "Flat")
    magnitude = result.get("magnitude", "")

    prior_dir = result.get("Prior Day Direction", "None")
    prior_mag = result.get("Prior Day Magnitude", "")
    prior_move = result.get("Prior Day Move ₹", 0.0)
    cum_dir = result.get("Cumulative Direction", "Flat")
    cum_move = result.get("Cumulative Move ₹", 0.0)

    if mv_rs > FLAT_TOLERANCE:
        arrow_cls, arrow = "arrow-up", "↑"
    elif mv_rs < -FLAT_TOLERANCE:
        arrow_cls, arrow = "arrow-down", "↓"
    else:
        arrow_cls, arrow = "arrow-flat", "→"

    reliability = result.get("Reliability", "ROUGH")
    bucket_source = result.get("Bucket Source", "—")
    bucket_days = result.get("Bucket Days", 0)
    baseline = result.get("Baseline", {})
    previous_date = pd.Timestamp(result.get("prev_date", projection_date))
    previous_close = result.get("previous_calendar_day_rate",
                                result["prev_rate"])
    midnight_rate = result.get("rate_at_midnight", result["prev_rate"])
    previous_timeline = result.get("Previous Day Rate Timeline", [])

    timeline_lines = []
    prior_timeline_rate = None
    for index, event in enumerate(previous_timeline):
        event_time = str(event.get("time", "00:00"))
        for time_format in ("%H:%M:%S", "%H:%M"):
            try:
                event_time = datetime.strptime(
                    event_time, time_format
                ).strftime(
                    "%I:%M:%S %p" if time_format == "%H:%M:%S"
                    else "%I:%M %p"
                )
                break
            except ValueError:
                continue
        event_rate = float(event.get("rate", 0.0))
        event_delta = float(event.get("delta", 0.0))
        if index == 0 and abs(event_delta) <= FLAT_TOLERANCE:
            description = "Active"
        else:
            event_pct = (
                event_delta / prior_timeline_rate * 100.0
                if prior_timeline_rate and prior_timeline_rate > 0 else 0.0
            )
            event_arrow = "↑" if event_delta > 0 else "↓" if event_delta < 0 else "→"
            description = (
                f"Rate {event_arrow} ₹{abs(event_delta):,.2f} "
                f"({event_pct:+.2f}%)"
            )
        timeline_lines.append(
            f'<div>{html.escape(event_time)} &nbsp; '
            f'₹{event_rate:,.2f} &nbsp; {html.escape(description)}</div>'
        )
        prior_timeline_rate = event_rate

    timeline_title = f"{previous_date.strftime('%d-%m-%Y')} Rate Timeline"
    previous_timeline_html = (
        f'<div style="font-size:0.84rem; color:#374151; margin-top:10px; '
        f'padding:10px 12px; background:#fbfbfd; border:1px solid #e6e8ef; '
        f'border-radius:8px;"><b>{timeline_title}</b>'
        f'{"".join(timeline_lines) if timeline_lines else "<div>Rate events unavailable.</div>"}'
        f'<div style="margin-top:6px; color:#6b7280;">'
        f'Previous calendar-day close: <b>₹{previous_close:,.2f}</b> · '
        f'{pd.Timestamp(projection_date).strftime("%d-%m-%Y")} rate at '
        f'12:00 AM: <b>₹{midnight_rate:,.2f}</b></div></div>'
    )

    context_parts = []
    if prior_dir != "None":
        context_parts.append(
            f"Prior day: <b>{prior_dir}</b> ₹{prior_move:+,.2f}"
        )

    intraday_dir = result.get("Intraday Cumulative Direction")
    intraday_move = result.get("Intraday Cumulative Move ₹")
    if intraday_dir is not None and intraday_move is not None:
        context_parts.append(
            f"Intraday cumulative movement: <b>{intraday_dir}</b> "
            f"₹{abs(intraday_move):,.2f}"
        )
    elif cum_dir != "Flat" or abs(cum_move) > FLAT_TOLERANCE:
        context_parts.append(
            f"Cumulative: <b>{cum_dir}</b> ₹{cum_move:+,.2f}"
        )
    context_html = " · ".join(context_parts) if context_parts else ""

    momentum = result.get("Momentum Adjustment")
    momentum_html = ""
    if momentum:
        trend = momentum.get("Trend", "")
        factors = momentum.get("Carry Factor", {})
        factor_txt = " · ".join(
            f"{k}: ×{v:.2f}" for k, v in factors.items()
        ) if factors else ""
        parts = []
        if momentum.get("Reason"):
            parts.append(momentum["Reason"])
        if trend:
            parts.append(trend)
        if factor_txt:
            parts.append(f"Adjustments: {factor_txt}")
        if momentum.get("Trend Factor"):
            parts.append(f"Trend factor: ×{momentum['Trend Factor']:.2f}")
        momentum_html = (
            '<div style="font-size:0.8rem; color:#0d3a6b; '
            'background:#eef6ff; padding:8px 12px; border-radius:8px; '
            'border-left:3px solid #2b7cd3; margin-top:10px;">'
            '⚡ <b>Context adjustment applied:</b><br>'
            + "<br>".join(parts) +
            '</div>'
        )

    st.markdown(
        f'<div class="hero-card">'
        f'<div class="metal-title">{icon} {metal} — '
        f'behaviour-driven projection (context-aware)</div>'
        f'<div class="rate-line">'
        f'Current/latest rate: <b>₹{curr:,.2f}</b> · '
        f'Latest event: <span class="{arrow_cls}">{arrow} '
        f'₹{abs(mv_rs):,.2f} ({mv_pct:+.2f}%)</span>'
        f'</div>'
        f'{previous_timeline_html}'
        f'{_reliability_badge(reliability)}'
        f'{_intraday_pills(result)}'
        f'<div style="font-size:0.82rem; color:#6b7280; margin-top:10px;">'
        f'Direction: <b>{direction}</b> · '
        f'Magnitude: <b>{magnitude or "—"}</b> · '
        f'Intraday changes: <b>{result.get("Today Intraday Changes", 0)}</b><br>'
        f'{context_html}<br>'
        f'Multipliers from <b>{bucket_source}</b> bucket '
        f'({bucket_days} observation(s)).<br>'
        f'Baseline: '
        f'Enrol <b>{baseline.get("Enrolment", 0):,.1f}</b> · '
        f'Collection <b>₹{baseline.get("Collection", 0):,.0f}</b> · '
        f'Weight <b>{baseline.get("Total Weight", 0):,.2f} g</b>'
        f'</div>'
        f'{momentum_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _answer_metrics(proj, rng):
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f'<div class="metric-label">👥 New Enrolments</div>'
            f'<div class="metric-value">{proj["Enrolment"]:,}</div>'
            f'<div class="range-chip">'
            f'Range: {rng["Enrolment"][0]:,} – {rng["Enrolment"][2]:,}'
            f'</div>',
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f'<div class="metric-label">💰 Collection (₹)</div>'
            f'<div class="metric-value">₹{proj["Collection"]:,.0f}</div>'
            f'<div class="range-chip">'
            f'Range: ₹{rng["Collection"][0]:,.0f} – '
            f'₹{rng["Collection"][2]:,.0f}'
            f'</div>',
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f'<div class="metric-label">⚖️ Total Weight (g)</div>'
            f'<div class="metric-value">{proj["Total Weight"]:,.2f}</div>'
            f'<div class="range-chip">'
            f'Range: {rng["Total Weight"][0]:,.2f} – '
            f'{rng["Total Weight"][2]:,.2f}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    c4, c5, c6 = st.columns(3)

    with c4:
        st.markdown(
            f'<div class="metric-label">💵 Enrolment Amount</div>'
            f'<div class="metric-value" style="font-size:1.4rem;">'
            f'₹{proj["Enrolment Amount"]:,.0f}</div>'
            f'<div class="range-chip">'
            f'₹{rng["Enrolment Amount"][0]:,.0f} – '
            f'₹{rng["Enrolment Amount"][2]:,.0f}'
            f'</div>',
            unsafe_allow_html=True,
        )

    with c5:
        st.markdown(
            f'<div class="metric-label">🔁 Collections (count)</div>'
            f'<div class="metric-value" style="font-size:1.4rem;">'
            f'{proj["Collection Count"]:,}</div>'
            f'<div class="range-chip">'
            f'{rng["Collection Count"][0]:,} – '
            f'{rng["Collection Count"][2]:,}'
            f'</div>',
            unsafe_allow_html=True,
        )

    with c6:
        st.markdown(
            f'<div class="metric-label">🏦 Saved Weight (g)</div>'
            f'<div class="metric-value" style="font-size:1.4rem;">'
            f'{proj["Saved Weight"]:,.2f}</div>'
            f'<div class="range-chip">'
            f'{rng["Saved Weight"][0]:,.2f} – '
            f'{rng["Saved Weight"][2]:,.2f}'
            f'</div>',
            unsafe_allow_html=True,
        )


def _delta_html(delta, pct=None):
    cls = ("up" if delta > FLAT_TOLERANCE
           else "down" if delta < -FLAT_TOLERANCE else "flat")
    sign = "+" if delta > FLAT_TOLERANCE else "−" if delta < -FLAT_TOLERANCE else ""
    pct_txt = f" ({pct:+.2f}%)" if pct is not None else ""
    return (
        f'<span class="step-delta {cls}">{sign}₹{abs(delta):,.2f}'
        f'{pct_txt}</span>'
    )


def _step_card_html(step_num, step_info):
    kind = step_info.get("kind", "flat")
    time_str = step_info.get("time") or "—"
    rate = step_info.get("rate", 0.0)
    net = step_info.get("net_vs_midnight", 0.0)
    result = step_info.get("result") or {}

    if kind == "start":
        badge_cls, badge = "start", "Active at midnight"
        delta_html = _delta_html(net)
    elif kind == "up":
        badge_cls, badge = "up", "Rate up"
        delta_html = _delta_html(step_info["delta_from_prev"],
                                 step_info["delta_pct"])
    elif kind == "down":
        badge_cls, badge = "down", "Rate down"
        delta_html = _delta_html(step_info["delta_from_prev"],
                                 step_info["delta_pct"])
    else:
        badge_cls, badge = "flat", "Flat"
        delta_html = _delta_html(0.0, 0.0)

    card_cls = {
        "start": "step-first", "up": "step-up",
        "down": "step-down", "flat": "step-flat",
    }.get(kind, "")

    header = (
        f'<div class="step-header">'
        f'<div>'
        f'<span class="step-badge {badge_cls}">Step {step_num} · {badge}</span>'
        f'<span class="step-time" style="margin-left:10px;">{time_str}</span>'
        f'</div>'
        f'<div>'
        f'<span class="step-rate">₹{rate:,.2f}</span>'
        f'{delta_html}'
        f'</div>'
        f'</div>'
    )

    if result.get("status") != "OK":
        reason = {
            "NO_BEHAVIOR_MODEL": "Behaviour model unavailable.",
            "NO_USABLE_BUCKET": (
                "No behavioural bucket available for this rate move."
            ),
            "STEP_ERROR": "Something went wrong at this step.",
        }.get(result.get("status"), "No projection available.")

        return (
            f'<div class="step-card {card_cls}">'
            f'{header}'
            f'<div style="color:#7a5200; font-size:0.85rem; '
            f'background:#fff8e6; padding:8px 12px; border-radius:8px; '
            f'border-left:3px solid #e59b0c; margin-top:6px;">'
            f'⚠️ {reason}'
            f'</div>'
            f'</div>'
        )

    proj = result["Projection"]
    rng = result["Range"]
    reliability = result.get("Reliability", "ROUGH")
    bucket_source = result.get("Bucket Source", "—")
    bucket_days = result.get("Bucket Days", 0)

    metrics = [
        ("Enrolments", f'{proj["Enrolment"]:,}',
         f'{rng["Enrolment"][0]:,}–{rng["Enrolment"][2]:,}'),
        ("Enrol. Amt", f'₹{proj["Enrolment Amount"]:,.0f}',
         f'₹{rng["Enrolment Amount"][0]:,.0f}–'
         f'₹{rng["Enrolment Amount"][2]:,.0f}'),
        ("Collections", f'{proj["Collection Count"]:,}',
         f'{rng["Collection Count"][0]:,}–{rng["Collection Count"][2]:,}'),
        ("Coll. Amt", f'₹{proj["Collection"]:,.0f}',
         f'₹{rng["Collection"][0]:,.0f}–₹{rng["Collection"][2]:,.0f}'),
        ("Saved Wt", f'{proj["Saved Weight"]:,.2f} g',
         f'{rng["Saved Weight"][0]:,.2f}–{rng["Saved Weight"][2]:,.2f} g'),
        ("Reward Wt", f'{proj["Reward Weight"]:,.2f} g',
         f'{rng["Reward Weight"][0]:,.2f}–'
         f'{rng["Reward Weight"][2]:,.2f} g'),
        ("Total Wt", f'{proj["Total Weight"]:,.2f} g',
         f'{rng["Total Weight"][0]:,.2f}–{rng["Total Weight"][2]:,.2f} g'),
    ]

    metrics_html = "".join(
        f'<div class="step-metric">'
        f'<div class="lab">{lab}</div>'
        f'<div class="val">{val}</div>'
        f'<div class="rng">{rng_str}</div>'
        f'</div>'
        for lab, val, rng_str in metrics
    )

    prior_dir = result.get("Prior Day Direction", "")
    prior_move = result.get("Prior Day Move ₹", 0.0)
    cum_dir = result.get("Cumulative Direction", "")
    cum_move = result.get("Cumulative Move ₹", 0.0)

    context_short = ""
    if prior_dir and prior_dir != "None":
        context_short = (
            f" · Prior day: <b>{prior_dir}</b> ₹{prior_move:+,.0f}"
        )
    if cum_dir and cum_dir != "Flat":
        context_short += (
            f" · Cumulative: <b>{cum_dir}</b> ₹{cum_move:+,.0f}"
        )

    footer = (
        f'<div style="font-size:0.78rem; color:#6b7280; margin-top:8px;">'
        f'Move vs midnight: <b>₹{net:+,.2f}</b> · '
        f'Reliability: <b>{reliability}</b> · '
        f'Bucket: <b>{bucket_source}</b> ({bucket_days} days) · '
        f'Direction: <b>{result.get("direction", "—")}</b> '
        f'{result.get("magnitude", "")}'
        f'{context_short}'
        f'</div>'
    )

    return (
        f'<div class="step-card {card_cls}">'
        f'{header}'
        f'<div class="step-metrics">{metrics_html}</div>'
        f'{footer}'
        f'</div>'
    )


def render_step_wise_panel(step_results):
    if not step_results:
        return

    st.markdown("##### 📈 Projection at every rate change")
    st.caption(
        "Each card is driven by the **context-aware behaviour model** — "
        "what customers do on days with this kind of rate move, in the "
        "context of the prior day and multi-day trend."
    )

    for i, step_info in enumerate(step_results, start=1):
        st.markdown(_step_card_html(i, step_info), unsafe_allow_html=True)


def render_supporting_evidence(result):
    with st.expander("🔍 Supporting historical evidence", expanded=False):
        st.caption(
            "These are historical transaction windows with similar rate "
            "changes. Each row includes the active rate when those customers "
            "transacted."
        )
        supporting = result.get("Supporting Matches")
        if supporting is not None and not supporting.empty:
            st.dataframe(supporting, hide_index=True,
                         use_container_width=True)
        else:
            st.info("No close historical matches in the tolerance window.")


def render_behavior_transparency(result):
    with st.expander("🧬 How the projection was derived", expanded=False):

        baseline = result.get("Baseline", {})
        multipliers = result.get("Multipliers", {})
        direction = result.get("direction", "—")
        magnitude = result.get("magnitude", "")
        bucket_source = result.get("Bucket Source", "—")
        bucket_days = result.get("Bucket Days", 0)
        proj = result.get("Projection", {})
        behavior_proj = result.get("Behavior Projection", proj)

        prior_dir = result.get("Prior Day Direction", "None")
        prior_move = result.get("Prior Day Move ₹", 0.0)
        cum_dir = result.get("Cumulative Direction", "Flat")
        cum_move = result.get("Cumulative Move ₹", 0.0)

        intraday_dir = result.get("Intraday Cumulative Direction", "Flat")
        intraday_move = result.get("Intraday Cumulative Move ₹", 0.0)

        st.markdown("**Step 0 — Context of today's move**")
        st.caption(
            "Today's rate move is interpreted in the context of the previous "
            "day's move and the cumulative multi-day trend. Intraday movement "
            "is reported separately from any multi-day trend."
        )
        ctx_rows = [
            {"Field": "Today's direction", "Value": direction},
            {"Field": "Today's magnitude", "Value": magnitude or "—"},
            {"Field": "Previous calendar-day close", "Value":
                f"₹{result.get('previous_calendar_day_rate', 0.0):,.2f}"},
            {"Field": "Rate effective at 12:00 AM", "Value":
                f"₹{result.get('rate_at_midnight', 0.0):,.2f}"},
            {"Field": "Current active rate", "Value":
                f"₹{result.get('manual_curr_rate', 0.0):,.2f}"},
            {"Field": "Current rate event", "Value":
                f"₹{result.get('today_move_rs', 0.0):+,.2f}"},
            {"Field": "Intraday cumulative movement", "Value":
                f"{intraday_dir} ₹{abs(intraday_move):,.2f}"},
            {"Field": "Prior day direction", "Value": prior_dir},
            {"Field": "Prior day move ₹", "Value": f"₹{prior_move:+,.2f}"},
            {"Field": "Combined cumulative direction", "Value": cum_dir},
            {"Field": "Combined cumulative move ₹", "Value": f"₹{cum_move:+,.2f}"},
            {"Field": "Bucket used", "Value": f"{bucket_source} "
                                              f"({bucket_days} days)"},
            {"Field": "Model window used", "Value":
                f"{result.get('Model Days', '—')} days"},
            {"Field": "Spike decay used", "Value":
                f"{result.get('Spike Decay Used', '—')}"},
            {"Field": "Trend boost used", "Value":
                f"{result.get('Trend Boost Used', '—')}"},
        ]
        st.dataframe(pd.DataFrame(ctx_rows), hide_index=True,
                     use_container_width=True)

        full_day_ctx = result.get("Full-Day Context")
        if full_day_ctx:
            st.markdown("**Full-day intraday context**")
            st.dataframe(
                pd.DataFrame(
                    [{"Field": k, "Value": v} for k, v in full_day_ctx.items()]
                ),
                hide_index=True,
                use_container_width=True,
            )

        st.markdown("**Step 1 — Recent baseline (recency-weighted)**")
        st.caption(
            f"Recent days are weighted higher (half-life "
            f"{BEHAVIOR_RECENCY_HALFLIFE:.0f} days)."
        )
        base_rows = [
            {"Metric": m, "Baseline": round(baseline.get(m, 0.0), 2)}
            for m in ["Enrolment", "Collection", "Total Weight"]
        ]
        st.dataframe(pd.DataFrame(base_rows), hide_index=True,
                     use_container_width=True)

        st.markdown("**Step 2 — Multipliers (after context adjustment)**")
        mult_rows = [
            {"Metric": m,
             "Multiplier": round(multipliers.get(m, 1.0), 4),
             "Meaning": f"×{multipliers.get(m, 1.0):.2f} vs normal"}
            for m in ["Enrolment", "Collection", "Total Weight"]
        ]
        st.dataframe(pd.DataFrame(mult_rows), hide_index=True,
                     use_container_width=True)

        st.markdown("**Step 3 — Raw behaviour projection**")
        st.caption(
            "Independent baseline × multiplier outputs, before the dependent "
            "business-rule metrics are reconciled below."
        )
        calc_rows = []
        for m in ["Enrolment", "Enrolment Amount", "Collection Count",
                  "Collection", "Saved Weight", "Reward Weight", "Total Weight"]:
            b = baseline.get(m, 0.0)
            x = multipliers.get(m, 1.0)
            p = behavior_proj.get(m, 0.0)
            calc_rows.append({
                "Metric": m,
                "Baseline": round(b, 2),
                "× Multiplier": round(x, 4),
                "= Projection": round(p, 2),
            })
        st.dataframe(pd.DataFrame(calc_rows), hide_index=True,
                     use_container_width=True)

        st.markdown("**Step 4 — Business-rule coherence**")
        st.caption(
            "Saved Weight = (Enrolment Amount + Collection ₹) / active rate; "
            "Reward Weight follows its recent baseline ratio; "
            "Total Weight = Saved Weight + Reward Weight."
        )

        saved_weight = float(proj.get("Saved Weight", 0.0))
        reward_weight = float(proj.get("Reward Weight", 0.0))
        total_weight = float(proj.get("Total Weight", 0.0))
        enrolment = float(proj.get("Enrolment", 0.0))
        enrolment_amount = float(proj.get("Enrolment Amount", 0.0))
        collection = float(proj.get("Collection", 0.0))
        rate = float(result.get("manual_curr_rate", 0.0))
        average_ticket, reward_ratio = _coherence_parameters(baseline)

        implied_saved = (
            (enrolment_amount + collection) / rate if rate > 1e-9 else 0.0
        )
        expected_enrolment_amount = enrolment * average_ticket
        expected_reward_weight = saved_weight * reward_ratio
        checks = [
            ("Saved Weight = (Enrolment Amount + Collection ₹) / active rate",
             f"(₹{enrolment_amount:,.0f} + ₹{collection:,.0f}) ÷ ₹{rate:,.2f}",
             f"{implied_saved:.2f} g", f"{saved_weight:.2f} g",
             rate > 1e-9 and np.isclose(
                 saved_weight, implied_saved, rtol=1e-6, atol=0.01)),
            ("Reward Weight = Saved Weight × baseline reward ratio",
             f"{saved_weight:.2f} × {reward_ratio:.4f}",
             f"{expected_reward_weight:.2f} g", f"{reward_weight:.2f} g",
             np.isclose(reward_weight, expected_reward_weight,
                        rtol=1e-6, atol=0.01)),
            ("Total Weight = Saved Weight + Reward Weight",
             f"{saved_weight:.2f} + {reward_weight:.2f}",
             f"{saved_weight + reward_weight:.2f} g", f"{total_weight:.2f} g",
             np.isclose(total_weight, saved_weight + reward_weight,
                        rtol=1e-6, atol=0.01)),
            ("Enrolment Amount = Enrolment × average ticket",
             f"{enrolment:.0f} × ₹{average_ticket:,.2f}",
             f"₹{expected_enrolment_amount:,.2f}",
             f"₹{enrolment_amount:,.2f}",
             np.isclose(enrolment_amount, expected_enrolment_amount,
                        rtol=1e-6, atol=0.01)),
        ]
        check_rows = [
            {"Check": label, "Formula": formula, "Implied": implied,
             "Projected": projected, "OK": "OK" if passed else "CHECK"}
            for label, formula, implied, projected, passed in checks
        ]
        st.dataframe(pd.DataFrame(check_rows), hide_index=True,
                     use_container_width=True)

        if rate > 1e-9:
            st.caption(
                f"Rate ₹{rate:,.2f}/g · Enrolment metal "
                f"{enrolment_amount / rate:.2f} g · Collection metal "
                f"{collection / rate:.2f} g · Saved Weight "
                f"{saved_weight:.2f} g · Reward Weight {reward_weight:.2f} g · "
                f"Total Weight {total_weight:.2f} g"
            )

        momentum = result.get("Momentum Adjustment")
        if momentum:
            st.markdown("**Context adjustments applied**")
            for k, v in momentum.items():
                if isinstance(v, dict):
                    st.caption(f"**{k}**")
                    for kk, vv in v.items():
                        st.caption(f"  • {kk}: {vv}")
                else:
                    st.caption(f"• **{k}**: {v}")


# ─────────────────────────────────────────────────────────────
# LAYER ① UI PANEL
# ─────────────────────────────────────────────────────────────
def render_rate_window_reaction_panel(rate_windows, metal, recent_days):
    if rate_windows is None or rate_windows.empty:
        st.warning(f"No transaction-rate windows are available for {metal}.")
        return

    latest_day = pd.to_datetime(rate_windows["Date"]).max().normalize()
    window_start = latest_day - pd.Timedelta(days=int(recent_days) - 1)
    recent = rate_windows[
        pd.to_datetime(rate_windows["Date"]).dt.normalize() >= window_start
    ].copy()
    if recent.empty:
        st.info("No rate windows fall within the selected date range.")
        return

    changes = pd.to_numeric(recent["Rate Change ₹"], errors="coerce").fillna(0.0)
    transactions = int(
        recent["Enrolment"].sum() + recent["Collection Count"].sum()
    )
    up_events = int((changes > FLAT_TOLERANCE).sum())
    down_events = int((changes < -FLAT_TOLERANCE).sum())

    c1, c2, c3 = st.columns(3)
    c1.metric("Active-rate windows", f"{len(recent):,}")
    c2.metric("Rate-change events", f"{up_events + down_events:,}")
    c3.metric("Transactions assigned", f"{transactions:,}")

    st.caption(
        "Transactions are grouped by their recorded Metal Rate. A window "
        "starts at midnight or at the first transaction timestamp carrying "
        "a changed rate; displayed amounts and weights are observed totals."
    )

    show = recent[[
        "Date", "Window Start", "Window End", "Window Hours",
        "Active Rate", "Rate Change ₹", "Enrolment", "Enrolment Amount",
        "Collection Count", "Collection", "Saved Weight", "Reward Weight",
        "Total Weight",
    ]].copy()
    show["Date"] = pd.to_datetime(show["Date"]).dt.strftime("%d-%m-%Y")
    show["Window Start"] = pd.to_datetime(
        show["Window Start"]
    ).dt.strftime("%I:%M %p")
    show["Window End"] = pd.to_datetime(
        show["Window End"]
    ).dt.strftime("%I:%M %p")
    st.dataframe(
        show.style.format({
            "Window Hours": "{:,.2f}",
            "Active Rate": "₹{:,.2f}",
            "Rate Change ₹": "₹{:+,.2f}",
            "Enrolment": "{:,.0f}",
            "Enrolment Amount": "₹{:,.0f}",
            "Collection Count": "{:,.0f}",
            "Collection": "₹{:,.0f}",
            "Saved Weight": "{:,.3f} g",
            "Reward Weight": "{:,.3f} g",
            "Total Weight": "{:,.3f} g",
        }),
        hide_index=True,
        use_container_width=True,
    )
    st.download_button(
        "⬇️ Download rate-window transactions (CSV)",
        data=show.to_csv(index=False).encode("utf-8-sig"),
        mime="text/csv",
        file_name=f"{metal.lower()}_rate_windows_{recent_days}d.csv",
        key=f"dl_rate_windows_{metal}_{recent_days}",
    )


def render_customer_reaction_panel(analysis, metal, key_prefix,
                                  rate_windows=None):
    icon = "🟡" if metal == "Gold" else "⚪"

    if analysis is None or analysis.get("status") != "OK":
        st.warning(
            f"⚠️ Not enough recent customer data to analyse {metal} "
            f"behaviour."
        )
        return

    detail = analysis["detail"]
    comparison = analysis["comparison"]
    summary = analysis["summary"]
    magnitude = analysis.get("magnitude", pd.DataFrame())
    intraday = analysis.get("intraday", pd.DataFrame())
    recent_days = analysis["recent_days"]

    inc_days = int((detail["Rate Direction"] == "Increase").sum())
    dec_days = int((detail["Rate Direction"] == "Decrease").sum())
    flat_days = int((detail["Rate Direction"] == "Flat").sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📈 Rate-up days", inc_days)
    c2.metric("📉 Rate-down days", dec_days)
    c3.metric("➡️ Flat days", flat_days)
    c4.metric("📅 Window", f"{recent_days} days")

    if not comparison.empty:
        st.markdown("###### 📊 Customer behaviour — same-day vs next-day")

        rows = []
        for _, r in comparison.iterrows():
            rows.append({
                "Rate Move": r["Rate Direction"],
                "Days": int(r["Days"]),
                "Avg Move ₹": r["Avg Rate Change ₹"],
                "Enrol (same)": r.get("Enrolment Same Day", np.nan),
                "Enrol vs flat": r.get("Enrolment Same Day vs Flat %", np.nan),
                "Enrol (next)": r.get("Enrolment Next Day", np.nan),
                "Enrol next vs flat":
                    r.get("Enrolment Next Day vs Flat %", np.nan),
                "Collection (same)":
                    r.get("Collection Same Day", np.nan),
                "Collection vs flat":
                    r.get("Collection Same Day vs Flat %", np.nan),
                "Weight (same)":
                    r.get("Total Weight Same Day", np.nan),
                "Weight vs flat":
                    r.get("Total Weight Same Day vs Flat %", np.nan),
            })

        display = pd.DataFrame(rows)

        if not summary.empty:
            flat_row = summary[summary["Rate Direction"] == "Flat"]
            if not flat_row.empty:
                fr = flat_row.iloc[0]
                display = pd.concat([
                    display,
                    pd.DataFrame([{
                        "Rate Move": "Flat (baseline)",
                        "Days": int(fr["Days"]),
                        "Avg Move ₹": 0.0,
                        "Enrol (same)": fr.get("Enrolment Same Day", np.nan),
                        "Enrol vs flat": 0.0,
                        "Enrol (next)": fr.get("Enrolment Next Day", np.nan),
                        "Enrol next vs flat": 0.0,
                        "Collection (same)":
                            fr.get("Collection Same Day", np.nan),
                        "Collection vs flat": 0.0,
                        "Weight (same)":
                            fr.get("Total Weight Same Day", np.nan),
                        "Weight vs flat": 0.0,
                    }])
                ], ignore_index=True)

        st.dataframe(
            display.style.format({
                "Avg Move ₹": "₹{:,.2f}",
                "Enrol (same)": "{:,.1f}",
                "Enrol vs flat": "{:+.1f}%",
                "Enrol (next)": "{:,.1f}",
                "Enrol next vs flat": "{:+.1f}%",
                "Collection (same)": "₹{:,.0f}",
                "Collection vs flat": "{:+.1f}%",
                "Weight (same)": "{:,.2f}",
                "Weight vs flat": "{:+.1f}%",
            }, na_rep="—"),
            hide_index=True,
            use_container_width=True,
        )

    if not magnitude.empty:
        st.markdown("###### 🎯 Sensitivity by magnitude of rate move")
        st.caption(
            "How customer behaviour changes as the **size** of the "
            "rate move grows."
        )
        m = magnitude.copy().rename(columns={
            "Rate Direction": "Direction",
            "Avg Rate Change ₹": "Avg Move ₹",
            "Enrolment": "Enrol",
            "Enrolment vs Flat %": "Enrol vs flat",
            "Collection": "Collection ₹",
            "Collection vs Flat %": "Coll vs flat",
            "Total Weight": "Weight g",
            "Total Weight vs Flat %": "Weight vs flat",
        })
        st.dataframe(
            m.style.format({
                "Avg Move ₹": "₹{:,.2f}",
                "Enrol": "{:,.1f}",
                "Enrol vs flat": "{:+.1f}%",
                "Collection ₹": "₹{:,.0f}",
                "Coll vs flat": "{:+.1f}%",
                "Weight g": "{:,.2f}",
                "Weight vs flat": "{:+.1f}%",
            }, na_rep="—"),
            hide_index=True,
            use_container_width=True,
        )

    if not intraday.empty:
        with st.expander("🔀 Behaviour by intraday change count",
                         expanded=False):
            st.dataframe(
                intraday.style.format({
                    "Avg Enrolment": "{:,.1f}",
                    "Avg Collection ₹": "₹{:,.0f}",
                    "Avg Total Weight g": "{:,.2f}",
                }),
                hide_index=True,
                use_container_width=True,
            )

    if rate_windows is not None and not rate_windows.empty:
        with st.expander("💹 Transactions by active-rate window",
                         expanded=False):
            latest_day = pd.to_datetime(rate_windows["Date"]).max().normalize()
            window_start = latest_day - pd.Timedelta(
                days=int(recent_days) - 1
            )
            show = rate_windows[
                pd.to_datetime(rate_windows["Date"]).dt.normalize()
                >= window_start
            ].copy()
            show["Date"] = pd.to_datetime(show["Date"]).dt.strftime(
                "%d-%m-%Y"
            )
            show["Window Start"] = pd.to_datetime(
                show["Window Start"]
            ).map(lambda value: value.strftime(
                "%I:%M:%S %p" if value.second else "%I:%M %p"
            ))
            show["Window End"] = pd.to_datetime(
                show["Window End"]
            ).map(lambda value: value.strftime(
                "%I:%M:%S %p" if value.second else "%I:%M %p"
            ))
            show = show[[
                "Date", "Window Start", "Window End", "Window Hours",
                "Active Rate", "Rate Change ₹", "Enrolment",
                "Enrolment Amount", "Collection Count", "Collection",
                "Saved Weight", "Reward Weight", "Total Weight",
            ]]
            st.dataframe(
                show.style.format({
                    "Window Hours": "{:,.2f}",
                    "Active Rate": "₹{:,.2f}",
                    "Rate Change ₹": "₹{:+,.2f}",
                    "Enrolment": "{:,.0f}",
                    "Enrolment Amount": "₹{:,.0f}",
                    "Collection Count": "{:,.0f}",
                    "Collection": "₹{:,.0f}",
                    "Saved Weight": "{:,.3f} g",
                    "Reward Weight": "{:,.3f} g",
                    "Total Weight": "{:,.3f} g",
                }),
                hide_index=True,
                use_container_width=True,
            )

    interp = _customer_reaction_interpretation(analysis, metal)
    st.markdown(
        f'<div class="callout callout-info">'
        f'🔎 <b>What customer behaviour says:</b><br>{interp}'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("###### 💡 Key observations")
    for line in analysis["insights"]:
        st.markdown(
            f'<div class="behavior-insight">{line}</div>',
            unsafe_allow_html=True,
        )

    with st.expander(f"📋 Daily summary — last {recent_days} days",
                     expanded=False):
        show = detail.copy()
        show["Date"] = pd.to_datetime(show["Date"]).dt.strftime("%d-%m-%Y")
        st.dataframe(show, hide_index=True, use_container_width=True)
        st.download_button(
            "⬇️ Download behaviour CSV",
            data=show.to_csv(index=False).encode("utf-8-sig"),
            mime="text/csv",
            file_name=f"{metal.lower()}_behavior_{recent_days}d.csv",
            key=f"dl_behavior_{key_prefix}_{metal}",
        )


# ─────────────────────────────────────────────────────────────
# RATE TIMELINE INPUT  (persistent, date-wise auto-save)
# ─────────────────────────────────────────────────────────────
def _render_rate_timeline_input(metal, prev_rate, prev_date,
                                projection_date, key_prefix):
    icon = "🟡" if metal == "Gold" else "⚪"
    st.markdown(f"**{icon} {metal}**")

    has_saved = has_saved_timeline(metal, projection_date)
    if has_saved:
        st.caption(
            f"💾 Loaded saved rates for **{projection_date.strftime('%d-%m-%Y')}**. "
            f"Previous calendar-day close: **₹{prev_rate:,.2f}** "
            f"({prev_date.strftime('%d-%m-%Y')}). Any change you make is "
            f"auto-saved for this date."
        )
    else:
        st.caption(
            f"🆕 No saved rates yet for **{projection_date.strftime('%d-%m-%Y')}**. "
            f"Starting from previous calendar-day close "
            f"**₹{prev_rate:,.2f}** ({prev_date.strftime('%d-%m-%Y')}). "
            f"Any change you make is auto-saved."
        )

    state_key = (
        f"timeline_{key_prefix}_{metal.lower()}_"
        f"{projection_date.strftime('%Y%m%d')}"
    )
    id_key = f"{state_key}_nextid"

    if state_key not in st.session_state:
        saved = load_saved_timeline(metal, projection_date)
        if saved:
            st.session_state[state_key] = saved
            st.session_state[id_key] = max(r["id"] for r in saved) + 1
        else:
            st.session_state[state_key] = [
                {"id": 0, "time": "12:00 am", "rate": float(prev_rate)},
            ]
            st.session_state[id_key] = 1

    rows = st.session_state[state_key]

    hc1, hc2, hc3, hc4 = st.columns([1.2, 1.6, 0.8, 0.6])
    for c, label in zip([hc1, hc2, hc3, hc4],
                        ["Time", "Rate (₹)", "Change", "&nbsp;"]):
        with c:
            st.markdown(
                f'<div style="font-size:0.72rem; color:#6b7280; '
                f'text-transform:uppercase; font-weight:700;">'
                f'{label}</div>',
                unsafe_allow_html=True,
            )

    updated_rows = []
    remove_id = None
    prev_val = None
    for i, row in enumerate(rows):
        rid = row["id"]
        c1, c2, c3, c4 = st.columns([1.2, 1.6, 0.8, 0.6])

        with c1:
            t_str = st.text_input(
                f"time_{metal}_{rid}",
                value=row.get("time", ""),
                key=f"{state_key}_time_{rid}",
                label_visibility="collapsed",
                placeholder="e.g. 10:36 am",
            )

        with c2:
            rate_val = st.number_input(
                f"rate_{metal}_{rid}",
                min_value=0.0,
                value=float(row.get("rate", prev_rate)),
                step=1.0,
                key=f"{state_key}_rate_{rid}",
                label_visibility="collapsed",
                format="%.2f",
            )

        with c3:
            if prev_val is None:
                delta_html = (
                    '<div style="padding-top:8px; font-size:0.82rem; '
                    'color:#6b7280; font-weight:600;">Start</div>'
                )
            else:
                d = float(rate_val) - prev_val
                color = "#0d5223" if d > 0 else "#7a1d15" if d < 0 else "#6b7280"
                sign = "+" if d > 0 else ""
                delta_html = (
                    f'<div style="padding-top:8px; font-size:0.85rem; '
                    f'font-weight:700; color:{color};">'
                    f'{sign}{d:,.2f}</div>'
                )
            st.markdown(delta_html, unsafe_allow_html=True)

        with c4:
            if i > 0:
                if st.button("✕", key=f"{state_key}_rm_{rid}"):
                    remove_id = rid

        updated_rows.append({"id": rid, "time": t_str, "rate": float(rate_val)})
        prev_val = float(rate_val)

    if remove_id is not None:
        st.session_state[state_key] = [
            r for r in updated_rows if r["id"] != remove_id
        ]
        save_timeline(metal, projection_date,
                      st.session_state[state_key])
        st.rerun()

    st.session_state[state_key] = updated_rows
    save_timeline(metal, projection_date, updated_rows)

    bc1, bc2 = st.columns([1, 1])
    with bc1:
        if len(updated_rows) < MAX_DAILY_CHANGES:
            if st.button("➕ Add rate change", key=f"{state_key}_add"):
                last_t = updated_rows[-1]["time"] if updated_rows else "12:00 am"
                try:
                    hh, mm = str(last_t).replace(" am", "").replace(
                        " pm", "").split(":")[:2]
                    next_t = f"{(int(hh) + 1) % 24:02d}:{mm}"
                except Exception:
                    next_t = "10:36 am"
                new_id = int(st.session_state.get(id_key, len(updated_rows)))
                st.session_state[id_key] = new_id + 1
                updated_rows.append({
                    "id": new_id,
                    "time": next_t,
                    "rate": float(updated_rows[-1]["rate"])
                    if updated_rows else float(prev_rate),
                })
                st.session_state[state_key] = updated_rows
                save_timeline(metal, projection_date, updated_rows)
                st.rerun()
        else:
            st.caption(f"Maximum {MAX_DAILY_CHANGES} rows reached.")

    with bc2:
        if st.button("↺ Reset to midnight", key=f"{state_key}_reset"):
            new_id = int(st.session_state.get(id_key, 1))
            st.session_state[id_key] = new_id + 1
            st.session_state[state_key] = [
                {"id": new_id, "time": "12:00 am", "rate": float(prev_rate)}
            ]
            save_timeline(metal, projection_date,
                          st.session_state[state_key])
            st.rerun()

    timeline = build_today_timeline(updated_rows)

    preview_html = _render_timeline_preview(timeline)
    if preview_html:
        st.markdown(preview_html, unsafe_allow_html=True)

    for e in timeline.get("errors", []):
        st.warning(f"⚠️ {e}")

    return timeline, updated_rows


# ─────────────────────────────────────────────────────────────
# MAIN SCREEN
# ─────────────────────────────────────────────────────────────
def render_today_screen(df, cfg):
    projection_date = cfg["projection_date"]
    baseline_days = cfg.get("baseline_days", BEHAVIOR_BASELINE_DAYS)
    spike_decay = cfg.get("spike_decay", BEHAVIOR_SPIKE_DECAY)
    trend_boost = cfg.get("trend_boost", BEHAVIOR_TREND_BOOST)

    st.markdown(
        '<div class="section-title"><span class="accent"></span><span class="text">'
        f'Today\'s Projection — {projection_date.strftime("%d %B %Y")}</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "**Context-aware behaviour projection.** The model learns how "
        "customers respond to rate moves — including whether it's a "
        "continuation of yesterday's move and the multi-day trend — and "
        "builds today's expectation from that learning. Rates you enter "
        "below are **auto-saved date-wise** and reloaded automatically."
    )

    historical = df[df["Date"].dt.normalize() < projection_date].copy()
    if historical.empty:
        st.error("❌ No historical data before today's date.")
        return

    last_hist = historical["Date"].max()
    st.markdown(
        f'<div class="callout callout-info">'
        f'🔒 Using your full history through '
        f'<b>{last_hist.strftime("%d-%m-%Y %H:%M:%S")}</b> '
        f'({len(historical):,} rows). '
        f'Behaviour model window: <b>controlled by Section 2 selector</b>. '
        f'Baseline: <b>last {baseline_days} days</b> (recency-weighted). '
        f'Saved rates persist on disk in <code>rate_timelines.json</code>.'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ─────────────────────────────────────────────────────────
    # SECTION 1
    # ─────────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-title"><span class="accent"></span><span class="text">'
        '1️⃣ Enter today\'s rate changes'
        '<span class="layer-badge l2">Trigger · auto-saved</span>'
        '</span></div>',
        unsafe_allow_html=True,
    )

    metals = ["Gold", "Silver"]
    timelines = {}
    dailies = {}
    rate_windows_by_metal = {}

    selected_metal = st.radio(
        "Select metal",
        options=metals,
        format_func=lambda m: f"{'🟡' if m == 'Gold' else '⚪'} {m}",
        horizontal=True,
        key="today_selected_metal",
    )

    for metal in metals:
        daily = build_daily_rate_series(historical, metal)
        if daily.empty:
            continue
        prev_rate = float(daily["Day Close Rate"].iloc[-1])
        prev_date = daily["Date"].iloc[-1]
        rate_windows_by_metal[metal] = (
            build_rate_window_customer_series(historical, metal, daily)
        )
        if metal == selected_metal:
            timeline, _raw = _render_rate_timeline_input(
                metal, prev_rate, prev_date,
                projection_date=projection_date,
                key_prefix="today",
            )
            timelines[metal] = timeline
            dailies[metal] = daily

    valid_metals = [m for m in metals
                    if m in timelines and timelines[m].get("valid")]

    # ─────────────────────────────────────────────────────────
    # SECTION 2
    # ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        '<div class="section-title"><span class="accent"></span><span class="text">'
        '2️⃣ 🧠 How customers reacted recently'
        '<span class="layer-badge l1">Layer ① · drives projection window</span>'
        '</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "This window is used both for the reaction diagnostics below **and** "
        "as the behaviour-model window that drives Section 3's projection. "
        "Changing it will change the projection."
    )

    rc1, _rc2 = st.columns([2, 3])
    with rc1:
        default_reaction = (
            BEHAVIOR_MODEL_DAYS
            if BEHAVIOR_MODEL_DAYS in CUSTOMER_REACTION_DAYS_OPTIONS
            else 30
        )
        reaction_window = st.selectbox(
            "Analysis + model window (days)",
            options=CUSTOMER_REACTION_DAYS_OPTIONS,
            index=CUSTOMER_REACTION_DAYS_OPTIONS.index(default_reaction),
            format_func=lambda d: f"Last {d} days",
            key="reaction_window_select",
        )

    model_days = int(reaction_window)

    render_rate_window_reaction_panel(
        rate_windows_by_metal.get(selected_metal),
        selected_metal,
        reaction_window,
    )

    # ─────────────────────────────────────────────────────────
    # SECTION 3
    # ─────────────────────────────────────────────────────────
    if not valid_metals:
        st.warning(
            "⚠️ Enter at least one rate for Gold or Silver to see the "
            "projection."
        )
        return

    st.markdown("---")
    st.markdown(
        '<div class="section-title"><span class="accent"></span><span class="text">'
        '3️⃣ 📈 Behaviour-driven projection'
        '<span class="layer-badge l3">Context-aware</span>'
        '</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        f"Model window: **last {model_days} days** (from Section 2). "
        f"Baseline window: **last {baseline_days} days**. "
        f"Each step card shows an alternative full-day-equivalent snapshot "
        f"at that moment in the day. The **full-day projection** below is a "
        f"separate, single integrated prediction driven by the complete "
        f"intraday rate sequence."
    )

    projection_metals = [m for m in valid_metals if m == selected_metal]

    for metal in projection_metals:
        timeline = timelines[metal]
        steps = timeline.get("steps", [])
        if not steps:
            st.info("Add at least one rate change to see the projection.")
            continue

        daily = dailies[metal]
        daily_cust = build_daily_customer_series(historical, metal)
        features = build_pattern_features(daily, daily_cust)

        if features.empty or len(features) < 10:
            st.warning(
                f"Not enough rate history for {metal} to run the "
                f"behaviour model (need ≥ 10 days)."
            )
            continue

        with st.spinner(
            "Learning context-aware behaviour and projecting every step..."
        ):
            step_results = project_step_wise_behavior(
                features=features,
                daily_cust=daily_cust,
                daily=daily,
                steps=steps,
                projection_date=projection_date,
                metal=metal,
                model_days=model_days,
                baseline_days=baseline_days,
                spike_decay=spike_decay,
                trend_boost=trend_boost,
                rate_windows=rate_windows_by_metal.get(metal),
            )

        render_step_wise_panel(step_results)

        st.markdown("---")
        st.markdown("##### 🎯 Current rate — full-day projection")

        with st.spinner(
            "Building integrated full-day projection from the "
            "complete intraday rate sequence..."
        ):
            full_day_result = project_full_day_behavior(
                features=features,
                daily_cust=daily_cust,
                daily=daily,
                timeline=timeline,
                projection_date=projection_date,
                metal=metal,
                model_days=model_days,
                baseline_days=baseline_days,
                spike_decay=spike_decay,
                trend_boost=trend_boost,
                rate_windows=rate_windows_by_metal.get(metal),
            )

        if full_day_result.get("status") != "OK":
            st.info(
                "No full-day behaviour-driven projection available "
                "for the complete intraday sequence. Try adjusting "
                "the rate changes or widening the behaviour model "
                "window."
            )
        else:
            _hero_card(metal, full_day_result, projection_date)
            st.markdown("")
            _answer_metrics(full_day_result["Projection"],
                            full_day_result["Range"])
            st.markdown("")
            render_behavior_transparency(full_day_result)
            st.markdown("")
            render_supporting_evidence(full_day_result)

        with st.expander("🧪 Diagnostics — all layers",
                         expanded=False):
            if full_day_result.get("status") == "OK":
                st.markdown("**Full-day context**")
                st.json(full_day_result.get("Full-Day Context", {}))

            diag = {
                "Method": "BEHAVIOR_DRIVEN_CONTEXT_AWARE",
                "Section 2 window (days)": model_days,
                "Baseline window (days)": baseline_days,
                "Context lookback (days)": BEHAVIOR_CONTEXT_LOOKBACK,
                "Recency half-life (days)": BEHAVIOR_RECENCY_HALFLIFE,
                "Spike threshold": BEHAVIOR_SPIKE_THRESHOLD,
                "Spike decay (used)": spike_decay,
                "Trend boost (used)": trend_boost,
                "Days of rate history": len(daily),
                "Today's rate path": timeline["path"],
                "Today's net move ₹": timeline["net_move"],
                "Today's intraday changes": timeline["changes"],
                "Steps projected": len(step_results),
            }
            st.json(diag)

            steps_df = pd.DataFrame([
                {
                    "Step": i + 1,
                    "Time": s.get("time"),
                    "Rate": s.get("rate"),
                    "Δ from prev ₹": s.get("delta_from_prev"),
                    "Move vs midnight ₹": s.get("net_vs_midnight"),
                    "Status": s.get("status"),
                    "Bucket": (s.get("result") or {}).get("Bucket Source"),
                    "Bucket days":
                        (s.get("result") or {}).get("Bucket Days"),
                    "Prior Day":
                        (s.get("result") or {})
                        .get("Prior Day Direction"),
                    "Cumulative":
                        (s.get("result") or {})
                        .get("Cumulative Direction"),
                    "Enrolments":
                        (s.get("result") or {})
                        .get("Projection", {}).get("Enrolment"),
                    "Collection":
                        (s.get("result") or {})
                        .get("Projection", {}).get("Collection"),
                    "Total Weight":
                        (s.get("result") or {})
                        .get("Projection", {}).get("Total Weight"),
                    "Reliability":
                        (s.get("result") or {}).get("Reliability"),
                }
                for i, s in enumerate(step_results)
            ])
            st.dataframe(steps_df, hide_index=True,
                         use_container_width=True)

        export_rows = []
        for i, s in enumerate(step_results, start=1):
            r = s.get("result") or {}
            proj = r.get("Projection", {}) or {}
            rng = r.get("Range", {}) or {}
            export_rows.append({
                "Metal": metal,
                "Projection Date":
                    projection_date.strftime("%Y-%m-%d"),
                "Step": i,
                "Time": s.get("time"),
                "Rate": s.get("rate"),
                "Delta ₹": s.get("delta_from_prev"),
                "Delta %": s.get("delta_pct"),
                "Move vs Midnight ₹": s.get("net_vs_midnight"),
                "Status": s.get("status"),
                "Direction": r.get("direction"),
                "Magnitude": r.get("magnitude"),
                "Prior Day Direction": r.get("Prior Day Direction"),
                "Prior Day Move ₹": r.get("Prior Day Move ₹"),
                "Cumulative Direction": r.get("Cumulative Direction"),
                "Cumulative Move ₹": r.get("Cumulative Move ₹"),
                "Bucket Source": r.get("Bucket Source"),
                "Bucket Days": r.get("Bucket Days"),
                "Expected Enrolments": proj.get("Enrolment"),
                "Range Enrolments Low":
                    (rng.get("Enrolment") or (None, None, None))[0],
                "Range Enrolments High":
                    (rng.get("Enrolment") or (None, None, None))[2],
                "Expected Enrolment Amount":
                    proj.get("Enrolment Amount"),
                "Expected Collection Count":
                    proj.get("Collection Count"),
                "Expected Collection": proj.get("Collection"),
                "Range Collection Low":
                    (rng.get("Collection") or (None, None, None))[0],
                "Range Collection High":
                    (rng.get("Collection") or (None, None, None))[2],
                "Expected Saved Weight": proj.get("Saved Weight"),
                "Expected Reward Weight": proj.get("Reward Weight"),
                "Expected Total Weight": proj.get("Total Weight"),
                "Reliability": r.get("Reliability"),
                "Supporting Matches": r.get("N_Matches"),
                "Method": r.get("method"),
            })

        if full_day_result.get("status") == "OK":
            fdr = full_day_result
            fproj = fdr.get("Projection", {})
            frng = fdr.get("Range", {})
            export_rows.append({
                "Metal": metal,
                "Projection Date":
                    projection_date.strftime("%Y-%m-%d"),
                "Step": "FULL_DAY",
                "Time": "Full calendar day",
                "Rate": fdr.get("manual_curr_rate"),
                "Delta ₹": fdr.get("Intraday Cumulative Move ₹"),
                "Delta %": fdr.get("today_move_pct"),
                "Move vs Midnight ₹":
                    fdr.get("Intraday Cumulative Move ₹"),
                "Status": fdr.get("status"),
                "Direction": fdr.get("direction"),
                "Magnitude": fdr.get("magnitude"),
                "Prior Day Direction": fdr.get("Prior Day Direction"),
                "Prior Day Move ₹": fdr.get("Prior Day Move ₹"),
                "Cumulative Direction": fdr.get("Cumulative Direction"),
                "Cumulative Move ₹": fdr.get("Cumulative Move ₹"),
                "Bucket Source": fdr.get("Bucket Source"),
                "Bucket Days": fdr.get("Bucket Days"),
                "Expected Enrolments": fproj.get("Enrolment"),
                "Range Enrolments Low":
                    (frng.get("Enrolment") or (None, None, None))[0],
                "Range Enrolments High":
                    (frng.get("Enrolment") or (None, None, None))[2],
                "Expected Enrolment Amount":
                    fproj.get("Enrolment Amount"),
                "Expected Collection Count":
                    fproj.get("Collection Count"),
                "Expected Collection": fproj.get("Collection"),
                "Range Collection Low":
                    (frng.get("Collection") or (None, None, None))[0],
                "Range Collection High":
                    (frng.get("Collection") or (None, None, None))[2],
                "Expected Saved Weight": fproj.get("Saved Weight"),
                "Expected Reward Weight": fproj.get("Reward Weight"),
                "Expected Total Weight": fproj.get("Total Weight"),
                "Reliability": fdr.get("Reliability"),
                "Supporting Matches": fdr.get("N_Matches"),
                "Method": fdr.get("method"),
            })

        csv = pd.DataFrame(export_rows).to_csv(
            index=False
        ).encode("utf-8-sig")

        pdf_bytes = None
        if full_day_result.get("status") == "OK":
            try:
                pdf_bytes = _build_projection_pdf(
                    metal=metal,
                    projection_date=projection_date,
                    full_day_result=full_day_result,
                    step_results=step_results,
                    model_days=model_days,
                    baseline_days=baseline_days,
                )
            except Exception as exc:
                logger.exception("PDF build failed")
                st.warning(
                    f"⚠️ Could not build PDF: {type(exc).__name__}: {exc}"
                )

        dl1, dl2 = st.columns([1, 1])
        with dl1:
            st.download_button(
                "⬇️ Download step-wise CSV",
                data=csv,
                mime="text/csv",
                file_name=(
                    f"{metal.lower()}_context_behavior_stepwise_"
                    f"{projection_date.date()}.csv"
                ),
                key=f"csv_stepwise_{metal}",
                use_container_width=True,
            )
        with dl2:
            if pdf_bytes is not None:
                st.download_button(
                    "📄 Download full projection PDF",
                    data=pdf_bytes,
                    mime="application/pdf",
                    file_name=(
                        f"{metal.lower()}_projection_"
                        f"{projection_date.date()}.pdf"
                    ),
                    key=f"pdf_full_{metal}",
                    use_container_width=True,
                )

    # ─────────────────────────────────────────────────────────
    # SECTION 4
    # ─────────────────────────────────────────────────────────
    _render_backtest_panel(
        df=df,
        metal=selected_metal,
        daily_rate_all=build_daily_rate_series(df, selected_metal),
        cfg={**cfg, "_reaction_window": model_days},
    )


def main():
    cfg = render_sidebar()

    if "error" in cfg:
        st.error(f"❌ Missing required columns: {cfg['error']}")
        st.write("Columns found:", cfg["df"].columns.tolist())
        st.stop()

    df = cfg.get("df")
    if df is None or df.empty:
        st.markdown(
            f'<div class="callout callout-info">'
            f'📂 No transaction data is available.<br><br>'
            f'The app checks this local default path first:<br>'
            f'<code>{DEFAULT_DATA_PATH}</code><br><br>'
            f'If the local file and GitHub copy are unavailable, use the '
            f'sidebar upload to provide a file.'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.stop()

    if cfg["projection_date"] is None:
        st.error("Please pick today's date.")
        st.stop()

    try:
        render_today_screen(df, cfg)
    except Exception as exc:
        _crash_banner("Projection", exc)

    st.divider()

    with st.expander("🔍 View cleaned data", expanded=False):
        st.caption(f"{len(df):,} rows · {len(df.columns)} columns")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Download cleaned data (CSV)",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            mime="text/csv",
            file_name="cleaned_transactions.csv",
            key="raw_dl",
        )


def _crash_banner(name, exc):
    logger.exception("%s crashed", name)
    st.markdown(
        f'<div class="callout callout-warn">'
        f'⚠️ <b>{name}</b> hit an error. Please try again or re-upload.'
        f'</div>',
        unsafe_allow_html=True,
    )
    with st.expander("🛠️ Technical details", expanded=False):
        st.code("".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        ))


if __name__ == "__main__":
    main()