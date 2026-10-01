# 🥇 Today's Projection

Context-aware customer-behaviour model for a gold/silver savings business.
Learns how customers respond to intraday rate movements and projects
the current day's expected activity from the full intraday rate path.

## What it does

- **Layer ① — Customer reaction diagnostics**: how enrolment, collection,
  and metal weight respond to rate-up / rate-down / flat days.
- **Layer ② — Context-aware behaviour model**: bucketises every historical
  rate-change day by direction, magnitude, intraday volatility, prior-day
  move, and multi-day trend. Multipliers are applied to a recency-weighted
  baseline to project today.
- **Layer ③ — Full-day integrated projection**: a single prediction for
  the whole calendar day, driven by the complete intraday rate sequence.
- **Backtest panel**: replays the same engine on any past date and shows
  projection vs actuals with MAPE and bias.
- **PDF + CSV export** of the projection and step-wise breakdown.

## Requirements

- Python 3.9 – 3.12
- See `requirements.txt`

## Install

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Data source

The app prefers the local `transaction_data.xlsx` at the configured default
path. If that file is not available (for example, in a hosted deployment), it
downloads the workbook from the repository's `main` branch and caches the
download for one hour. A file uploaded through the sidebar takes precedence.