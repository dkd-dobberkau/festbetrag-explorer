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


def get_darreichungsform_lang(kuerzel):
    """
    Konvertiert Darreichungsform-Kürzel in Langform.

    Args:
        kuerzel: Abkürzung (z.B. "FTBL")

    Returns:
        Langform (z.B. "Filmtabletten") oder Kürzel falls nicht gefunden
    """
    if not kuerzel:
        return ""

    kuerzel_upper = kuerzel.strip().upper()
    return DARREICHUNGSFORMEN.get(kuerzel_upper, kuerzel)


def get_darreichungsform_with_abbr(kuerzel):
    """
    Gibt Langform mit Kürzel in Klammern zurück.

    Args:
        kuerzel: Abkürzung (z.B. "FTBL")

    Returns:
        "Filmtabletten (FTBL)" oder nur Kürzel falls nicht gefunden
    """
    if not kuerzel:
        return ""

    kuerzel_upper = kuerzel.strip().upper()
    langform = DARREICHUNGSFORMEN.get(kuerzel_upper)

    if langform:
        return f"{langform} ({kuerzel_upper})"
    else:
        return kuerzel_upper
