#!/usr/bin/env python3
"""
Darreichungsformen-Lookup
Konvertiert Abkürzungen in Langformen für bessere Lesbarkeit.

Quelle: BfArM Darreichungsformen-Liste (Stand: 01.10.2025)
"""

DARREICHUNGSFORMEN = {
    'AMP': 'Ampullen',
    'AMPD': 'Depotampullen',
    'AMPT': 'Trinkampullen',
    'ANSLB': 'Augen- und Nasensalbe',
    'AUGG': 'Augengel',
    'AUGS': 'Augensalbe',
    'AUGT': 'Augentropfen',
    'BTL': 'Beutel',
    'CREM': 'Creme',
    'DA': 'Druckgasinhalation',
    'DRAG': 'Dragees',
    'EDAT': 'Augentropfen (Einzeldosis)',
    'EDGL': 'Augengel (Einzeldosis)',
    'EMUL': 'Emulsion zur Anwendung auf der Haut',
    'EMULE': 'Emulsion zum Einnehmen',
    'EXPT': 'Expidettäfelchen',
    'FTBL': 'Filmtabletten',
    'FTBM': 'Magensaftresistente Filmtabletten',
    'GEL': 'Gel',
    'GELE': 'Gel zum Einnehmen',
    'GRAM': 'Magensaftresistentes Granulat',
    'GRAN': 'Granulat',
    'IFIJ': 'Injektions-/Infusionslösung',
    'IFLG': 'Infusionslösung',
    'IJLG': 'Injektionslösung',
    'IJSU': 'Injektionssuspension',
    'INHK': 'Hartkapseln mit Pulver zur Inhalation',
    'INHL': 'Lösung zur Inhalation',
    'INHP': 'Pulver zur Inhalation',
    'KAPM': 'Magensaftresistente Kapseln',
    'KAPR': 'Retardkapseln',
    'KAPS': 'Kapseln',
    'KGUM': 'Kaugummis',
    'KOMB': 'Kombipackung',
    'KTAB': 'Kautabletten',
    'LOTI': 'Lotion',
    'LSG': 'Lösung zum Einnehmen',
    'LYOP': 'Lyophilisat zum Einnehmen',
    'NCREM': 'Nasencreme',
    'NGEL': 'Nasengel',
    'NSPR': 'Nasenspray',
    'NTRP': 'Nasentropfen',
    'PAST': 'Paste',
    'PFLA': 'Transdermale Pflaster',
    'PLVD': 'Einzeldosiertes Pulver zur Inhalation',
    'PSTI': 'Pastillen',
    'PULV': 'Pulver',
    'PULVE': 'Pulver zum Einnehmen',
    'RGRAN': 'Retardgranulat',
    'RSCHA': 'Rektalschaum',
    'RSUSP': 'Rektalsuspension',
    'SALB': 'Salbe',
    'SCHAU': 'Schaum zur Anwendung auf der Haut',
    'SIRP': 'Sirup',
    'SPRY': 'Spray zur Anwendung in der Mundhöhle',
    'SPRYX': 'Spray zur Anwendung auf der Haut',
    'STABL': 'Schmelztabletten',
    'SUPP': 'Zäpfchen',
    'SUSP': 'Suspension zum Einnehmen',
    'SUTA': 'Sublingualtabletten',
    'TABB': 'Brausetabletten',
    'TABL': 'Tabletten',
    'TABMD': 'Tabletten mit veränderter Wirkstofffreisetzung',
    'TABR': 'Retardtabletten',
    'TABRM': 'Magensaftresistente Retardtabletten',
    'TBLL': 'Lutschtabletten',
    'TBLM': 'Magensaftresistente Tabletten',
    'TROP': 'Tropfen zum Einnehmen',
    'TTAB': 'Tabletten zur Herstellung einer Lösung',
    'UTBL': 'Überzogene Tabletten',
    'VACR': 'Vaginalcreme',
    'VAGT': 'Vaginaltabletten',
    'VASP': 'Vaginalzäpfchen'
}

# Fallback-Definitionen für häufige Sonderfälle
DARREICHUNGSFORMEN_FALLBACK = {
    'BETA': 'Verschiedene Darreichungsformen',
    'COMP': 'Kombinationspräparat',
}


def get_darreichungsform_lang(kuerzel):
    """
    Konvertiert Darreichungsform-Kürzel in Langform.

    Args:
        kuerzel: Abkürzung (z.B. "FTBL")

    Returns:
        Langform (z.B. "Filmtabletten") oder Fallback/Kürzel falls nicht gefunden
    """
    if not kuerzel:
        return ""

    kuerzel_upper = kuerzel.strip().upper()

    # Erst in offiziellen Darreichungsformen suchen
    if kuerzel_upper in DARREICHUNGSFORMEN:
        return DARREICHUNGSFORMEN[kuerzel_upper]

    # Dann in Fallback-Definitionen suchen
    if kuerzel_upper in DARREICHUNGSFORMEN_FALLBACK:
        return DARREICHUNGSFORMEN_FALLBACK[kuerzel_upper]

    # Sonst Kürzel zurückgeben
    return kuerzel


def get_darreichungsform_with_abbr(kuerzel):
    """
    Gibt Langform mit Kürzel in Klammern zurück.

    Args:
        kuerzel: Abkürzung (z.B. "FTBL")

    Returns:
        - "Filmtabletten (FTBL)" für offizielle Darreichungsformen
        - "Verschiedene Darreichungsformen (BETA)" für Fallback-Werte
        - Nur Kürzel (z.B. "TEVA") für unbekannte Werte (Herstellernamen etc.)
    """
    if not kuerzel:
        return ""

    kuerzel_upper = kuerzel.strip().upper()

    # Erst in offiziellen Darreichungsformen suchen
    if kuerzel_upper in DARREICHUNGSFORMEN:
        return f"{DARREICHUNGSFORMEN[kuerzel_upper]} ({kuerzel_upper})"

    # Dann in Fallback-Definitionen suchen
    if kuerzel_upper in DARREICHUNGSFORMEN_FALLBACK:
        return f"{DARREICHUNGSFORMEN_FALLBACK[kuerzel_upper]} ({kuerzel_upper})"

    # Für unbekannte Werte nur Kürzel zurückgeben (vermutlich Hersteller/Produktnamen)
    return kuerzel_upper
