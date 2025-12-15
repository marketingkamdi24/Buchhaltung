# Excel-Bearbeitungsanleitung

## Spaltenverarbeitung und Datentransformation

---

### 1. Quelldatei: Erforderliche Spalten

Die folgenden Spalten werden aus der eBay-Transaktionsdatei gelesen:

| Spalte | Verarbeitung |
|--------|--------------|
| Datum der Transaktionserstellung | Direkt übernommen → Spalte A |
| Typ | Direkt übernommen → Spalte B |
| Bestellnummer | Direkt übernommen → Spalte C |
| Alte Bestellnummer | Direkt übernommen → Spalte D |
| Nutzername des Käufers | Direkt übernommen → Spalte E |
| Name des Käufers | Direkt übernommen → Spalte F |
| Zwischensumme Artikel | **+ Verpackung und Versand** → Spalte J |
| Verpackung und Versand | Wird zu Zwischensumme addiert |
| Transaktionsbetrag (inkl. Kosten) | Direkt übernommen → Spalte I |
| Fixer Anteil der Verkaufsprovision | Direkt übernommen → Spalte K |
| Variabler Anteil der Verkaufsprovision | Direkt übernommen → Spalte L |
| Gebühr für sehr hohe Quote | Direkt übernommen → Spalte M |
| Gebühr für unterdurchschnittlichen Servicestatus | Direkt übernommen → Spalte N |
| Internationale Gebühr | Direkt übernommen → Spalte O |
| Betrag abzügl. Kosten | Direkt übernommen → Spalte P |
| Auszahlung Nr. | Direkt übernommen → Spalte Q |
| Auszahlungsdatum | Direkt übernommen → Spalte R |

---

### 2. Wertumwandlungen

| Originalwert | Neuer Wert |
|--------------|------------|
| `--` | `0` |
| `—` | `0` |
| Leer/None | `0` |

---

### 3. Zieldatei: Spaltenstruktur (Hauptblatt)

#### Zeilen 1-3: Metadaten

| Zeile | Spalte A | Spalte B |
|-------|----------|----------|
| 1 | Verkäufer | [Wert aus Quelldatei] |
| 2 | Transaktionen | [Gesamtanzahl] |
| 3 | Betrag | [Wert aus Quelldatei] |

#### Zeile 4: Spaltenüberschriften

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

#### Zeilen ab 5: Transaktionsdaten

| Spalte | Inhalt |
|--------|--------|
| G (KD-NR) | Aus API-Daten: KUNDENNR (Zuordnung über Bestellnummer) |
| H (RG-NR) | Aus API-Daten: BELEGNR (Zuordnung über Bestellnummer) |
| T | Kopie von Spalte J (Verifizierung) |
| U | Formel: `=J[Zeile]-T[Zeile]` |

---

### 4. Zusammenfassungszeilen

#### Gebuehr-Zeile (nach Datenzeilen)

| Spalte | Inhalt |
|--------|--------|
| A | Letztes Transaktionsdatum |
| F | "Gebuehr" |
| G | "7400700" |
| H | Datum als JJJJMM |
| I | Formel: `=J[Zeile]` |
| J | Formel: `=SUMME(K[Zeile]:O[Zeile])` |
| K | Formel: `=SUMME(K5:K[letzte Datenzeile])` |
| L | Formel: `=SUMME(L5:L[letzte Datenzeile])` |
| M | Formel: `=SUMME(M5:M[letzte Datenzeile])` |
| N | Formel: `=SUMME(N5:N[letzte Datenzeile])` |
| O | Formel: `=SUMME(O5:O[letzte Datenzeile])` |
| P | 0 |
| Q | Auszahlungsnummer |
| R | Auszahlungsdatum |

#### Andere Gebuehr-Zeile

| Spalte | Inhalt |
|--------|--------|
| A | Datum der ersten "Andere Gebühr"-Transaktion |
| F | "Andere Gebuehr" |
| G | "7400700" |
| H | Datum als JJJJMM |
| I | Formel: `=J[Zeile]` |
| J | Summe aller "Andere Gebühr"-Beträge |
| P | Summe aller "Andere Gebühr"-Beträge |
| Q | Auszahlungsnummer |
| R | Auszahlungsdatum |

#### Summenzeile

| Spalte | Formel |
|--------|--------|
| J | `=SUMME(J5:J[Andere Gebuehr Zeile])` |
| P | `=SUMME(P5:P[Andere Gebuehr Zeile])` |

---

### 5. Zweites Tabellenblatt ("Tabelle1")

Wird erstellt wenn "Andere Gebühr"-Transaktionen vorhanden sind.

#### Spaltenstruktur pro Zeile

| Spalte | Inhalt |
|--------|--------|
| A | Datum |
| B | Typ |
| C | Bestellnummer |
| D | Alte Bestellnummer |
| E | Nutzername |
| F | Name |
| G | "7400700" |
| H | Datum als JJJJMM |
| I | Betrag abzügl. Kosten |
| J | Betrag abzügl. Kosten |
| K-O | 0 |
| P | Betrag abzügl. Kosten |
| Q | Auszahlungsnummer |
| R | Auszahlungsdatum |

#### Summenzeile (nach Leerzeile)

| Spalte | Formel |
|--------|--------|
| J | `=SUMME(J1:J[letzte Zeile])` |
| P | `=SUMME(P1:P[letzte Zeile])` |

---

### 6. Zeilentrennung nach Typ

| Typ-Wert | Ziel |
|----------|------|
| Enthält "Andere Geb" | → Tabelle1 (zweites Blatt) |
| Alle anderen | → Hauptblatt (Zeilen ab 5) |

---

### 7. Feste Werte

| Position | Wert |
|----------|------|
| Gebuehr-Zeile, Spalte G | "7400700" |
| Andere Gebuehr-Zeile, Spalte G | "7400700" |
| Tabelle1, Spalte G | "7400700" |
| Tabelle1, Spalten K-O | 0 |

---

### 8. Datumsformatierung

| Verwendung | Format |
|------------|--------|
| Spalte H (Gebuehr-Zeilen) | JJJJMM (z.B. "202510") |
| Spalte H (Tabelle1) | JJJJMM (z.B. "202510") |

---

### 9. Ausgabedatei

```
Dateiname: bearbeitet_[Originaldateiname].xlsx
Speicherort: output/