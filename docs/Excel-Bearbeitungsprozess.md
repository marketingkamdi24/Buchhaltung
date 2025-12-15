# Excel-Bearbeitungsprozess

Diese Dokumentation beschreibt den vollständigen Prozess der Excel-Bearbeitung, der auf eBay-Transaktionsberichte angewendet wird.

---

## Übersicht

Der Excel-Bearbeitungsprozess besteht aus zwei Hauptschritten:

1. **Schritt 1: API-Daten abrufen** - Laden von Kundennummern und Belegnummern aus der API
2. **Schritt 2: Daten abgleichen & verarbeiten** - Abgleich der Shop-Daten mit API-Daten und Transformation der Excel-Datei

---

## Schritt 1: API-Daten abrufen

### Eingabeparameter
| Parameter | Beschreibung | Beispiel |
|-----------|--------------|----------|
| IDATE_FROM | Startdatum | "28.10.2025" |
| IDATE_TO | Enddatum | "29.10.2025" |
| IORIGIN | Herkunftsfilter | "'Amazon','Ebay'" |

### Erforderliche API-Spalten
| Spalte | Verwendung |
|--------|------------|
| ORDER_ID | Abgleichschlüssel (↔ Bestellnummer) |
| KUNDENNR | Wird zu KD-NR-Spalte zugeordnet |
| BELEGNR | Wird zu RG-NR-Spalte zugeordnet |

---

## Schritt 2: Excel-Transformation

### 2.1 Datei laden und Kopfzeile finden

1. Die Excel-Datei wird mit `openpyxl` geladen
2. Die Kopfzeile wird durch Suche nach `'Datum der Transaktionserstellung'` identifiziert
3. Eine Spaltenzuordnung wird aus der gefundenen Kopfzeile erstellt

### 2.2 Metadaten extrahieren

Aus den Zeilen vor der Kopfzeile werden folgende Werte extrahiert:
- **Verkäufer**: Verkäufername aus Zeile mit "Verkäufer" in Spalte A
- **Betrag**: Gesamtbetrag aus Zeile mit "Betrag" in Spalte A

### 2.3 API-Zuordnungen erstellen

Aus den API-Daten werden zwei Zuordnungstabellen erstellt:
- **KDNR-Zuordnung**: Bestellnummer → KUNDENNR
- **RGNR-Zuordnung**: Bestellnummer → BELEGNR

### 2.4 Datenzeilen lesen und kategorisieren

Alle Transaktionszeilen werden gelesen und in zwei Kategorien aufgeteilt:
- **Reguläre Transaktionen**: Alle Zeilen außer "Andere Gebühr"
- **Andere Gebühr-Transaktionen**: Zeilen mit Typ "Andere Gebühr"

### 2.5 Spaltentransformationen

Für jede Transaktionszeile werden folgende Daten erfasst:

| Ursprungsspalte | Transformation |
|-----------------|----------------|
| Datum der Transaktionserstellung | Direkt übernommen |
| Typ | Direkt übernommen |
| Bestellnummer | Direkt übernommen |
| Alte Bestellnummer | Direkt übernommen |
| Nutzername des Käufers | Direkt übernommen |
| Name des Käufers | Direkt übernommen |
| Zwischensumme Artikel | **+ Verpackung und Versand addiert** |
| Fixer Anteil der Verkaufsprovision | Direkt übernommen |
| Variabler Anteil der Verkaufsprovision | Direkt übernommen |
| Gebühr für sehr hohe Quote | Direkt übernommen |
| Gebühr für unterdurchschnittlichen Servicestatus | Direkt übernommen |
| Internationale Gebühr | Direkt übernommen |
| Betrag abzügl. Kosten | Direkt übernommen |
| Auszahlung Nr. | Direkt übernommen |
| Auszahlungsdatum | Direkt übernommen |

**Besondere Wertkonvertierung:**
- `'--'` oder `'—'` oder `None` → `0` (numerischer Wert)

### 2.6 Neue Arbeitsmappe erstellen

#### Hauptblatt-Struktur

**Zeilen 1-3: Metadaten**
| Zeile | Spalte A | Spalte B |
|-------|----------|----------|
| 1 | Verkäufer | [Verkäufername] |
| 2 | Transaktionen | [Gesamtanzahl Transaktionen] |
| 3 | Betrag | [Gesamtbetrag] |

**Zeile 4: Spaltenüberschriften**
| Spalte | Überschrift |
|--------|-------------|
| A | Datum der Transaktionserstellung |
| B | Typ |
| C | Bestellnummer |
| D | Alte Bestellnummer |
| E | Nutzername des Käufers |
| F | Name des Käufers |
| G | KD-NR |
| H | RG-NR |
| I | Transaktionsbetrag (inkl. Kosten) |
| J | Zwischensumme Artikel |
| K | Fixer Anteil der Verkaufsprovision |
| L | Variabler Anteil der Verkaufsprovision |
| M | Gebühr für sehr hohe Quote an „nicht wie beschriebenen Artikeln" |
| N | Gebühr für unterdurchschnittlichen Servicestatus |
| O | Internationale Gebühr |
| P | Betrag abzügl. Kosten |
| Q | Auszahlung Nr. |
| R | Auszahlungsdatum |

**Zeile 5+: Transaktionsdaten**
- KD-NR (Spalte G): Aus API-Daten über Bestellnummer zugeordnet
- RG-NR (Spalte H): Aus API-Daten über Bestellnummer zugeordnet
- Spalte T: Kopie von Zwischensumme (zur Verifizierung)
- Spalte U: Formel `=J[Zeile]-T[Zeile]` (zur Verifizierung)

### 2.7 Gebührenzeilen erstellen

#### "Gebuehr"-Zeile (nach Datenzeilen)

| Spalte | Wert |
|--------|------|
| A | Letztes Datum der Transaktionen |
| F | "Gebuehr" |
| G | "7400700" |
| H | Datum im Format YYYYMM |
| I | `=J[Zeile]` |
| J | `=SUM(K[Zeile]:O[Zeile])` |
| K | `=SUM(K5:K[letzte Datenzeile])` |
| L | `=SUM(L5:L[letzte Datenzeile])` |
| M | `=SUM(M5:M[letzte Datenzeile])` |
| N | `=SUM(N5:N[letzte Datenzeile])` |
| O | `=SUM(O5:O[letzte Datenzeile])` |
| P | 0 |
| Q | Auszahlungsnummer |
| R | Auszahlungsdatum |

#### "Andere Gebuehr"-Zeile

| Spalte | Wert |
|--------|------|
| A | Datum der ersten "Andere Gebühr"-Transaktion |
| F | "Andere Gebuehr" |
| G | "7400700" |
| H | Datum im Format YYYYMM |
| I | `=J[Zeile]` |
| J | Summe aller "Andere Gebühr" Beträge |
| P | Summe aller "Andere Gebühr" Beträge |
| Q | Auszahlungsnummer |
| R | Auszahlungsdatum |

#### Summenzeile

| Spalte | Formel |
|--------|--------|
| J | `=SUM(J5:J[Andere Gebuehr Zeile])` |
| P | `=SUM(P5:P[Andere Gebuehr Zeile])` |

### 2.8 Zweites Tabellenblatt ("Tabelle1")

Falls "Andere Gebühr"-Transaktionen vorhanden sind, wird ein zweites Tabellenblatt erstellt:

**Spaltenstruktur (pro "Andere Gebühr"-Zeile):**
| Spalte | Inhalt |
|--------|--------|
| A | Datum |
| B | Typ |
| C | Bestellnummer |
| D | Alte Bestellnummer |
| E | Nutzername |
| F | Name |
| G | "7400700" |
| H | Datum im Format YYYYMM |
| I | Betrag abzügl. Kosten |
| J | Betrag abzügl. Kosten |
| K-O | 0 |
| P | Betrag abzügl. Kosten |
| Q | Auszahlungsnummer |
| R | Auszahlungsdatum |

**Summenzeilen am Ende:**
- Spalte J: `=SUM(J1:J[Summenzeile-1])`
- Spalte P: `=SUM(P1:P[Summenzeile-1])`

---

## Zusammenfassung der Transformationsregeln

| Nr. | Regel | Beschreibung |
|-----|-------|--------------|
| 1 | Kopfzeilen-Extraktion | Verkäufer, Betrag, Transaktionen aus Metadaten |
| 2 | Datenabgleich | Bestellnummer ↔ ORDER_ID |
| 3 | Zeilen-Umstrukturierung | Daten ab Zeile 5, Überschriften in Zeile 4 |
| 4 | Spalten-Organisation | Standard-Format A-R |
| 5 | KD-NR / RG-NR Zuordnung | Aus API-Daten via Bestellnummer |
| 6 | Verifizierungsspalten | T: Kopie von J, U: =J-T Formel |
| 7 | "Andere Gebühr" Behandlung | Verschiebung auf Tabellenblatt 2 |
| 8 | Gebühren-Aggregation | Gebuehr-Zeile mit SUM-Formeln |
| 9 | Wertkonvertierung | `--` → `0` |
| 10 | Versandkosten-Addition | Verpackung und Versand zu Zwischensumme addiert |

---

## Ausgabedatei

Die verarbeitete Datei wird gespeichert als:
```
bearbeitet_[Original-Dateiname].xlsx
```

im `output/`-Verzeichnis.

---

## Prozessprotokoll

Während der Verarbeitung werden folgende Informationen protokolliert:
- Geladene Datei und Dimensionen
- Anzahl geladener KUNDENNR- und BELEGNR-Zuordnungen
- Gefundene Kopfzeile
- Anzahl der Spalten
- Extrahierte Metadaten
- Anzahl regulärer Transaktionen
- Anzahl "Andere Gebühr"-Transaktionen
- Abgleichstatistiken für KD-NR und RG-NR
- Speicherbestätigung mit Zusammenfassung

---

## Fehlerbehandlung

Falls Fehler auftreten:
- Fehlende Kopfzeile → Abbruch mit Fehlermeldung
- Keine API-Daten → Abbruch mit Hinweis auf Schritt 1
- Fehlende ORDER_ID-Spalte → Abbruch mit Spaltenfehler
- Keine übereinstimmenden Bestellungen → Abbruch mit Abgleichfehler
- Sonstige Fehler → Vollständiger Traceback wird protokolliert