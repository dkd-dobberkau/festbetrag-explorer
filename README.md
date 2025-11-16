# 💊 Festbetrag Explorer

Eine einfache Streamlit-App zum Suchen und Vergleichen von Medikamentenpreisen basierend auf der deutschen Festbetragsliste und Zuzahlungsbefreiungsliste.

## 🎯 Features

- 🔍 **Autovervollständigung** - Inline-Suche mit Live-Vorschlägen
- 💊 **Schnelle Suche** nach PZN, Medikamentenname oder Wirkstoff
- 💰 **Preisvergleich** mit Festbetrag-Anzeige
- 🔄 **Alternative Medikamente** finden in gleicher Festbetragsgruppe
- 📊 **Statistiken** zu Preisen und Einsparpotenzial
- 🎨 **Farbcodierung**: Grün (unter Festbetrag), Rot (über Festbetrag)
- 🆓 **Zuzahlungsbefreiung** - Import von GKV-Spitzenverband Daten

## 🚀 Installation

### Voraussetzungen
- Python 3.8+
- pip

### Setup

1. Repository klonen:
```bash
git clone https://github.com/YOURUSERNAME/festbetrag-explorer.git
cd festbetrag-explorer
```

2. Dependencies installieren:
```bash
pip install -r requirements.txt
```

3. Datenbank einrichten (siehe unten)

4. (Optional) Zuzahlungsbefreiungsliste importieren:
```bash
# CSV-Datei bereitstellen und importieren
python scripts/import_csv_zuzahlungsbefreit.py docs/Zuzahlungsbefreit_LATEST.csv
```

5. App starten:
```bash
streamlit run app.py
```

Die App öffnet sich automatisch im Browser unter `http://localhost:8501`

## 📊 Datenbank einrichten

Die App benötigt eine SQLite-Datenbank mit der Festbetragsliste.

### Schritt 1: BfArM Festbetragsliste herunterladen

**Offizielle Quelle:** [BfArM - Festbeträge und Zuzahlungen](https://www.bfarm.de/DE/Arzneimittel/Arzneimittelinformationen/Festbetraege-und-Zuzahlungen/_node.html)

1. Laden Sie das aktuelle PDF herunter (z.B. `Festbetraege_20251101.pdf`)
2. Speichern Sie es im `docs/` Verzeichnis

### Schritt 2: Datenbank erstellen

```bash
# Automatischer Import aus PDF (erfordert pdftotext)
# macOS: brew install poppler
# Linux: apt-get install poppler-utils
python scripts/setup_database.py docs/Festbetraege_YYYYMMDD.pdf
```

**Hinweis:** Das PDF-Parsing ist komplex. Wenn Sie Probleme haben, können Sie:
1. Eine vorhandene Datenbank verwenden
2. Die Daten manuell in CSV konvertieren und importieren

### Alternative: Eigene Datenbank

Falls Sie bereits eine Datenbank haben:

```bash
cp /pfad/zu/ihrer/festbetrag.db data/
```

### Erforderliche Datenbank-Struktur

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
    pzn TEXT,
    stand_datum TEXT,
    zuzahlungsbefreit INTEGER DEFAULT 0,  -- 0 = nein, 1 = ja
    UNIQUE(pzn, packungsgroesse, darreichungsform)
);

-- Wichtige Indizes für Performance
CREATE INDEX idx_pzn ON medications(pzn);
CREATE INDEX idx_wirkstoff ON medications(wirkstoff);
CREATE INDEX idx_festbetragsgruppe ON medications(festbetragsgruppe);
CREATE INDEX idx_arzneimittelname ON medications(arzneimittelname);
CREATE INDEX idx_zuzahlungsbefreit ON medications(zuzahlungsbefreit);
```

### CSV-Format

Ihre CSV-Datei sollte mindestens folgende Spalten enthalten:
- `PZN` - Pharmazentralnummer (7-stellig)
- `Arzneimittelname`
- `Wirkstoff`
- `Packungsgroesse`
- `Preis`
- `Festbetrag`
- `Darreichungsform`

## 🆓 Zuzahlungsbefreiung importieren

Die App kann die offizielle Liste zuzahlungsbefreiter Arzneimittel vom GKV-Spitzenverband importieren.

### CSV-Import

```bash
# CSV-Datei vorbereiten (manuell herunterladen oder vorhandene CSV nutzen)
# Erwartetes Format: pzn,name,hersteller,preis

# CSV importieren
python scripts/import_csv_zuzahlungsbefreit.py docs/Zuzahlungsbefreit_LATEST.csv

# Mit Reset aller Flags vor Import
python scripts/import_csv_zuzahlungsbefreit.py --reset-all

# Nur testen, ohne DB zu ändern
python scripts/import_csv_zuzahlungsbefreit.py --dry-run
```

**Was passiert beim Import?**
1. Liest CSV mit PZN, Name, Hersteller, Preis
2. Setzt `zuzahlungsbefreit = 1` für alle gefundenen Medikamente
3. Aktualisiert Hersteller-Information aus CSV

**Erwartetes CSV-Format:**
```csv
pzn,name,hersteller,preis
15210588,ABILIFY 1 MG/ML,CC Pharma GmbH Aripiprazol,36.60
12395133,ABILIFY 1 MG/ML LSG Z EINN,Medicopharm AG Aripiprazol,36.49
```

## 💡 Verwendung

### Suche mit Autovervollständigung

1. **Tippen Sie mindestens 2 Zeichen** in das Suchfeld
2. **Inline-Vorschläge erscheinen** automatisch während der Eingabe
3. **Wählen Sie einen Vorschlag** mit Maus oder Pfeiltasten
4. **Ergebnisse werden sofort angezeigt**

### Suchoptionen (Sidebar)

- **Alles**: Sucht in PZN, Name und Wirkstoff
- **PZN**: Nur Pharmazentralnummer (7-stellig)
- **Medikamentenname**: Nach Handelsnamen suchen
- **Wirkstoff**: Nach Wirkstoff/Active Ingredient suchen

### Alternative Medikamente finden

1. Führen Sie eine Suche durch
2. Scrollen Sie zu "Günstigere Alternativen finden"
3. Wählen Sie ein Medikament aus der Dropdown-Liste
4. Sehen Sie **alle Medikamente in der gleichen Festbetragsgruppe** mit:
   - Gleichem Wirkstoff und Wirkstoffmenge
   - Gleicher Packungsgröße
   - Gleicher Darreichungsform
5. **Einsparpotenzial** wird automatisch berechnet

### Interpretation der Ergebnisse

- **Festbetrag**: Maximalbetrag, den die Krankenkasse erstattet
- **Preis**: Tatsächlicher Apothekenpreis
- **Differenz**:
  - 🟢 **Negativ**: Medikament kostet weniger als Festbetrag → voll erstattet
  - 🔴 **Positiv**: Medikament kostet mehr als Festbetrag → Patient zahlt Differenz
  - 🟡 **Null**: Medikament kostet genau Festbetrag
- **Zuzahlungsbefreit**: Keine gesetzliche Zuzahlung (5-10€) erforderlich

### Was bedeutet "Zuzahlungsbefreit"?

Ein Medikament ist zuzahlungsbefreit, wenn:
- Der Preis **mindestens 30% unter** dem Festbetrag liegt
- Der Hersteller eine Vereinbarung mit dem GKV-Spitzenverband hat

**Vorteil**: Patient zahlt **keine** Zuzahlung (normalerweise 5-10€ pro Packung)

## 📁 Projektstruktur

```
festbetrag-explorer/
├── app.py                          # Haupt-Streamlit-App mit Autovervollständigung
├── requirements.txt                # Python Dependencies
├── README.md                       # Diese Datei
├── CLAUDE.md                       # Entwickler-Dokumentation
├── LICENSE                         # MIT License
├── data/                           # Datenbank-Verzeichnis
│   ├── .gitkeep
│   └── festbetrag.db              # SQLite-Datenbank (nicht im Repo)
├── docs/                           # Dokumentation & Downloads (gitignored)
│   ├── README.md                  # TLDR zu Festbeträgen & Zuzahlungsbefreiung
│   ├── .gitkeep
│   ├── *.pdf                      # GKV-PDFs (gitignored)
│   ├── *.txt                      # Extrahierte Texte (gitignored)
│   └── *.csv                      # Generierte CSVs (gitignored)
├── scripts/                        # Utility-Scripts
│   ├── import_csv_zuzahlungsbefreit.py  # CSV→DB Importer
│   └── extract_manufacturers.py   # Hersteller aus Namen extrahieren
└── utils/                          # Utility-Funktionen (leer)
```

## 🔒 Datenschutz

Diese App verarbeitet keine persönlichen Daten. Sie arbeitet ausschließlich mit der öffentlichen Festbetragsliste.

## ⚠️ Haftungsausschluss

Diese App dient nur zu Informationszwecken. Sie ersetzt nicht die medizinische oder pharmazeutische Beratung.

**Wichtig:**
- Ändern Sie niemals Ihre Medikation ohne Rücksprache mit Ihrem Arzt
- Die Preise können abweichen und veraltet sein
- Medizinische Entscheidungen sollten immer mit medizinischem Fachpersonal getroffen werden

## 📜 Datenquellen

### Festbeträge und Festbetragsgruppen
- **BfArM (Bundesinstitut für Arzneimittel und Medizinprodukte)**
  - https://www.bfarm.de/DE/Arzneimittel/Arzneimittelinformationen/Festbetraege-und-Zuzahlungen/_node.html

### Zuzahlungsbefreite Arzneimittel
- **GKV-Spitzenverband - Befreiungsliste Übersicht**
  - https://www.gkv-spitzenverband.de/service/befreiungsliste_arzneimittel/befreiungsliste_arzneimittel.jsp

- **GKV-Spitzenverband - Aktuelle PDF-Liste (sortiert nach Name)**
  - https://www.gkv-spitzenverband.de/media/dokumente/service_1/zuzahlung_und_befreiung/zuzahlungsbefreite_arzneimittel_nach_name/Zuzahlungsbefreit_sort_Name_251101.pdf
  - Wird monatlich aktualisiert

### Weitere Informationen
- **docs/README.md** - Ausführliches TLDR zu Festbeträgen und Zuzahlungsbefreiung

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei

## 🤝 Beitragen

Contributions sind willkommen! Bitte:
1. Forken Sie das Repo
2. Erstellen Sie einen Feature Branch
3. Committen Sie Ihre Änderungen
4. Pushen Sie zum Branch
5. Öffnen Sie einen Pull Request

## 📞 Support

Bei Fragen oder Problemen öffnen Sie bitte ein Issue auf GitHub.

## 🙏 Credits

Entwickelt mit ❤️ und [Streamlit](https://streamlit.io/)

Daten: GKV-Spitzenverband Festbetragsliste

---

**Hinweis für Entwickler**: Diese App ist absichtlich einfach gehalten, um als Grundlage für eigene Anpassungen zu dienen. Erweitern Sie sie nach Ihren Bedürfnissen!
