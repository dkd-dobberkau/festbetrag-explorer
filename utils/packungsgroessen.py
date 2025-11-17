#!/usr/bin/env python3
"""
N-Größen (Packungsgrößen) Berechnung nach deutscher Packungsgrößenverordnung

N1 = Kleinpackung
N2 = Normalpackung
N3 = Großpackung

Quelle: § 31 AMG, Packungsgrößenverordnung
"""

# Packungsgrößen-Grenzen für verschiedene Darreichungsformen
# Format: (N1_max, N2_max) - alles darüber ist N3

PACKUNGSGROESSEN_REGELN = {
    # Feste orale Darreichungsformen (Tabletten, Kapseln, etc.)
    'TABL': (10, 30),      # Tabletten
    'FTBL': (10, 30),      # Filmtabletten
    'TBLM': (10, 30),      # Magensaftresistente Tabletten
    'TABR': (10, 30),      # Retardtabletten
    'TABRM': (10, 30),     # Magensaftresistente Retardtabletten
    'TABMD': (10, 30),     # Tabletten mit veränderter Wirkstofffreisetzung
    'KAPS': (10, 30),      # Kapseln
    'KAPM': (10, 30),      # Magensaftresistente Kapseln
    'KAPR': (10, 30),      # Retardkapseln
    'DRAG': (10, 30),      # Dragees
    'KTAB': (10, 30),      # Kautabletten
    'TABB': (10, 30),      # Brausetabletten
    'TBLL': (10, 30),      # Lutschtabletten
    'SUTA': (10, 30),      # Sublingualtabletten
    'STABL': (10, 30),     # Schmelztabletten
    'UTBL': (10, 30),      # Überzogene Tabletten

    # Flüssige Darreichungsformen (in ml)
    'LSG': (50, 100),      # Lösung zum Einnehmen
    'TROP': (10, 30),      # Tropfen zum Einnehmen (meist kleinere Packungen)
    'SUSP': (50, 100),     # Suspension zum Einnehmen
    'EMULE': (50, 100),    # Emulsion zum Einnehmen
    'SIRP': (100, 200),    # Sirup

    # Rektale/Vaginale Darreichungsformen
    'SUPP': (5, 10),       # Zäpfchen
    'VASP': (5, 10),       # Vaginalzäpfchen
    'VAGT': (6, 12),       # Vaginaltabletten

    # Topische Darreichungsformen (in g oder ml)
    'CREM': (20, 50),      # Creme
    'SALB': (20, 50),      # Salbe
    'GEL': (20, 50),       # Gel
    'LOTI': (30, 100),     # Lotion

    # Augenpräparate (in ml oder Einzeldosen)
    'AUGT': (5, 10),       # Augentropfen
    'AUGG': (3, 10),       # Augengel

    # Nasenpräparate
    'NSPR': (10, 20),      # Nasenspray (ml)
    'NTRP': (10, 20),      # Nasentropfen (ml)

    # Inhalativa
    'INHP': (30, 100),     # Pulver zur Inhalation (Einzeldosen)
    'INHL': (20, 60),      # Lösung zur Inhalation (ml)

    # Injektionspräparate
    'AMP': (5, 10),        # Ampullen
    'IJLG': (5, 10),       # Injektionslösung (Ampullen)

    # Pflaster
    'PFLA': (4, 12),       # Transdermale Pflaster

    # Granulat/Pulver (in Beuteln oder Dosen)
    'GRAN': (10, 30),      # Granulat (Beutel)
    'PULVE': (10, 30),     # Pulver zum Einnehmen (Beutel)

    # Default für unbekannte Darreichungsformen
    'DEFAULT': (10, 30)
}


def get_packungsgroesse_n(packungsgroesse, darreichungsform):
    """
    Ermittelt die N-Größe (N1, N2, N3) basierend auf Packungsgröße und Darreichungsform.

    Args:
        packungsgroesse: Anzahl der Einheiten (Tabletten, ml, etc.)
        darreichungsform: Darreichungsform-Kürzel (z.B. "FTBL", "LSG")

    Returns:
        str: "N1", "N2", "N3" oder "" falls nicht berechenbar
    """
    if not packungsgroesse or packungsgroesse <= 0:
        return ""

    # Darreichungsform normalisieren
    dform = darreichungsform.strip().upper() if darreichungsform else "DEFAULT"

    # Grenzen abrufen (mit Fallback auf DEFAULT)
    n1_max, n2_max = PACKUNGSGROESSEN_REGELN.get(dform, PACKUNGSGROESSEN_REGELN['DEFAULT'])

    # N-Größe berechnen
    if packungsgroesse <= n1_max:
        return "N1"
    elif packungsgroesse <= n2_max:
        return "N2"
    else:
        return "N3"


def get_packungsgroesse_beschreibung(n_groesse):
    """
    Gibt Beschreibung der N-Größe zurück.

    Args:
        n_groesse: "N1", "N2" oder "N3"

    Returns:
        str: Beschreibung der Packungsgröße
    """
    beschreibungen = {
        'N1': 'Kleinpackung',
        'N2': 'Normalpackung',
        'N3': 'Großpackung'
    }
    return beschreibungen.get(n_groesse, '')


def get_packungsgroesse_with_beschreibung(packungsgroesse, darreichungsform):
    """
    Gibt N-Größe mit Beschreibung zurück.

    Args:
        packungsgroesse: Anzahl der Einheiten
        darreichungsform: Darreichungsform-Kürzel

    Returns:
        str: z.B. "N3 (Großpackung)" oder "" falls nicht berechenbar
    """
    n_groesse = get_packungsgroesse_n(packungsgroesse, darreichungsform)

    if not n_groesse:
        return ""

    beschreibung = get_packungsgroesse_beschreibung(n_groesse)

    if beschreibung:
        return f"{n_groesse} ({beschreibung})"
    else:
        return n_groesse


def get_packungsgroesse_emoji(n_groesse):
    """
    Gibt Emoji für N-Größe zurück.

    Args:
        n_groesse: "N1", "N2" oder "N3"

    Returns:
        str: Emoji
    """
    emojis = {
        'N1': '📦',  # Kleine Box
        'N2': '📦📦',  # Mittlere Box
        'N3': '📦📦📦'  # Große Box
    }
    return emojis.get(n_groesse, '')
