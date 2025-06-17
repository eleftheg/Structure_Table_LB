# Updated Script Usage Examples

The `nephro_reports_processor_excel_only.py` script has been updated to support both Excel (.xlsx) and CSV output formats.

## Command Line Usage

### Default behavior (Excel output):
```powershell
python nephro_reports_processor_excel_only.py
```
This will create an Excel file (.xlsx) by default.

### Explicit Excel output:
```powershell
python nephro_reports_processor_excel_only.py --format xlsx
```

### CSV output:
```powershell
python nephro_reports_processor_excel_only.py --format csv
```

## Changes Made

1. **Added command line argument parsing** using `argparse`
2. **Excel is now the default format** (.xlsx)
3. **CSV format still supported** with `--format csv`
4. **Automatic openpyxl installation** if the package is missing
5. **Enhanced output messages** showing the selected format
6. **Added AF-Nummer (MEDAT) extraction** - now included in output data
7. **Added AF-Nummer (MEDAT) auto-filling** - fills missing AF-Nummer values when the same Blutbuch-Nummer has AF-Nummer elsewhere

## Data Processing Features

### Missing Value Handling
The script now includes intelligent missing value handling:

1. **Blutbuch-Nummer filling**: Missing patient identifiers are forward-filled from previous rows
2. **AF-Nummer (MEDAT) filling**: Missing laboratory accession numbers are filled using values from the same patient (Blutbuch-Nummer) when available
   - Searches for existing AF-Nummer values within the same Blutbuch-Nummer group
   - Fills empty AF-Nummer cells with the found value
   - Provides statistics on filling success rate

## Data Columns Extracted

The script now extracts the following columns:
- **Blutbuch_nummer**: Patient identifier
- **AF_Nummer_MEDAT**: Laboratory accession number (MEDAT)
- **Gen**: Gene name
- **cDNA**: DNA variant description
- **Protein**: Protein variant description  
- **Klassifizierung**: Variant classification (standardized)

## Output Files

- Excel files: `nephro_long_table_transformed.YYYY-MM-DD_HH-MM-SS.xlsx`
- CSV files: `nephro_long_table_transformed.YYYY-MM-DD_HH-MM-SS.csv`

## Requirements

- pandas
- numpy
- openpyxl (for Excel support - automatically installed if missing)

The script will automatically attempt to install openpyxl if it's not available when Excel output is requested.
