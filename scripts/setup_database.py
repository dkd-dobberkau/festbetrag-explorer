#!/usr/bin/env python3
"""
Setup database from BfArM Festbetragsliste.

This script creates the database schema and imports data from the BfArM PDF.

Usage:
    python scripts/setup_database.py [path/to/festbetrag.pdf]

    If no PDF path provided, uses docs/BfArM_Festbetraege_LATEST.pdf
"""

import sys
import sqlite3
import re
from pathlib import Path
from typing import List, Dict
import subprocess

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
DB_PATH = DATA_DIR / "festbetrag.db"


def create_database_schema():
    """Create database schema with all tables and indexes."""
    print("📝 Creating database schema...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create medications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medications (
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
            differenz REAL,
            arzneimittelname TEXT,
            pzn TEXT,
            stand_datum TEXT,
            zuzahlungsbefreit INTEGER DEFAULT 0,
            hersteller TEXT,
            UNIQUE(pzn, packungsgroesse, darreichungsform)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pzn ON medications(pzn)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wirkstoff ON medications(wirkstoff)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_festbetragsgruppe ON medications(festbetragsgruppe)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_arzneimittelname ON medications(arzneimittelname)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_zuzahlungsbefreit ON medications(zuzahlungsbefreit)")

    conn.commit()
    conn.close()

    print("✅ Database schema created")


def pdf_to_text(pdf_path: Path) -> Path:
    """
    Convert PDF to text using pdftotext.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Path to generated text file
    """
    txt_path = pdf_path.with_suffix('.txt')

    print(f"📖 Converting PDF to text...")
    print(f"   PDF: {pdf_path}")
    print(f"   TXT: {txt_path}")

    try:
        result = subprocess.run([
            'pdftotext',
            '-layout',
            '-enc', 'UTF-8',
            str(pdf_path),
            str(txt_path)
        ], capture_output=True, text=True, check=True)

        print("✅ PDF converted to text")
        return txt_path

    except FileNotFoundError:
        print("❌ pdftotext not found!")
        print("\nPlease install poppler-utils:")
        print("  macOS:  brew install poppler")
        print("  Linux:  apt-get install poppler-utils")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error converting PDF: {e}")
        print(f"   stderr: {e.stderr}")
        sys.exit(1)


def parse_festbetrag_text(txt_path: Path) -> List[Dict]:
    """
    Parse BfArM text file and extract medication data.

    The format is space-separated with fixed columns:
    wirkstoffmenge wirkstoffmenge packungsgroesse darreichungsform preis festbetrag differenz arzneimittelname pzn

    Args:
        txt_path: Path to text file

    Returns:
        List of medication dictionaries
    """
    print(f"📝 Parsing text file: {txt_path}")

    medications = []
    current_stufe = None
    current_gruppe = None
    current_wirkstoff = None

    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, 1):
        if line_num % 10000 == 0:
            print(f"   Processed {line_num:,} lines, found {len(medications):,} medications...", end='\r')

        # Skip empty lines
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Skip header/footer lines
        if ('GKV-Spitzenverband' in line or 'Seite' in line or
            'Festbetrags' in line or 'Stufe Festbetragsgruppe' in line or
            'Wirkstoff' in line and 'menge' in line):
            continue

        # Check for new group header
        # Format: "  1    Abirateron, Gruppe 1" or "  1    5-Fluorouracil, Gruppe 1"
        header_match = re.match(r'^\s*(\d+)\s+(.+?)(?:,\s*Gruppe\s*\d+)?\s*$', line_stripped)
        if header_match:
            current_stufe = header_match.group(1).strip()
            current_gruppe = header_match.group(2).strip()
            # Extract wirkstoff from gruppe name (remove ", Gruppe X" part)
            current_wirkstoff = re.sub(r',\s*Gruppe\s*\d+', '', current_gruppe).strip()
            continue

        # Parse medication line
        # Must have PZN (8 digits) at the end
        pzn_match = re.search(r'(\d{8})\s*$', line_stripped)
        if not pzn_match:
            continue

        pzn = pzn_match.group(1)

        try:
            # Pattern: extract all numeric and text fields
            # Split line by whitespace
            parts = line_stripped.split()

            if len(parts) < 9:  # Minimum: 2 numbers + packung + dform + 3 prices + name + pzn
                continue

            # Find PZN index
            try:
                pzn_idx = parts.index(pzn)
            except ValueError:
                continue

            # Work backwards from PZN
            # Last part is PZN
            # Everything before last 7 numeric fields is the name

            # Extract numeric values from start
            wirkstoffmenge_1 = None
            wirkstoffmenge_2 = None
            packungsgroesse = None
            preis = None
            festbetrag = None
            differenz = None
            darreichungsform = None

            # Find all numeric values (convert , to .)
            numeric_values = []
            numeric_indices = []
            for i, part in enumerate(parts[:pzn_idx]):
                clean = part.replace(',', '.')
                try:
                    val = float(clean)
                    numeric_values.append(val)
                    numeric_indices.append(i)
                except ValueError:
                    pass

            # Need at least 6 numeric values (wirkstoff1, wirkstoff2, packung, preis, festbetrag, differenz)
            if len(numeric_values) < 6:
                continue

            # Extract values
            wirkstoffmenge_1 = numeric_values[0]
            wirkstoffmenge_2 = numeric_values[1]
            packungsgroesse = int(numeric_values[2])

            # Last 3 numbers are preis, festbetrag, differenz
            preis = numeric_values[-3]
            festbetrag = numeric_values[-2]
            differenz = numeric_values[-1]

            # Find darreichungsform (uppercase letters, typically 4 chars like TABL, FTBL, IJLG, IFIJ)
            # It's between packungsgroesse and preis
            dform_start_idx = numeric_indices[2] + 1  # After packungsgroesse
            dform_end_idx = numeric_indices[-3]  # Before preis

            for i in range(dform_start_idx, min(dform_end_idx, dform_start_idx + 3)):
                if i < len(parts) and parts[i].isupper() and parts[i].isalpha():
                    darreichungsform = parts[i]
                    break

            if not darreichungsform:
                continue

            # Find darreichungsform index
            try:
                dform_idx = parts.index(darreichungsform)
            except ValueError:
                continue

            # Name is between darreichungsform and last 3 numbers
            # Find where the last number before name ends
            last_num_idx = numeric_indices[-3] - 1
            name_parts = parts[dform_idx+1:numeric_indices[-3]]
            arzneimittelname = ' '.join(name_parts).strip()

            if not arzneimittelname or not current_wirkstoff:
                continue

            medications.append({
                'stufe': current_stufe,
                'festbetragsgruppe': current_gruppe,
                'wirkstoff': current_wirkstoff,
                'wirkstoffmenge_1': wirkstoffmenge_1,
                'wirkstoffmenge_2': wirkstoffmenge_2,
                'packungsgroesse': packungsgroesse,
                'darreichungsform': darreichungsform,
                'preis': preis,
                'festbetrag': festbetrag,
                'differenz': differenz,
                'arzneimittelname': arzneimittelname,
                'pzn': pzn
            })

        except (ValueError, IndexError) as e:
            # Skip lines that don't parse correctly
            continue

    print(f"\n✅ Parsed {len(medications):,} medications from text")
    return medications


def import_medications(medications: List[Dict], stand_datum: str = None):
    """
    Import medications into database.

    Args:
        medications: List of medication dictionaries
        stand_datum: Date of the data (e.g., "01.11.2024")
    """
    if not medications:
        print("⚠️  No medications to import")
        return

    print(f"💾 Importing {len(medications):,} medications into database...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    inserted = 0
    skipped = 0

    for i, med in enumerate(medications, 1):
        if i % 1000 == 0:
            print(f"   Imported {inserted:,}, skipped {skipped:,}...", end='\r')

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO medications (
                    stufe, festbetragsgruppe, wirkstoff,
                    wirkstoffmenge_1, wirkstoffmenge_2, packungsgroesse,
                    darreichungsform, preis, festbetrag, differenz,
                    arzneimittelname, pzn, stand_datum
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                med['stufe'],
                med['festbetragsgruppe'],
                med['wirkstoff'],
                med['wirkstoffmenge_1'],
                med['wirkstoffmenge_2'],
                med['packungsgroesse'],
                med['darreichungsform'],
                med['preis'],
                med['festbetrag'],
                med['differenz'],
                med['arzneimittelname'],
                med['pzn'],
                stand_datum
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1

    conn.commit()
    conn.close()

    print(f"\n✅ Imported {inserted:,} medications, skipped {skipped:,} duplicates")


def show_statistics():
    """Show database statistics."""
    if not DB_PATH.exists():
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM medications")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT festbetragsgruppe) FROM medications")
    groups = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT wirkstoff) FROM medications")
    wirkstoffe = cursor.fetchone()[0]

    conn.close()

    print("\n" + "=" * 70)
    print("📊 Database Statistics")
    print("=" * 70)
    print(f"Total medications:              {total:,}")
    print(f"Festbetragsgruppen:             {groups:,}")
    print(f"Unique Wirkstoffe:              {wirkstoffe:,}")
    print("=" * 70)


def main():
    """Main setup function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Setup database from BfArM Festbetragsliste PDF"
    )
    parser.add_argument(
        'pdf_path',
        nargs='?',
        type=Path,
        help="Path to BfArM PDF file (default: docs/BfArM_Festbetraege_LATEST.pdf)"
    )
    parser.add_argument(
        '--skip-pdf',
        action='store_true',
        help="Skip PDF conversion (use existing TXT file)"
    )

    args = parser.parse_args()

    # Determine PDF path
    if args.pdf_path:
        pdf_path = args.pdf_path
    else:
        # Look for latest PDF in docs
        pdf_files = list(DOCS_DIR.glob("BfArM_Festbetraege_*.pdf"))
        if pdf_files:
            pdf_path = sorted(pdf_files)[-1]  # Use latest
        else:
            print("❌ No PDF file found!")
            print("\nPlease provide a PDF file:")
            print("  python scripts/setup_database.py path/to/festbetrag.pdf")
            print("\nOr download from BfArM:")
            print("  https://www.bfarm.de/DE/Arzneimittel/Arzneimittelinformationen/Festbetraege-und-Zuzahlungen/_node.html")
            return 1

    if not pdf_path.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return 1

    print("=" * 70)
    print("📦 Festbetrag Explorer - Database Setup")
    print("=" * 70)
    print()

    # Extract date from filename (e.g., BfArM_Festbetraege_20251101.pdf -> 01.11.2025)
    date_match = re.search(r'(\d{4})(\d{2})(\d{2})', pdf_path.stem)
    stand_datum = None
    if date_match:
        year, month, day = date_match.groups()
        stand_datum = f"{day}.{month}.{year}"
        print(f"📅 Stand: {stand_datum}")

    # Create database schema
    DATA_DIR.mkdir(exist_ok=True)
    create_database_schema()

    # Convert PDF to text
    if args.skip_pdf:
        txt_path = pdf_path.with_suffix('.txt')
        if not txt_path.exists():
            print(f"❌ Text file not found: {txt_path}")
            return 1
        print(f"⏭️  Skipping PDF conversion, using: {txt_path}")
    else:
        txt_path = pdf_to_text(pdf_path)

    # Parse text file
    medications = parse_festbetrag_text(txt_path)

    if not medications:
        print("❌ No medications found in text file")
        return 1

    # Import into database
    import_medications(medications, stand_datum)

    # Show statistics
    show_statistics()

    print("\n" + "=" * 70)
    print("✅ Database setup completed successfully!")
    print("=" * 70)
    print(f"\nDatabase created at: {DB_PATH}")
    print("\nNext steps:")
    print("  1. (Optional) Import zuzahlungsbefreite Medikamente:")
    print("     python scripts/import_csv_zuzahlungsbefreit.py")
    print("  2. Start the app:")
    print("     streamlit run app.py")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
