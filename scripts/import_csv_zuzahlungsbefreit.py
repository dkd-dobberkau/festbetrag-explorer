#!/usr/bin/env python3
"""
Import zuzahlungsbefreite Arzneimittel from CSV file.

This script:
1. Reads CSV file with zuzahlungsbefreite medications
2. Updates database with zuzahlungsbefreiung status and manufacturer info

The CSV should have columns: pzn, name, hersteller, preis

Usage:
    python scripts/import_csv_zuzahlungsbefreit.py [path/to/csv]

    If no CSV path provided, uses docs/Zuzahlungsbefreit_LATEST.csv
"""

import sys
import sqlite3
import csv
from pathlib import Path
from typing import List, Dict
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


def read_csv_medications(csv_path: Path) -> List[Dict[str, str]]:
    """
    Read medications from CSV file.

    Expected CSV columns:
    - pzn: Pharmazentralnummer (8 digits in CSV, 7 digits in DB)
    - name: Medication name
    - hersteller: Manufacturer
    - preis: Price

    Args:
        csv_path: Path to CSV file

    Returns:
        List of medication dictionaries
    """
    medications = []

    print(f"📖 Reading CSV file: {csv_path}")

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Check if required columns exist
            if reader.fieldnames:
                print(f"   Columns: {', '.join(reader.fieldnames)}")

            for i, row in enumerate(reader, 1):
                if i % 1000 == 0:
                    print(f"   Read {i} rows...", end='\r')

                # Extract PZN (keep as-is, pad with zeros if needed)
                pzn = row.get('pzn', '').strip()
                # Ensure 8 digits with leading zeros
                if pzn and pzn.isdigit():
                    pzn = pzn.zfill(8)  # Pad with leading zeros to 8 digits

                # Extract other fields
                name = row.get('name', '').strip()
                hersteller = row.get('hersteller', '').strip()
                preis = row.get('preis', '').strip()

                # Skip if no PZN
                if not pzn:
                    continue

                medications.append({
                    'pzn': pzn,
                    'name': name,
                    'hersteller': hersteller,
                    'preis': preis
                })

        print(f"\n✅ Read {len(medications)} medications from CSV")

    except Exception as e:
        print(f"\n❌ Error reading CSV: {e}")
        import traceback
        traceback.print_exc()

    return medications


def update_database(medications: List[Dict[str, str]], mark_all: bool = False) -> int:
    """
    Update database with zuzahlungsbefreiung status.

    Args:
        medications: List of medication data from CSV
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

    # Update medications from CSV
    updated = 0
    not_found = 0
    updated_hersteller = 0

    print(f"💾 Updating database...")

    for i, med in enumerate(medications, 1):
        if i % 100 == 0:
            print(f"   Processed {i}/{len(medications)}...", end='\r')

        pzn = med['pzn']
        hersteller = med.get('hersteller', '')

        # Try to find medication by PZN
        cursor.execute("SELECT id, hersteller FROM medications WHERE pzn = ?", (pzn,))
        result = cursor.fetchone()

        if result:
            med_id, current_hersteller = result

            # Update both zuzahlungsbefreit and hersteller in one query
            if hersteller:
                cursor.execute("""
                    UPDATE medications
                    SET zuzahlungsbefreit = 1,
                        hersteller = ?
                    WHERE id = ?
                """, (hersteller, med_id))
                if hersteller != current_hersteller:
                    updated_hersteller += 1
            else:
                # Only update zuzahlungsbefreit if no hersteller provided
                cursor.execute("""
                    UPDATE medications
                    SET zuzahlungsbefreit = 1
                    WHERE id = ?
                """, (med_id,))

            updated += 1
        else:
            not_found += 1

    conn.commit()
    conn.close()

    print(f"\n✅ Updated {updated} medications")
    print(f"   └─ Updated {updated_hersteller} manufacturers")

    if not_found > 0:
        print(f"⚠️  {not_found} medications from CSV not found in database")
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

    cursor.execute("""
        SELECT COUNT(*) FROM medications
        WHERE hersteller IS NOT NULL AND hersteller != ''
    """)
    with_hersteller = cursor.fetchone()[0]

    conn.close()

    print("\n" + "=" * 70)
    print("📊 Database Statistics")
    print("=" * 70)
    print(f"Total medications:              {total:,}")
    print(f"Zuzahlungsbefreit:              {exempt:,} ({exempt/total*100:.1f}%)")
    print(f"  └─ Also under Festbetrag:     {exempt_under_festbetrag:,}")
    print(f"With manufacturer info:         {with_hersteller:,} ({with_hersteller/total*100:.1f}%)")
    print("=" * 70)


def main():
    """Main import function."""
    parser = argparse.ArgumentParser(
        description="Import zuzahlungsbefreite Arzneimittel from CSV"
    )
    parser.add_argument(
        'csv_path',
        nargs='?',
        type=Path,
        default=DOCS_DIR / "Zuzahlungsbefreit_LATEST.csv",
        help="Path to CSV file (default: docs/Zuzahlungsbefreit_LATEST.csv)"
    )
    parser.add_argument(
        '--reset-all',
        action='store_true',
        help="Reset all zuzahlungsbefreit flags before import"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be updated without making changes"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("📦 Festbetrag Explorer - CSV Zuzahlungsbefreiung Importer")
    print("=" * 70)
    print()

    # Check if CSV exists
    if not args.csv_path.exists():
        print(f"❌ CSV not found: {args.csv_path}")
        print("\nPlease run: python scripts/download_data.py")
        return 1

    # Read CSV
    medications = read_csv_medications(args.csv_path)

    if not medications:
        print("❌ No medications found in CSV")
        return 1

    # Check if database exists
    if not DB_PATH.exists():
        print(f"\n⚠️  Database not found: {DB_PATH}")
        print("   Please create database first")
        return 1

    if args.dry_run:
        print("\n⚠️  DRY RUN - No changes will be made to database")
        print(f"\nWould update {len(medications)} medications")
        # Show first 10 as examples
        print("\nFirst 10 medications:")
        for i, med in enumerate(medications[:10], 1):
            print(f"  {i:2}. PZN {med['pzn']:8} - {med['name'][:50]:50} - {med['hersteller'][:30]}")
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
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
