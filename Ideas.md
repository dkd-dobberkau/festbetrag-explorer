# Verbesserungsideen für Festbetrag Explorer

## 🔍 Erweiterte Such- und Filterfunktionen

### 1. Filter-Sidebar
- [ ] Filter nach Zuzahlungsbefreiung (nur 🆓 anzeigen)
- [ ] Filter nach N-Größe (N1/N2/N3)
- [ ] Preisspanne (von-bis)
- [ ] Filter nach Hersteller
- [ ] Nur Medikamente unter Festbetrag

### 2. Intelligente Suche
- [ ] Fuzzy-Suche (Tippfehler-tolerant)
- [ ] Suche nach Indikation/Anwendungsgebiet
- [ ] "Ähnliche Medikamente" Vorschläge

## 💰 Berechnungs- und Vergleichstools

### 3. Kostenrechner
- [ ] Jahreskosten bei Dauermedikation (z.B. "2x täglich → 730 Tabletten/Jahr")
- [ ] Ersparnis-Berechnung beim Wechsel zu Generika
- [ ] Vergleich verschiedener Packungsgrößen (N1 vs N3)

### 4. Direkter Vergleich
- [ ] 2-3 Medikamente nebeneinander vergleichen
- [ ] Beste Alternative automatisch markieren
- [ ] "Günstigste in Festbetragsgruppe" anzeigen

## 📊 Visualisierungen

### 5. Charts und Grafiken
- [ ] Balkendiagramm: Preisvergleich in Festbetragsgruppe
- [ ] Verteilung der Preise (unter/über Festbetrag)
- [ ] Ersparnis-Visualisierung

## 📤 Export und Teilen

### 6. Export-Funktionen
- [ ] Merkliste als PDF (zum Ausdrucken für Arztbesuch)
- [ ] Excel/CSV-Export der Suchergebnisse
- [ ] QR-Code mit PZNs für Apotheke

## 📱 UX-Verbesserungen

### 7. Benutzerfreundlichkeit
- [ ] "Häufig gesucht" Medikamente
- [ ] Letzte Suchanfragen
- [ ] Notizen zu Medikamenten in Merkliste
- [ ] Dark Mode

### 8. Sortierung erweitern
- [ ] Nach Ersparnis sortieren (Differenz zum teuersten)
- [ ] Nach Hersteller
- [ ] Nach Verfügbarkeit (wenn Daten vorhanden)

## 📈 Daten und Analyse

### 9. Statistiken
- [ ] Durchschnittspreis pro Wirkstoff
- [ ] Preisspanne in Festbetragsgruppe
- [ ] Anzahl zuzahlungsbefreiter Alternativen

### 10. Festbetragsgruppen-Ansicht
- [ ] Alle Medikamente einer Festbetragsgruppe anzeigen
- [ ] Vergleich innerhalb der Gruppe
- [ ] Gruppenbeschreibung (Stufe 1/2/3)

## 🔔 Praktische Helfer

### 11. Apotheken-Integration
- [ ] Link zu Apotheken-Preisvergleich (z.B. shop-apotheke.com)
- [ ] Verfügbarkeits-Check (wenn API verfügbar)

### 12. Wirkstoff-Informationen
- [ ] Detailseite mit Wirkstoff-Infos
- [ ] Anwendungsgebiete
- [ ] Link zu offiziellen Quellen (BfArM, Gelbe Liste)

## 🔄 Daten-Updates

### 13. Automatisierung
- [ ] Script zum automatischen Import neuer Listen
- [ ] Update-Datum anzeigen
- [ ] Changelog für Festbetragsänderungen

---

## 🏆 Top 5 Prioritäten (größter Nutzen)

1. **Filter-Sidebar** - Nutzer können schnell zuzahlungsbefreite Medikamente finden
2. **Kostenrechner** - Zeigt echte Jahreskosten und Ersparnis
3. **PDF-Export der Merkliste** - Zum Mitnehmen zum Arzt/Apotheke
4. **Festbetragsgruppen-Ansicht** - Alle Alternativen auf einen Blick
5. **Charts/Visualisierung** - Preisspanne in Gruppe visuell darstellen

---

## Technische Notizen

### Benötigte Packages
- `reportlab` oder `fpdf2` für PDF-Export
- `plotly` oder `altair` für interaktive Charts
- `thefuzz` für Fuzzy-Suche
- `qrcode` für QR-Code-Generierung

### Datenbank-Erweiterungen
- Festbetragsgruppen-Tabelle (Stufe 1/2/3)
- Anwendungsgebiete/Indikationen
- Update-History-Tabelle
