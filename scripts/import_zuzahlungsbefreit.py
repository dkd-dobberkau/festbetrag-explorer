#!/usr/bin/env python3
"""
Parse and import zuzahlungsbefreite Arzneimittel from GKV-Spitzenverband PDF.

This script:
1. Uses pdftotext to extract text from PDF
2. Parses the text and extracts medication information (PZN, name, price, etc.)
3. Converts to CSV format
4. Optionally updates the database with zuzahlungsbefreiung status

Requirements:
    - pdftotext (from poppler-utils)
      macOS: brew install poppler
      Linux: apt-get install poppler-utils

Usage:
    python scripts/import_zuzahlungsbefreit.py [path/to/pdf]

    If no PDF path provided, uses docs/Zuzahlungsbefreit_LATEST.pdf
"""

import sys
import sqlite3
import re
import csv
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import argparse

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "festbetrag.db"


def ensure_database_schema():
    """Ensure database has the correct schema with zuzahlungsbefreit column."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if zuzahlungsbefreit column exists
    cursor.execute("PRAGMA table_info(medications)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'zuzahlungsbefreit' not in columns:
        print("📝 Adding 'zuzahlungsbefreit' column to database...")
        cursor.execute("""
            ALTER TABLE medications
            ADD COLUMN zuzahlungsbefreit INTEGER DEFAULT 0
        """)
        print("✅ Column added")

    # Create index for faster lookups
    try:
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_zuzahlungsbefreit
            ON medications(zuzahlungsbefreit)
        """)
    except sqlite3.OperationalError:
        pass  # Index might already exist

    conn.commit()
    conn.close()


def check_pdftotext() -> bool:
    """Check if pdftotext is available."""
    try:
        result = subprocess.run(['pdftotext', '-v'],
                              capture_output=True,
                              text=True)
        return True
    except FileNotFoundError:
        print("❌ pdftotext not found!")
        print("\nPlease install poppler-utils:")
        print("  macOS:  brew install poppler")
        print("  Linux:  apt-get install poppler-utils")
        return False


def pdf_to_text(pdf_path: Path) -> Path:
    """
    Convert PDF to text using pdftotext.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Path to the generated text file
    """
    txt_path = pdf_path.with_suffix('.txt')

    print(f"📖 Converting PDF to text: {pdf_path}")

    try:
        # Run pdftotext with layout preservation and UTF-8 encoding
        result = subprocess.run([
            'pdftotext',
            '-layout',
            '-enc', 'UTF-8',
            str(pdf_path),
            str(txt_path)
        ], capture_output=True, text=True, check=True)

        print(f"✅ Text extracted to: {txt_path}")
        return txt_path

    except subprocess.CalledProcessError as e:
        print(f"❌ Error running pdftotext: {e}")
        print(f"   stderr: {e.stderr}")
        sys.exit(1)


def parse_text_to_medications(txt_path: Path) -> List[Dict[str, str]]:
    """
    Parse the extracted text file and extract medication data.

    The text typically contains columns (space-separated):
    - PZN (Pharmazentralnummer) - 7 digits
    - Arzneimittelname
    - Darreichungsform
    - Wirkstoff(e)
    - Packungsgröße
    - Hersteller
    - Preis

    Args:
        txt_path: Path to the text file

    Returns:
        List of dictionaries with medication data
    """
    print(f"📝 Parsing text file: {txt_path}")
    medications = []

    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        print(f"   Lines: {len(lines)}")

        for line_num, line in enumerate(lines, 1):
            if line_num % 1000 == 0:
                print(f"   Processing line {line_num}/{len(lines)}...", end='\r')

            # Skip empty lines and headers
            line_stripped = line.strip()
            if not line_stripped or len(line_stripped) < 20:
                continue

            # Skip header lines
            if 'Arzneimittelname' in line or 'PZN' in line or 'Wirkstoff' in line:
                continue

            # Look for PZN (8-digit number, PZN can be 8 digits in layout)
            pzn_match = re.search(r'\b(\d{8})\b', line_stripped)
            if not pzn_match:
                continue

            pzn = pzn_match.group(1)

            # The format is: NAME   PZN   MANUFACTURER   WIRKSTOFF   ...   PREIS
            # Use column positions from the layout
            # Name is typically in columns 0-35, PZN around 35-50

            # Extract name (everything before PZN)
            pzn_pos = line.find(pzn)
            if pzn_pos == -1:
                continue

            name = line[:pzn_pos].strip()

            # Extract price (last number with decimal point in format XX,XX or XX.XX)
            preis = ''
            price_matches = re.findall(r'\d+[,.]\d{2}', line_stripped)
            if price_matches:
                # Take the last price (usually at end of line)
                preis = price_matches[-1].replace(',', '.')

            # Skip if no name or price found
            if not name or not preis:
                continue

            med_data = {
                'pzn': pzn,
                'name': name.strip(),
                'raw_line': line_stripped,  # Keep raw line for debugging
                'preis': preis
            }

            medications.append(med_data)

        print(f"\n✅ Parsed {len(medications)} medications from text")

    except Exception as e:
        print(f"\n❌ Error parsing text file: {e}")
        import traceback
        traceback.print_exc()

    return medications


def save_to_csv(medications: List[Dict[str, str]], csv_path: Path):
    """
    Save medications to CSV file.

    Args:
        medications: List of medication dictionaries
        csv_path: Path where to save the CSV
    """
    if not medications:
        print("⚠️  No medications to save")
        return

    print(f"💾 Saving to CSV: {csv_path}")

    try:
        # Get all unique keys from medications
        fieldnames = set()
        for med in medications:
            fieldnames.update(med.keys())

        fieldnames = sorted(fieldnames)

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(medications)

        print(f"✅ Saved {len(medications)} medications to CSV")
        print(f"   Columns: {', '.join(fieldnames)}")

    except Exception as e:
        print(f"❌ Error saving CSV: {e}")
        import traceback
        traceback.print_exc()


def update_database(medications: List[Dict[str, str]], mark_all: bool = False) -> int:
    """
    Update database with zuzahlungsbefreiung status.

    Args:
        medications: List of medication data from PDF
        mark_all: If True, reset all medications to not exempt before updating

    Returns:
        Number of medications updated
    """
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("   Please ensure your database exists first")
        return 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Reset all if requested
    if mark_all:
        print("🔄 Resetting all zuzahlungsbefreit flags...")
        cursor.execute("UPDATE medications SET zuzahlungsbefreit = 0")
        conn.commit()

    # Update medications from PDF
    updated = 0
    not_found = 0

    print(f"💾 Updating database...")

    for i, med in enumerate(medications, 1):
        if i % 100 == 0:
            print(f"   Processed {i}/{len(medications)}...", end='\r')

        pzn = med['pzn']

        # Try to find medication by PZN
        cursor.execute("""
            UPDATE medications
            SET zuzahlungsbefreit = 1
            WHERE pzn = ?
        """, (pzn,))

        if cursor.rowcount > 0:
            updated += 1
        else:
            not_found += 1

    conn.commit()
    conn.close()

    print(f"\n✅ Updated {updated} medications")
    if not_found > 0:
        print(f"⚠️  {not_found} medications from PDF not found in database")
        print("   (This is normal if your database has different data)")

    return updated


def show_statistics():
    """Show statistics about zuzahlungsbefreit medications."""
    if not DB_PATH.exists():
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM medications")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM medications WHERE zuzahlungsbefreit = 1")
    exempt = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM medications
        WHERE zuzahlungsbefreit = 1 AND differenz < 0
    """)
    exempt_under_festbetrag = cursor.fetchone()[0]

    conn.close()

    print("\n" + "=" * 70)
    print("📊 Database Statistics")
    print("=" * 70)
    print(f"Total medications:              {total:,}")
    print(f"Zuzahlungsbefreit:              {exempt:,} ({exempt/total*100:.1f}%)")
    print(f"  └─ Also under Festbetrag:     {exempt_under_festbetrag:,}")
    print("=" * 70)


def main():
    """Main import function."""
    parser = argparse.ArgumentParser(
        description="Import zuzahlungsbefreite Arzneimittel from PDF"
    )
    parser.add_argument(
        'pdf_path',
        nargs='?',
        type=Path,
        default=DOCS_DIR / "Zuzahlungsbefreit_LATEST.pdf",
        help="Path to PDF file (default: docs/Zuzahlungsbefreit_LATEST.pdf)"
    )
    parser.add_argument(
        '--csv-only',
        action='store_true',
        help="Only generate CSV, do not update database"
    )
    parser.add_argument(
        '--reset-all',
        action='store_true',
        help="Reset all zuzahlungsbefreit flags before import"
    )
    parser.add_argument(
        '--output-csv',
        type=Path,
        help="Custom output path for CSV (default: same directory as PDF)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("📦 Festbetrag Explorer - Zuzahlungsbefreiung Importer")
    print("=" * 70)
    print()

    # Check if pdftotext is available
    if not check_pdftotext():
        return 1

    # Check if PDF exists
    if not args.pdf_path.exists():
        print(f"❌ PDF not found: {args.pdf_path}")
        print("\nPlease run: python scripts/download_data.py")
        return 1

    # Convert PDF to text
    txt_path = pdf_to_text(args.pdf_path)

    # Parse text to medications
    medications = parse_text_to_medications(txt_path)

    if not medications:
        print("❌ No medications found in text")
        return 1

    # Save to CSV
    csv_path = args.output_csv if args.output_csv else txt_path.with_suffix('.csv')
    save_to_csv(medications, csv_path)

    # Update database if requested
    if not args.csv_only:
        # Check if database exists
        if not DB_PATH.exists():
            print(f"\n⚠️  Database not found: {DB_PATH}")
            print("   Skipping database update")
            print("   CSV file has been created: {csv_path}")
        else:
            # Ensure database schema
            ensure_database_schema()

            # Update database
            updated = update_database(medications, mark_all=args.reset_all)

            if updated == 0:
                print("\n⚠️  No medications were updated in database")
            else:
                # Show statistics
                show_statistics()

    print("\n" + "=" * 70)
    print("✅ Processing completed successfully!")
    print(f"\nGenerated files:")
    print(f"  - Text: {txt_path}")
    print(f"  - CSV:  {csv_path}")
    if not args.csv_only and DB_PATH.exists():
        print(f"  - DB:   {DB_PATH} (updated)")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
