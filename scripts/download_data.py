#!/usr/bin/env python3
"""
Download official medication data from GKV-Spitzenverband and BfArM.

This script downloads:
1. Zuzahlungsbefreite Arzneimittelliste (PDF) from GKV-Spitzenverband
2. Additional data sources as needed

Usage:
    python scripts/download_data.py
"""

import requests
import os
from pathlib import Path
from datetime import datetime
import sys

# Base URLs
GKV_BASE_URL = "https://www.gkv-spitzenverband.de/media/dokumente/service_1/zuzahlung_und_befreiung/zuzahlungsbefreite_arzneimittel_nach_name"
BFARM_BASE_URL = "https://www.bfarm.de/DE/Arzneimittel/Arzneimittelinformationen/Festbetraege-und-Zuzahlungen/_node.html"

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"

# Ensure docs directory exists
DOCS_DIR.mkdir(exist_ok=True)


def download_file(url: str, destination: Path, description: str = "File") -> bool:
    """
    Download a file from URL to destination.

    Args:
        url: URL to download from
        destination: Path where to save the file
        description: Human-readable description for logging

    Returns:
        True if successful, False otherwise
    """
    print(f"📥 Downloading {description}...")
    print(f"   URL: {url}")
    print(f"   Destination: {destination}")

    try:
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()

        # Get file size if available
        total_size = int(response.headers.get('content-length', 0))

        # Download with progress
        downloaded = 0
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r   Progress: {percent:.1f}%", end='', flush=True)

        print(f"\n✅ Downloaded {description} successfully")
        print(f"   Size: {downloaded / 1024:.2f} KB")
        return True

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error downloading {description}: {e}")
        return False


def download_gkv_zuzahlungsbefreit_pdf() -> bool:
    """
    Download the latest Zuzahlungsbefreite Arzneimittel PDF.

    The filename format is: Zuzahlungsbefreit_sort_Name_YYMMDD.pdf
    We'll try the current month first, then previous months.

    Returns:
        True if successful, False otherwise
    """
    now = datetime.now()

    # Try current month and last 3 months
    for month_offset in range(4):
        year = now.year if now.month - month_offset > 0 else now.year - 1
        month = (now.month - month_offset) if now.month - month_offset > 0 else 12 + (now.month - month_offset)

        # Format: YYMMDD (first day of month)
        date_str = f"{year % 100:02d}{month:02d}01"
        filename = f"Zuzahlungsbefreit_sort_Name_{date_str}.pdf"
        url = f"{GKV_BASE_URL}/{filename}"
        destination = DOCS_DIR / filename

        print(f"\n🔍 Trying {filename}...")
        if download_file(url, destination, f"Zuzahlungsbefreite Liste ({date_str})"):
            # Create a symlink to latest
            latest_link = DOCS_DIR / "Zuzahlungsbefreit_LATEST.pdf"
            if latest_link.exists():
                latest_link.unlink()
            try:
                latest_link.symlink_to(filename)
                print(f"🔗 Created symlink: {latest_link.name} -> {filename}")
            except OSError:
                # Symlinks might not work on all systems, copy instead
                import shutil
                shutil.copy(destination, latest_link)
                print(f"📄 Created copy: {latest_link.name}")
            return True

    print("\n❌ Could not find any recent PDF version")
    print("   Please check manually at:")
    print("   https://www.gkv-spitzenverband.de/service/befreiungsliste_arzneimittel/befreiungsliste_arzneimittel.jsp")
    return False


def main():
    """Main download function."""
    print("=" * 70)
    print("📦 Festbetrag Explorer - Data Downloader")
    print("=" * 70)
    print()

    success = True

    # Download GKV Zuzahlungsbefreit PDF
    if not download_gkv_zuzahlungsbefreit_pdf():
        success = False

    print("\n" + "=" * 70)
    if success:
        print("✅ All downloads completed successfully!")
        print("\nNext steps:")
        print("1. Run: python scripts/import_zuzahlungsbefreit.py")
        print("2. This will parse the PDF and update the database")
    else:
        print("⚠️  Some downloads failed - check the errors above")
        print("\nYou can still proceed with manual downloads:")
        print("1. Visit: https://www.gkv-spitzenverband.de/service/befreiungsliste_arzneimittel/befreiungsliste_arzneimittel.jsp")
        print(f"2. Download PDF manually to: {DOCS_DIR}")
    print("=" * 70)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
