#!/usr/bin/env python3
"""
Extract manufacturer names from medication names.

This script analyzes the arzneimittelname field and extracts manufacturer
information based on common patterns and a comprehensive manufacturer mapping.
"""

import sqlite3
import re
from pathlib import Path
from typing import Optional, Dict

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "festbetrag.db"

# Comprehensive manufacturer mapping
# Format: short_name -> full_name
MANUFACTURER_MAP = {
    # Common German pharmaceutical manufacturers
    'ABZ': 'AbZ Pharma GmbH',
    'ACCORD': 'Accord Healthcare GmbH',
    'AL': 'ALIUD Pharma GmbH',
    'ALIUD': 'ALIUD Pharma GmbH',
    'ARISTO': 'Aristo Pharma GmbH',
    'ARX': 'ARX Healthcare',
    'AXIROMED': 'Axiromed GmbH',
    'BASICS': 'BASICS GmbH',
    'BETA': 'betapharm Arzneimittel GmbH',
    'CIPLA': 'Cipla Europe NV',
    'CT': 'CT Arzneimittel GmbH',
    'DEVATIS': 'Devatis GmbH',
    'GLENMARK': 'Glenmark Pharmaceuticals',
    'HEUMANN': 'HEUMANN PHARMA GmbH',
    'HEXAL': 'Hexal AG',
    'HOLSTEN': 'Holsten Pharma',
    'KRKA': 'KRKA Pharma',
    'MEDAC': 'medac GmbH',
    'MYLAN': 'Mylan Healthcare GmbH',
    'QILU': 'Qilu Pharma',
    'RATIO': 'ratiopharm GmbH',
    'RATIOPHARM': 'ratiopharm GmbH',
    'SANDOZ': 'Sandoz Pharmaceuticals GmbH',
    'STADA': 'STADA Arzneimittel AG',
    'SUN': 'Sun Pharmaceutical',
    'TEVA': 'TEVA GmbH',
    'UROPHARM': 'Uropharm GmbH',
    'VIVANTA': 'Vivanta Pharma',
    'VITANE': 'Vitane Pharma',
    'ZEN': 'Zentiva Pharma',
    'ZENTIVA': 'Zentiva Pharma',
    '1A': '1A Pharma GmbH',
    '1 A': '1A Pharma GmbH',

    # Additional manufacturers
    'BENDA': 'Benda Healthcare',
    'CC PHARMA': 'CC Pharma GmbH',
    'FAIRMED': 'Fair-Med Healthcare',
    'GRY': 'GRY Pharma',
    'HIK': 'Hikma Pharma',
    'PHARES': 'Phares Pharma',
    'PUREN': 'Puren Pharma',
    'PHARMA': 'Pharma GmbH',
    'AMGEN': 'Amgen GmbH',
    'ASTRAZENECA': 'AstraZeneca GmbH',
    'BAYER': 'Bayer Vital GmbH',
    'BERLIN-CHEMIE': 'Berlin-Chemie AG',
    'BOEHRINGER': 'Boehringer Ingelheim',
    'MSD': 'MSD Sharp & Dohme',
    'NOVARTIS': 'Novartis Pharma',
    'PFIZER': 'Pfizer Pharma',
    'ROCHE': 'Roche Pharma AG',
    'SANOFI': 'Sanofi-Aventis Deutschland',

    # Brand names (where brand indicates manufacturer)
    'VELMETIA': 'MSD Sharp & Dohme',
    'JANUVIA': 'MSD Sharp & Dohme',
    'ZYTIGA': 'Janssen-Cilag',
}


def extract_manufacturer_from_name(name: str) -> Optional[str]:
    """
    Extract manufacturer from medication name.

    Examples:
        "ABIRATERON QILU 500MG" -> "Qilu Pharma"
        "BENAZEPRIL AL 5MG" -> "ALIUD Pharma GmbH"
        "FLUOROURACIL ACC 500MG" -> "ACC"

    Args:
        name: Medication name

    Returns:
        Manufacturer name or None if not found
    """
    if not name:
        return None

    name_upper = name.upper()

    # Strategy 1: Look for known manufacturer abbreviations/names
    # Check each known manufacturer (sorted by length, longest first)
    for short_name in sorted(MANUFACTURER_MAP.keys(), key=len, reverse=True):
        # Word boundary pattern - manufacturer must be separate word
        pattern = r'\b' + re.escape(short_name) + r'\b'
        if re.search(pattern, name_upper):
            return MANUFACTURER_MAP[short_name]

    # Strategy 2: Extract second word (often manufacturer)
    # Pattern: WIRKSTOFF HERSTELLER DOSAGE
    # E.g., "Sitagliptin VELMETIA 50MG" -> VELMETIA might be manufacturer
    parts = name.split()

    # If we have at least 2 parts and second part isn't a number or dosage unit
    if len(parts) >= 2:
        second_part = parts[1].upper()

        # Skip if it looks like dosage (contains numbers or units)
        if not re.search(r'\d', second_part) and second_part not in ['MG', 'ML', 'G', 'ST']:
            # Check if this might be a brand name (all caps or mixed case, 3+ chars)
            if len(second_part) >= 3 and not second_part.endswith('MG'):
                # Return as-is if not in map
                return second_part.title()

    return None


def update_all_manufacturers(dry_run=False):
    """
    Update manufacturer field for all medications based on name extraction.

    Args:
        dry_run: If True, only show what would be updated without writing

    Returns:
        Tuple of (total_updated, total_found, total_medications)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all medications without manufacturer
    cursor.execute("""
        SELECT id, arzneimittelname, hersteller
        FROM medications
        WHERE hersteller IS NULL OR hersteller = ''
    """)

    medications = cursor.fetchall()
    total = len(medications)
    found = 0
    updated = 0

    print(f"Processing {total:,} medications without manufacturer...")

    updates = []

    for i, (med_id, name, current_hersteller) in enumerate(medications, 1):
        if i % 5000 == 0:
            print(f"  Processed {i:,}/{total:,}...", end='\r')

        hersteller = extract_manufacturer_from_name(name)

        if hersteller:
            found += 1
            if not dry_run:
                updates.append((hersteller, med_id))

            if i <= 20:  # Show first 20 as examples
                print(f"\n  {name[:50]:50} -> {hersteller}")

    print(f"\n\nFound manufacturer for {found:,} medications ({found/total*100:.1f}%)")

    if not dry_run and updates:
        print(f"\nUpdating {len(updates):,} records in database...")
        cursor.executemany("""
            UPDATE medications
            SET hersteller = ?
            WHERE id = ?
        """, updates)
        conn.commit()
        updated = len(updates)
        print(f"✅ Updated {updated:,} medications")
    elif dry_run:
        print("\n⚠️  Dry run - no changes made to database")

    conn.close()

    return updated, found, total


def show_statistics():
    """Show manufacturer statistics."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM medications")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM medications WHERE hersteller IS NOT NULL AND hersteller != ''")
    with_hersteller = cursor.fetchone()[0]

    cursor.execute("""
        SELECT hersteller, COUNT(*) as cnt
        FROM medications
        WHERE hersteller IS NOT NULL AND hersteller != ''
        GROUP BY hersteller
        ORDER BY cnt DESC
        LIMIT 20
    """)
    top_manufacturers = cursor.fetchall()

    conn.close()

    print("\n" + "=" * 70)
    print("📊 Manufacturer Statistics")
    print("=" * 70)
    print(f"Total medications:              {total:,}")
    print(f"With manufacturer:              {with_hersteller:,} ({with_hersteller/total*100:.1f}%)")
    print(f"Without manufacturer:           {total - with_hersteller:,} ({(total-with_hersteller)/total*100:.1f}%)")
    print("\nTop 20 Manufacturers:")
    for i, (hersteller, cnt) in enumerate(top_manufacturers, 1):
        print(f"  {i:2}. {hersteller[:40]:40} {cnt:5,} medications")
    print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract manufacturers from medication names"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be updated without making changes"
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help="Only show statistics, don't update"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("📦 Festbetrag Explorer - Manufacturer Extractor")
    print("=" * 70)
    print()

    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return 1

    if args.stats_only:
        show_statistics()
        return 0

    # Update manufacturers
    updated, found, total = update_all_manufacturers(dry_run=args.dry_run)

    # Show statistics
    show_statistics()

    print("\n✅ Processing completed!")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
