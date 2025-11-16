# 💊 Festbetrag Explorer

Eine einfache Streamlit-App zum Suchen und Vergleichen von Medikamentenpreisen basierend auf der deutschen Festbetragsliste.

## 🎯 Features

- 🔍 **Schnelle Suche** nach PZN, Medikamentenname oder Wirkstoff
- 💰 **Preisvergleich** mit Festbetrag-Anzeige
- 🔄 **Alternative Medikamente** finden
- 📊 **Statistiken** zu Preisen und Einsparpotenzial
- 🎨 **Farbcodierung**: Grün (unter Festbetrag), Rot (über Festbetrag)

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

4. App starten:
```bash
streamlit run app.py
```

Die App öffnet sich automatisch im Browser unter `http://localhost:8501`

## 📊 Datenbank einrichten

Die App benötigt eine SQLite-Datenbank mit der Festbetragsliste.

### Option 1: Eigene Datenbank mitbringen

Legen Sie Ihre `festbetrag.db` in das `data/` Verzeichnis:
```bash
cp /pfad/zu/ihrer/festbetrag.db data/
```

### Option 2: Aus CSV importieren

Falls Sie eine CSV-Datei haben:

```bash
python scripts/import_csv.py /pfad/zur/festbetragsliste.csv
```

### Erforderliche Datenbank-Struktur

```sql
CREATE TABLE medications (
    id INTEGER PRIMARY KEY,
    pzn TEXT UNIQUE,
    arzneimittelname TEXT,
    wirkstoff TEXT,
    wirkstoffmenge_1 REAL,
    wirkstoffmenge_2 REAL,
    packungsgroesse INTEGER,
    darreichungsform TEXT,
    preis REAL,
    festbetrag REAL,
    differenz REAL,  -- preis - festbetrag
    festbetragsgruppe TEXT,
    stufe TEXT,
    stand_datum TEXT
);
```

### CSV-Format

Ihre CSV-Datei sollte mindestens folgende Spalten enthalten:
- `PZN`
- `Arzneimittelname`
- `Wirkstoff`
- `Packungsgroesse`
- `Preis`
- `Festbetrag`
- `Darreichungsform`

## 💡 Verwendung

1. **Suchen**: Geben Sie PZN, Medikamentenname oder Wirkstoff ein
2. **Filtern**: Wählen Sie in der Sidebar die Suchart
3. **Vergleichen**: Sehen Sie alle Preise sortiert
4. **Alternativen finden**: Wählen Sie ein Medikament für günstigere Optionen

### Interpretation der Ergebnisse

- **Festbetrag**: Maximalbetrag, den die Krankenkasse erstattet
- **Preis**: Tatsächlicher Apothekenpreis
- **Differenz**:
  - 🟢 **Negativ**: Medikament kostet weniger als Festbetrag → voll erstattet
  - 🔴 **Positiv**: Medikament kostet mehr als Festbetrag → Zuzahlung erforderlich
  - 🟡 **Null**: Medikament kostet genau Festbetrag

## 📁 Projektstruktur

```
festbetrag-explorer/
├── app.py                 # Haupt-Streamlit-App
├── requirements.txt       # Python Dependencies
├── README.md             # Diese Datei
├── LICENSE               # MIT License
├── data/                 # Datenbank-Verzeichnis
│   ├── .gitkeep
│   └── festbetrag.db    # Ihre Datenbank (nicht im Repo)
├── scripts/             # Hilfs-Scripts
│   └── import_csv.py    # CSV-Import-Script
└── utils/               # Utility-Funktionen
    └── db_handler.py    # Datenbank-Helper
```

## 🔒 Datenschutz

Diese App verarbeitet keine persönlichen Daten. Sie arbeitet ausschließlich mit der öffentlichen Festbetragsliste.

## ⚠️ Haftungsausschluss

Diese App dient nur zu Informationszwecken. Sie ersetzt nicht die medizinische oder pharmazeutische Beratung.

**Wichtig:**
- Ändern Sie niemals Ihre Medikation ohne Rücksprache mit Ihrem Arzt
- Die Preise können abweichen und veraltet sein
- Medizinische Entscheidungen sollten immer mit medizinischem Fachpersonal getroffen werden

## 📜 Datenquelle

Die Festbetragsliste wird vom GKV-Spitzenverband veröffentlicht:
https://www.gkv-spitzenverband.de/

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
