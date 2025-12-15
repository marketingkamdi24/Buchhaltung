# Excel Processing TODO - Step-by-Step Instructions

## How to Process eBay Transaction Excel Files

---

### STEP 1: PREPARE API DATA (Required First)
- [ ] **1.1** Set date range parameters:
  - `IDATE_FROM`: Start date (format: "DD.MM.YYYY")
  - `IDATE_TO`: End date (format: "DD.MM.YYYY")
  - `IORIGIN`: Set to "'Amazon','Ebay'" for filtering
- [ ] **1.2** Fetch API data containing columns: `ORDER_ID`, `KUNDENNR`, `BELEGNR`
- [ ] **1.3** Save API data (will be used for matching in Step 2)

---

### STEP 2: LOAD AND ANALYZE SOURCE FILE
- [ ] **2.1** Open the eBay transaction Excel file with openpyxl
- [ ] **2.2** Find header row by searching for cell containing "Datum der Transaktionserstellung"
- [ ] **2.3** Create column mapping from header row (column name → column index)
- [ ] **2.4** Extract metadata from rows BEFORE header row:
  - Find row with "Verkäufer" in column A → get value from column B
  - Find row with "Betrag" in column A → get value from column B

---

### STEP 3: BUILD LOOKUP MAPPINGS FROM API DATA
- [ ] **3.1** Create KDNR mapping: `Bestellnummer → KUNDENNR`
- [ ] **3.2** Create RGNR mapping: `Bestellnummer → BELEGNR`
- [ ] **3.3** Log the count of mappings created

---

### STEP 4: READ AND CATEGORIZE DATA ROWS
- [ ] **4.1** Loop through all rows starting from `header_row + 1`
- [ ] **4.2** For each row, extract these columns:
  | Column | Action |
  |--------|--------|
  | Datum der Transaktionserstellung | Copy as-is |
  | Typ | Copy as-is |
  | Bestellnummer | Copy as-is |
  | Alte Bestellnummer | Copy as-is |
  | Nutzername des Käufers | Copy as-is |
  | Name des Käufers | Copy as-is |
  | Zwischensumme Artikel | **ADD** "Verpackung und Versand" value |
  | Transaktionsbetrag (inkl. Kosten) | Copy as-is |
  | Fixer Anteil der Verkaufsprovision | Copy as-is |
  | Variabler Anteil der Verkaufsprovision | Copy as-is |
  | All fee columns (K-O) | Copy as-is |
  | Betrag abzügl. Kosten | Copy as-is |
  | Auszahlung Nr. | Copy as-is |
  | Auszahlungsdatum | Copy as-is |

- [ ] **4.3** Convert special values: `'--'` or `'—'` or `None` → `0`
- [ ] **4.4** Separate rows into two lists:
  - **Regular transactions**: Typ does NOT contain "Andere Geb"
  - **Andere Gebühr transactions**: Typ CONTAINS "Andere Geb"
- [ ] **4.5** Match KD-NR and RG-NR from API data using Bestellnummer as key

---

### STEP 5: CREATE NEW WORKBOOK - MAIN SHEET

#### 5A: Write Header Section (Rows 1-3)
- [ ] **5A.1** Row 1: Cell A1 = "Verkäufer", Cell B1 = [extracted Verkäufer value]
- [ ] **5A.2** Row 2: Cell A2 = "Transaktionen", Cell B2 = [total count of all transactions]
- [ ] **5A.3** Row 3: Cell A3 = "Betrag", Cell B3 = [extracted Betrag value]

#### 5B: Write Column Headers (Row 4)
- [ ] **5B.1** Write headers in row 4:
  | Column | Header |
  |--------|--------|
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

#### 5C: Write Data Rows (Starting Row 5)
- [ ] **5C.1** For each REGULAR transaction, write to columns A-R
- [ ] **5C.2** Column G (KD-NR): Use mapped KUNDENNR from API data
- [ ] **5C.3** Column H (RG-NR): Use mapped BELEGNR from API data
- [ ] **5C.4** Column T: Copy of Zwischensumme (for verification)
- [ ] **5C.5** Column U: Formula `=J[row]-T[row]` (verification check)
- [ ] **5C.6** Track the last row number as `data_end_row`

---

### STEP 6: CREATE SUMMARY ROWS

#### 6A: "Gebuehr" Row (After Last Data Row)
- [ ] **6A.1** Column A: Last transaction date
- [ ] **6A.2** Column F: "Gebuehr"
- [ ] **6A.3** Column G: "7400700"
- [ ] **6A.4** Column H: Date formatted as YYYYMM
- [ ] **6A.5** Column I: Formula `=J[row]`
- [ ] **6A.6** Column J: Formula `=SUM(K[row]:O[row])`
- [ ] **6A.7** Column K: Formula `=SUM(K5:K[data_end_row])`
- [ ] **6A.8** Column L: Formula `=SUM(L5:L[data_end_row])`
- [ ] **6A.9** Column M: Formula `=SUM(M5:M[data_end_row])`
- [ ] **6A.10** Column N: Formula `=SUM(N5:N[data_end_row])`
- [ ] **6A.11** Column O: Formula `=SUM(O5:O[data_end_row])`
- [ ] **6A.12** Column P: 0
- [ ] **6A.13** Columns Q-R: Copy Auszahlungsnr and Auszahlungsdatum

#### 6B: "Andere Gebuehr" Row (Next Row)
- [ ] **6B.1** Column A: Date from first "Andere Gebühr" transaction
- [ ] **6B.2** Column F: "Andere Gebuehr"
- [ ] **6B.3** Column G: "7400700"
- [ ] **6B.4** Column H: Date formatted as YYYYMM
- [ ] **6B.5** Column I: Formula `=J[row]`
- [ ] **6B.6** Column J: **SUM of all "Andere Gebühr" amounts**
- [ ] **6B.7** Column P: **SUM of all "Andere Gebühr" amounts**
- [ ] **6B.8** Columns Q-R: Copy Auszahlungsnr and Auszahlungsdatum

#### 6C: Totals Row (Next Row)
- [ ] **6C.1** Column J: Formula `=SUM(J5:J[andere_gebuehr_row])`
- [ ] **6C.2** Column P: Formula `=SUM(P5:P[andere_gebuehr_row])`

---

### STEP 7: CREATE SECOND SHEET ("Tabelle1") - IF ANDERE GEBÜHR EXISTS
- [ ] **7.1** Create new sheet named "Tabelle1"
- [ ] **7.2** For each "Andere Gebühr" transaction, write row:
  | Column | Value |
  |--------|-------|
  | A | Datum |
  | B | Typ |
  | C | Bestellnummer |
  | D | Alte Bestellnummer |
  | E | Nutzername |
  | F | Name |
  | G | "7400700" |
  | H | Date as YYYYMM |
  | I | Betrag abzügl. Kosten |
  | J | Betrag abzügl. Kosten |
  | K-O | 0 |
  | P | Betrag abzügl. Kosten |
  | Q | Auszahlungsnr |
  | R | Auszahlungsdatum |

- [ ] **7.3** Add SUM formulas after empty row:
  - Column J: `=SUM(J1:J[last_row])`
  - Column P: `=SUM(P1:P[last_row])`

---

### STEP 8: SAVE OUTPUT FILE
- [ ] **8.1** Generate filename: `bearbeitet_[original_filename].xlsx`
- [ ] **8.2** Save to `output/` directory
- [ ] **8.3** Log processing summary:
  - Regular transactions count
  - Andere Gebühr entries count
  - Total Andere Gebühr amount
  - Matched KD-NR count
  - Matched RG-NR count

---

## Quick Reference: Value Transformations

| Original Value | Transformed Value |
|----------------|-------------------|
| `'--'` | `0` |
| `'—'` | `0` |
| `None` | `0` |
| Zwischensumme Artikel | Zwischensumme + Verpackung und Versand |
| Date (for H column) | YYYYMM format |

---

## Quick Reference: Fixed Values

| Location | Fixed Value |
|----------|-------------|
| Gebuehr row, Column G | "7400700" |
| Andere Gebuehr row, Column G | "7400700" |
| Tabelle1, Column G | "7400700" |
| Tabelle1, Columns K-O | 0 |

---

## Output Structure Summary

```
Sheet 1 (Main):
├── Row 1: Verkäufer | [value]
├── Row 2: Transaktionen | [count]
├── Row 3: Betrag | [value]
├── Row 4: [Column Headers A-R]
├── Rows 5-N: [Regular Transaction Data]
├── Row N+1: [Gebuehr Summary Row]
├── Row N+2: [Andere Gebuehr Summary Row]
└── Row N+3: [Totals Row]

Sheet 2 (Tabelle1) - if Andere Gebühr exists:
├── Rows 1-M: [Andere Gebühr Detail Rows]
├── Row M+1: [Empty]
└── Row M+2: [SUM formulas for J and P]