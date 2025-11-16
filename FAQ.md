# FAQ - Häufig gestellte Fragen

## 📦 Installation & Setup

### Wie installiere ich die App?

```bash
# 1. Repository klonen
git clone https://github.com/dkd-dobberkau/festbetrag-explorer.git
cd festbetrag-explorer

# 2. Dependencies installieren
pip install -r requirements.txt

# 3. Datenbank einrichten (siehe nächste Fragen)
# 4. App starten
streamlit run app.py
```

### Welche Python-Version benötige ich?

Python 3.8 oder höher ist erforderlich. Prüfe deine Version mit:
```bash
python --version
```

### Wie erstelle ich die Datenbank?

Die Datenbank wird NICHT mit dem Repository verteilt. Du musst sie selbst erstellen:

**Schritt 1:** BfArM PDF herunterladen
- Gehe zu https://www.bfarm.de/DE/Arzneimittel/Arzneimittelinformationen/Festbetraege-und-Zuzahlungen/_node.html
- Lade die aktuelle Festbetragsliste als PDF herunter
- Speichere sie im `docs/` Verzeichnis

**Schritt 2:** Datenbank erstellen
```bash
python scripts/setup_database.py docs/Festbetraege_YYYYMMDD.pdf
```

### Ich bekomme den Fehler "pdftotext not found" - was tun?

Das Tool `pdftotext` wird für die PDF-Konvertierung benötigt:

**macOS:**
```bash
brew install poppler
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install poppler-utils
```

**Windows:**
- Lade Poppler für Windows herunter: http://blog.alivate.com.au/poppler-windows/
- Füge den `bin/` Ordner zu deinem PATH hinzu

### Das PDF-Parsing findet nur wenige Medikamente - ist das normal?

Ja, das BfArM PDF hat ein komplexes Layout mit variabler Formatierung. Der Parser ist robust, aber nicht perfekt.

**Alternativen:**
1. Verwende eine bereits vorhandene Datenbank (von einem Kollegen/Team)
2. Konvertiere das PDF manuell in CSV und importiere die Daten
3. Akzeptiere die Einschränkung - auch eine partielle Datenbank ist nützlich

### Wie importiere ich die Zuzahlungsbefreiungsliste?

**Schritt 1:** CSV-Datei vorbereiten
- Lade die Liste vom GKV-Spitzenverband herunter
- Konvertiere zu CSV mit Spalten: `pzn,name,hersteller,preis`
- Speichere als `docs/Zuzahlungsbefreit_LATEST.csv`

**Schritt 2:** Import ausführen
```bash
# Dry-run (testen ohne DB zu ändern)
python scripts/import_csv_zuzahlungsbefreit.py --dry-run

# Echter Import
python scripts/import_csv_zuzahlungsbefreit.py docs/Zuzahlungsbefreit_LATEST.csv

# Mit Reset aller vorherigen Flags
python scripts/import_csv_zuzahlungsbefreit.py --reset-all
```

## 🔍 Nutzung der App

### Wie funktioniert die Suche?

1. **Tippe mindestens 2 Zeichen** in das Suchfeld
2. **Wähle den Suchtyp** in der Sidebar:
   - "Alles" - sucht in PZN, Name und Wirkstoff
   - "PZN" - nur Pharmazentralnummer
   - "Medikamentenname" - Handelsname
   - "Wirkstoff" - Active Ingredient
3. **Inline-Vorschläge** erscheinen automatisch
4. **Klicke auf einen Vorschlag** oder drücke Enter

### Was bedeuten die Farben bei den Preisen?

- 🟢 **Grün (negative Differenz)**: Preis liegt UNTER dem Festbetrag → Krankenkasse erstattet vollständig
- 🔴 **Rot (positive Differenz)**: Preis liegt ÜBER dem Festbetrag → Patient zahlt die Differenz selbst
- 🟡 **Gelb (Differenz = 0)**: Preis entspricht genau dem Festbetrag

### Was ist der Unterschied zwischen "Festbetrag" und "Zuzahlungsbefreiung"?

**Festbetrag:**
- Maximalbetrag, den die Krankenkasse für ein Medikament erstattet
- Wenn der Preis höher ist, zahlt der Patient die Differenz
- Gesetzlich in § 35 SGB V geregelt

**Zuzahlungsbefreiung:**
- Befreiung von der gesetzlichen Zuzahlung (normalerweise 5-10€ pro Packung)
- Gilt für Medikamente, die mindestens 30% unter dem Festbetrag liegen
- Oder wenn der Hersteller eine Vereinbarung mit dem GKV-Spitzenverband hat

**Beispiel:**
- Festbetrag: 100€
- Medikament A: 95€ → Patient zahlt 0€ Differenz + 5-10€ Zuzahlung = 5-10€
- Medikament B: 68€ (>30% unter FB) → Patient zahlt 0€ Differenz + 0€ Zuzahlung (befreit!) = 0€

### Wie finde ich günstigere Alternativen?

1. Führe eine Suche nach deinem Medikament durch
2. Scrolle zu "Günstigere Alternativen finden"
3. Wähle ein Medikament aus der Dropdown-Liste
4. Die App zeigt alle Medikamente mit:
   - Gleichem Wirkstoff und Wirkstoffmenge
   - Gleicher Packungsgröße
   - Gleicher Darreichungsform
5. Das **Einsparpotenzial** wird automatisch berechnet

### Was ist die Watchlist?

Eine lokale Liste deiner bevorzugten/häufig gesuchten Medikamente.

**Wichtig:**
- Speicherung erfolgt nur lokal in `watchlist.json`
- Keine Cloud-Synchronisation
- Keine Datenübertragung
- Privacy-First Design

**Funktionen:**
- Medikamente hinzufügen/entfernen
- Schnellsuche in der Watchlist
- Export als JSON

## 📊 Daten & Quellen

### Woher kommen die Daten?

**Festbeträge & Preise:**
- BfArM (Bundesinstitut für Arzneimittel und Medizinprodukte)
- Offizielle Festbetragsliste nach § 35 SGB V
- https://www.bfarm.de

**Zuzahlungsbefreite Arzneimittel:**
- GKV-Spitzenverband
- Monatlich aktualisierte Befreiungsliste
- https://www.gkv-spitzenverband.de

### Wie aktuell sind die Daten?

Die Daten sind so aktuell wie das PDF, das du heruntergeladen hast.

**Empfehlung:**
- Prüfe regelmäßig (monatlich) auf Updates
- Das Datum steht im Dateinamen: `Festbetraege_YYYYMMDD.pdf`
- Erstelle die Datenbank neu mit aktuellen PDFs

### Warum ist keine Datenbank im Repository?

**Rechtliche Gründe:**
- Die Daten sind urheberrechtlich geschützt
- Dürfen nicht ohne Weiteres verteilt werden
- Nutzer müssen Daten selbst von offiziellen Quellen beziehen

**Technische Gründe:**
- Datenbank wäre zu groß für Git (>100 MB)
- Daten veralten schnell (monatliche Updates)

### Sind die Preise verbindlich?

**Nein!** Die Preise können abweichen und sind nicht verbindlich.

**Wichtig:**
- Preise können sich ändern
- Apotheken können unterschiedliche Preise haben
- Immer aktuellen Preis in der Apotheke erfragen

## 🔧 Fehlerbehebung

### Die App startet nicht - "ModuleNotFoundError"

Du hast die Dependencies nicht installiert:
```bash
pip install -r requirements.txt
```

### "Database not found" Fehler

Die Datenbank existiert nicht. Erstelle sie mit:
```bash
python scripts/setup_database.py docs/Festbetraege_YYYYMMDD.pdf
```

### Die Suche findet keine Ergebnisse

**Mögliche Ursachen:**
1. **Datenbank ist leer** → Prüfe mit:
   ```bash
   sqlite3 data/festbetrag.db "SELECT COUNT(*) FROM medications"
   ```
2. **Falsche PZN-Format** → PZN muss 8-stellig sein (mit führenden Nullen)
3. **Medikament nicht in der Datenbank** → Nicht alle Medikamente sind in der Festbetragsliste

### Import findet 0 Medikamente in CSV

**Prüfe das CSV-Format:**
```csv
pzn,name,hersteller,preis
12345678,MEDIKAMENT NAME,Hersteller GmbH,10.50
```

**Wichtig:**
- PZN muss 8-stellig sein (mit führenden Nullen)
- Spalten: `pzn,name,hersteller,preis`
- UTF-8 Encoding

### Multiple Streamlit-Prozesse laufen

Alle Prozesse stoppen:
```bash
pkill -f "streamlit run app.py"
```

Dann neu starten:
```bash
streamlit run app.py
```

## 🔒 Datenschutz & Sicherheit

### Werden meine Suchanfragen gespeichert?

**Nein!**
- Keine Logs von Suchanfragen
- Keine Tracking-Cookies
- Keine Analytics

### Was passiert mit meiner Watchlist?

- Speicherung nur lokal in `watchlist.json`
- Keine Cloud-Synchronisation
- Keine Server-Übertragung
- Du hast volle Kontrolle

### Kann ich die App offline nutzen?

**Ja!** Nach der Installation ist keine Internetverbindung erforderlich:
- Alle Daten sind lokal in SQLite
- App läuft auf localhost (127.0.0.1)
- Keine externen API-Calls

## ⚖️ Rechtliches

### Darf ich die App kommerziell nutzen?

Die App steht unter **MIT License** - das bedeutet:
- ✅ Private Nutzung
- ✅ Kommerzielle Nutzung
- ✅ Modifikation
- ✅ Distribution
- ⚠️ ABER: Keine Haftung oder Garantie

**Wichtig:** Die Daten (Festbetragsliste) haben eigene Lizenzbedingungen!

### Kann ich mich auf die Preise verlassen?

**Nein!** Diese App dient nur zu Informationszwecken.

**Haftungsausschluss:**
- Preise können veraltet oder fehlerhaft sein
- Keine Garantie für Vollständigkeit oder Richtigkeit
- Keine medizinische oder pharmazeutische Beratung
- Ändern Sie niemals Ihre Medikation ohne Rücksprache mit Ihrem Arzt

### Wer haftet bei Fehlern in den Daten?

Niemand. Die App wird "as-is" bereitgestellt ohne jegliche Garantie.

**§ 7 MIT License:**
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND

## 🛠️ Entwicklung & Anpassung

### Wie kann ich die App anpassen?

1. **Fork das Repository**
2. **Erstelle einen Feature-Branch**
3. **Implementiere deine Änderungen**
4. **(Optional) Pull Request erstellen**

### Wie kann ich zur Entwicklung beitragen?

Siehe [README.md](README.md) Abschnitt "Beitragen"

Issues und Pull Requests sind willkommen!

### Wo kann ich Bugs melden?

GitHub Issues: https://github.com/dkd-dobberkau/festbetrag-explorer/issues

**Bitte angeben:**
- Python-Version
- Betriebssystem
- Fehlermeldung (vollständig)
- Schritte zur Reproduktion

## 📞 Support

### Wo bekomme ich Hilfe?

1. **Diese FAQ durchlesen**
2. **README.md konsultieren**
3. **GitHub Issues durchsuchen**
4. **Neues Issue erstellen** (wenn Problem nicht bekannt)

### Gibt es eine Community?

Aktuell noch nicht. Bei Interesse:
- GitHub Discussions aktivieren?
- Discord Server?
- Matrix Channel?

Feedback willkommen!

---

**Weitere Fragen?** Öffne ein Issue auf GitHub!
