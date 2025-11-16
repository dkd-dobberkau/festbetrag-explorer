# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Festbetrag Explorer** is a Streamlit web application for searching and comparing German medication prices based on the official Festbetragsliste (fixed reimbursement amount list) and Zuzahlungsbefreiungsliste (co-payment exemption list). The app helps users find cheaper medication alternatives by comparing actual pharmacy prices against the fixed reimbursement amounts set by health insurance providers.

**Key Features:**
- Inline autocomplete search using `streamlit-searchbox`
- Real-time medication price comparison
- Alternative medication finder by Festbetragsgruppe
- Import of co-payment exemption data from GKV-Spitzenverband PDFs

## Running the Application

```bash
# Start the Streamlit app
streamlit run app.py

# App will be available at http://localhost:8501
```

## Import Zuzahlungsbefreiung Data

```bash
# Download current PDF from GKV-Spitzenverband
python scripts/download_data.py

# Convert PDF to CSV and update database
python scripts/import_zuzahlungsbefreit.py

# Or just generate CSV without DB update
python scripts/import_zuzahlungsbefreit.py --csv-only
```

## Database Structure

The application uses a SQLite database (`data/festbetrag.db`) with the following schema:

```sql
CREATE TABLE medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stufe TEXT,
    festbetragsgruppe TEXT,
    wirkstoff TEXT,
    wirkstoffmenge_1 REAL,
    wirkstoffmenge_2 REAL,
    packungsgroesse INTEGER,
    darreichungsform TEXT,
    preis REAL,
    festbetrag REAL,
    differenz REAL,  -- preis - festbetrag
    arzneimittelname TEXT,
    pzn TEXT,  -- Pharmazentralnummer (unique medication identifier)
    stand_datum TEXT,
    zuzahlungsbefreit INTEGER DEFAULT 0,  -- 0 = not exempt, 1 = exempt from co-payment
    UNIQUE(pzn, packungsgroesse, darreichungsform)
);
```

**Important indexes:**
- `idx_pzn` - PZN lookups (REQUIRED for fast search)
- `idx_wirkstoff` - Active ingredient searches (REQUIRED for autocomplete)
- `idx_festbetragsgruppe` - Finding alternatives in same reimbursement group
- `idx_arzneimittelname` - Medication name searches (REQUIRED for autocomplete)
- `idx_zuzahlungsbefreit` - Filter co-payment exempt medications

## Key Concepts

1. **PZN (Pharmazentralnummer)**: Unique 7-digit identifier for each medication in Germany
2. **Festbetrag**: Maximum amount health insurance will reimburse
3. **Differenz**: Price difference (preis - festbetrag)
   - Negative: Fully covered by insurance (displayed green)
   - Positive: Patient pays difference (displayed red)
   - Zero: Exactly at reimbursement limit (displayed yellow)
4. **Festbetragsgruppe**: Medications grouped by same active ingredient, strength, and form - used to find alternatives
5. **Zuzahlungsbefreit**: Co-payment exempt - medication price is at least 30% below Festbetrag and manufacturer has agreement with GKV-Spitzenverband

## Application Architecture

The app is intentionally kept simple with a single-file architecture (`app.py`):

**Main Functions:**
- `check_database()`: Validates database exists and has data
- `search_function(searchterm: str)`: Autocomplete callback for `st_searchbox`
  - Returns up to 15 suggestions based on current search_type
  - Formats suggestions differently per type (PZN, name, wirkstoff)
- `search_medications(query, search_type, limit)`: Main search with 4 modes:
  - `pzn`: Search by PZN (exact match from start)
  - `name`: Search medication names (case-insensitive partial match)
  - `wirkstoff`: Search by active ingredient
  - `all`: Combined search across all fields
- `get_alternatives(pzn)`: Finds cheaper alternatives by matching:
  - Same festbetragsgruppe
  - Same wirkstoffmenge_1 and wirkstoffmenge_2
  - Same packungsgroesse
  - Same darreichungsform

**UI Layout:**
- Sidebar: Search type selection (stored in `st.session_state`), result limit slider, info text
- Main area: Searchbox with inline autocomplete, results table with color coding, statistics
- Bottom section: Alternative finder with savings calculation

**Autocomplete Implementation:**
- Uses `streamlit-searchbox` library for inline autocomplete
- Suggestions appear after 2+ characters typed
- Search type is read from `st.session_state['search_type']`
- Formats: PZN shows "1234567 - Name", Name shows "Name (Wirkstoff)", Wirkstoff shows just "Wirkstoff"

## Database Query Patterns

All searches:
- Use parameterized queries (no SQL injection risk)
- Results sorted by `preis ASC` (cheapest first)
- Limited to prevent performance issues

Search patterns:
- PZN: `pzn LIKE ?` with `f'{query}%'` (prefix match)
- Name: `arzneimittelname LIKE ?` with `f'%{query.upper()}%'` (case-insensitive contains)
- Wirkstoff: `wirkstoff LIKE ?` with `f'%{query}%'` (contains)

## UI Styling

Uses Pandas `style.map()` for conditional formatting (migrated from deprecated `applymap()`):
- Green background (`#d4edda`): differenz < 0 (under Festbetrag)
- Red background (`#f8d7da`): differenz > 0 (over Festbetrag)
- Yellow background (`#fff3cd`): differenz = 0 (exactly at Festbetrag)

Applied in two places:
- Main search results table (app.py:294)
- Alternative medications table (app.py:326)

## Dependencies

**Python packages:**
- `streamlit>=1.30.0`: Web framework
- `pandas>=2.0.0`: Data manipulation and display
- `streamlit-searchbox>=0.1.0`: Inline autocomplete widget
- `requests>=2.31.0`: HTTP downloads for data scripts

**System tools:**
- `pdftotext` (from poppler-utils): PDF text extraction
  - macOS: `brew install poppler`
  - Linux: `apt-get install poppler-utils`

## Project Structure

```
festbetrag-explorer/
├── app.py                          # Single-file Streamlit app with autocomplete
├── requirements.txt                # Python dependencies
├── CLAUDE.md                       # This file
├── README.md                       # User documentation
├── data/
│   ├── .gitkeep
│   └── festbetrag.db              # SQLite database (gitignored)
├── docs/
│   ├── README.md                  # TLDR on Festbeträge & Zuzahlungsbefreiung
│   ├── .gitkeep
│   ├── *.pdf                      # Downloaded PDFs (gitignored)
│   ├── *.txt                      # Extracted text (gitignored)
│   └── *.csv                      # Generated CSVs (gitignored)
├── scripts/
│   ├── download_data.py           # Download GKV-Spitzenverband PDF
│   └── import_zuzahlungsbefreit.py # PDF→TXT→CSV→DB pipeline
└── utils/                          # Empty (reserved for future utilities)
```

## Data Import Pipeline (Zuzahlungsbefreiung)

The import pipeline converts GKV-Spitzenverband PDFs to database entries:

**Pipeline:** PDF → pdftotext → TXT → Parser → CSV → Database

**Key Scripts:**

1. **download_data.py**:
   - Downloads latest PDF from GKV-Spitzenverband
   - Tries current month and last 3 months
   - Creates symlink to `Zuzahlungsbefreit_LATEST.pdf`

2. **import_zuzahlungsbefreit.py**:
   - Uses `pdftotext -layout -enc UTF-8` to extract text
   - Parses text line-by-line for PZN (7-digit numbers)
   - Extracts medication name and price
   - Saves to CSV with columns: `pzn`, `name`, `preis`, `raw_line`
   - Optionally updates database `zuzahlungsbefreit` column
   - Options:
     - `--csv-only`: Don't update database
     - `--reset-all`: Reset all flags before import
     - `--output-csv PATH`: Custom CSV path

**Important:** The parser is heuristic and may need adjustment based on actual PDF format. Check `raw_line` column in CSV for debugging.

## Important Notes

- Database is not in version control (gitignored)
- All downloaded PDFs, TXTs, and CSVs are gitignored
- All German text in UI - app is German-language only
- Medical disclaimer: App is informational only, not medical advice
- Autocomplete requires `st.session_state['search_type']` to be set

## Official Data Sources

1. **BfArM Festbeträge**: https://www.bfarm.de/DE/Arzneimittel/Arzneimittelinformationen/Festbetraege-und-Zuzahlungen/_node.html
2. **GKV-Spitzenverband Befreiungsliste**: https://www.gkv-spitzenverband.de/service/befreiungsliste_arzneimittel/befreiungsliste_arzneimittel.jsp
3. **GKV-Spitzenverband PDF**: https://www.gkv-spitzenverband.de/media/dokumente/service_1/zuzahlung_und_befreiung/zuzahlungsbefreite_arzneimittel_nach_name/Zuzahlungsbefreit_sort_Name_YYMMDD.pdf

See `docs/README.md` for detailed explanation of Festbeträge and Zuzahlungsbefreiung concepts.
