# Bloomberg GTC 2026 — NTU

Team research scripts and the WLS constituent identifier workbook for the 2026 Bloomberg Global Trading Challenge.

See [strategy review and Bloomberg export priorities](STRATEGY_REVIEW.md) for the research-process critique and weekend plan. It is a proposed workflow, not a tested trading model.

## Open the stock list

[Download the Excel workbook](wls_export/WLS_Stocks_2026-10-09.xlsx).

The 9 October 2026 snapshot contains **10,419 constituent listings**, reconciled against Bloomberg's member count. The main sheet contains official local exchange tickers, company names, exchange names and MIC codes. Bloomberg identifiers are kept separately. Tickers are stored as text to preserve leading zeros.

Two rows require review: Mi Material Holding has no local exchange symbol in Bloomberg's response; Senior PLC has no exchange name or MIC in that response. Neither was guessed. Different listings and share classes remain separate. This is not a prevalidated Capital IQ import: match by exchange, ticker and company name, and verify ambiguous results.

## Setup

Opening the workbook does not require Python or Bloomberg. Running the Bloomberg scripts requires Windows, an entitled Bloomberg Terminal session on that computer, and Python. The original environment used Python 3.14.8 (64-bit).

Run in PowerShell from this project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install --index-url=https://blpapi.bloomberg.com/repository/releases/python/simple/ blpapi==3.26.9.1
.\.venv\Scripts\python.exe .\check_bloomberg.py
```

The connection check opens a session and the reference-data service; it requests no securities or market data. Python BLPAPI bundles its native library. You do not need a C++ compiler to use it.

## Scripts

| File | Purpose |
|---|---|
| `check_bloomberg.py` | Connection-only Python API test |
| `check_bloomberg.cpp` | Equivalent C++ example; requires a separately installed compiler and Bloomberg C++ SDK |
| `bloomberg_extract.py` | Bounded API request helper, cache, and field/member diagnostics |
| `collect_wls_members.py` | Retrieve complete paginated WLS membership, discard weights, and reconcile the member count |
| `build_wls_workbook.py` | Retrieve four identifying fields, build the workbook, and validate it |

## Reproduce the export

**This makes Bloomberg data requests and can consume account allowances.** Download the existing workbook unless you need to reproduce the snapshot. Limits depend on the account; this project does not measure remaining entitlement or quota.

```powershell
.\.venv\Scripts\python.exe -X utf8 .\collect_wls_members.py
.\.venv\Scripts\python.exe -X utf8 .\build_wls_workbook.py
```

The paginated membership field also returns index weights; the original user approved this route because identifier-only membership fields were capped. Weights are discarded. Security requests are limited to `ID_EXCH_SYMBOL`, `LONG_COMP_NAME`, `PRIMARY_EXCHANGE_NAME` and `ID_MIC_PRIM_EXCH`. No security prices, fundamentals or history are requested.

Requests are cached locally. **The current scripts are for the dated 9 October snapshot, not a refresh service.** They reuse existing cache files and use a fixed output filename/date. Before collecting a later snapshot, preserve the old cache/output and deliberately update the snapshot date and destination. Do not mix dated cache files. Opening or rebuilding from a full existing cache does not refresh Bloomberg data.

The script handles partial responses, uses a request timeout, batches identifying fields, stops on detected allowance/entitlement errors, checks unique constituent IDs and member count, flags missing fields, and reopens the Excel workbook to verify rows and ticker preservation.

## What is not included

Local Python environments, downloaded installers and SDKs, raw API caches, rendered PDF pages and the challenge handbook are excluded. Each teammate should obtain their own authorized Bloomberg access and official SDK downloads if needed. `SETUP.txt` records the original machine's setup and is not a promise that those local downloads exist in a clone.

## Competition context

The supplied 2026 handbook specifies $1 million starting capital, long-only positions, no leverage, WLS constituents, a stated 20%/$200,000 company limit, and ranking by relative P&L. Trading runs 12 October–13 November 2026. The captain enters trades in TMSG. Verify the exact network's scoring, execution, FX and limit rules before modeling the competition.

No automated order placement is implemented. Research scripts do not imply an investment signal or a recommendation.
