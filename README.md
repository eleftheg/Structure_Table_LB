# Nephrology Reports Processor

## Overview

The `nephro_reports_processor_excel_only.py` script is a configurable tool designed to process and standardize nephrology genetic testing data from Excel files. It performs comprehensive data cleaning, standardization, and long-table transformation operations to prepare the data for analysis.

## Configuration

The script uses a `config.json` file to externalize all hardcoded values, making it easily customizable without modifying the code.

### Configuration Structure

```json
{
  "file_paths": {
    "input_excel_file": "path/to/input/file.xlsx",
    "output_directory": "results",
    "output_filename_prefix": "nephro_long_table_transformed"
  },
  "column_mapping": {
    "Blutbuch-Nummer": "Blutbuch_nummer",
    "Gen": "Gen",
    "cDNA": "cDNA",
    "Protein": "Protein",
    "Klassifizierung": "Klassifizierung"
  },
  "alternative_column_names": {
    "Gen": ["Gen...17", "Gen...16", "Gen...15"],
    "Protein": ["Protein...19", "Protein...18", "Protein...17"]
  },
  "klassifizierung_mapping": {
    "class_2_variants": {
      "input_values": ["Klasse II (Risiko-Poly)", "Klasse II, Risk Factor"],
      "output_value": "Risk factor"
    }
  }
}
```

## Main Functionality

### 1. Data Loading
- Loads Excel file from path specified in `config.json`
- Configurable input file path and data types
- Handles missing files gracefully with appropriate error messages

### 2. Data Preprocessing
- **Whitespace Cleaning**: Strips leading/trailing whitespace from all cells
- **Forward Fill**: Fills missing Blutbuch-Nummer values from the line above
- **Column Selection**: Extracts and renames columns based on configuration mapping
- **Alternative Column Detection**: Checks for alternative column names when exact matches aren't found

### 3. Long Table Creation
- **Comprehensive Coverage**: Ensures every Blutbuch-Nummer appears at least once
- **Genetic Information Inclusion**: Includes all rows with genetic data (Gen, cDNA, Protein, Klassifizierung)
- **Empty Row Handling**: Adds entries for patients without genetic information to maintain completeness
- **Deduplication**: Removes duplicate patient-variant combinations

### 4. Data Standardization

#### Variant Classification Transformation
- Converts German/mixed classifications to standardized ACMG terminology using configurable mappings:
  - "Klasse II" variants → "Risk factor"
  - "Klasse III" variants → "VUS" (Variant of Uncertain Significance)  - "Klasse IV" variants → "Likely pathogenic"
  - "Klasse V" → "Pathogenic"
- **Special Case Handling**: Processes specific cDNA/gene combinations for missing classifications using configurable rules

### 5. Output Generation
- **Timestamped Files**: Saves processed data with unique timestamps to prevent overwrites
- **Configurable Paths**: Output directory and filename prefix defined in config.json
- **Long Table Format**: Creates one row per unique patient-variant combination
- **Comprehensive Coverage**: Includes all patients from original dataset

## Key Features

### Configuration-Based Processing
- **No Hardcoded Values**: All file paths, mappings, and rules externalized to config.json
- **Easy Customization**: Modify behavior without changing source code
- **Maintainable**: Clear separation of configuration and logic

### Data Quality Improvements
- **Whitespace Cleaning**: Automatic removal of leading/trailing spaces
- **Consistent Formatting**: Standardized output format
- **Complete Coverage**: Ensures no patients are lost during processing
- **Deduplication**: Removes redundant patient-variant combinations

### Robust Processing
- **Error Handling**: Graceful handling of missing files and columns
- **Alternative Column Detection**: Flexible column matching for varying input formats
- **Detailed Logging**: Comprehensive progress reporting and statistics

## Configuration Parameters

### File Paths
- `input_excel_file`: Path to the source Excel file
- `output_directory`: Directory for output files
- `output_filename_prefix`: Prefix for output filenames

### Column Mapping
- `column_mapping`: Maps source column names to standardized names
- `alternative_column_names`: Alternative names to check when exact matches fail
- `genetic_columns`: List of columns containing genetic information

### Classification Rules
- `klassifizierung_mapping`: Maps German classifications to ACMG terms
- `special_variant_rules`: Rules for specific cDNA/gene combinations

### Processing Options
- `clean_whitespace`: Enable/disable whitespace cleaning
- `fill_missing_blutbuch_nummer`: Enable/disable forward filling
- `include_all_blutbuch_nummer`: Ensure all patients appear in output

## Output Format

The script generates a long-table CSV file with the following structure:
- **Blutbuch_nummer**: Patient identifier
- **Gen**: Gene name
- **cDNA**: cDNA change notation
- **Protein**: Protein change notation  
- **Klassifizierung**: Standardized variant classification

### Sample Output
```csv
Blutbuch_nummer,Gen,cDNA,Protein,Klassifizierung
LB21-1390,COL4A3,c.1183G>A het,p.Gly395Arg,Likely pathogenic
LB21-1430,PKD1,c.12061C>T het,p.Arg4021Ter,Pathogenic
LB21-1518,NPHS2,c.686G>A het,p.Arg229Gln,VUS
```

## Usage

### Prerequisites
- Python 3.x with pandas, numpy
- Excel file accessible at configured path
- `config.json` file in same directory as script

### Running the Script
```bash
python nephro_reports_processor_excel_only.py
```

### Configuration
1. Edit `config.json` to match your environment:
   - Update `input_excel_file` path
   - Modify column mappings if needed
   - Adjust classification rules as required

2. Ensure the input file exists and is accessible

## Output Statistics
The script provides detailed logging including:  
- Configuration loading status
- Input file statistics (rows, columns)
- Processing step results
- Whitespace cleaning results
- Missing value filling statistics  
- Long table creation metrics
- Classification transformation results
- Final output file location and statistics

## Dependencies
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical operations  
- **json**: Configuration file parsing
- **os**: File system operations
- **datetime**: Timestamp generation

## Error Handling
- **Missing Config**: Clear error if config.json not found
- **Missing Input File**: Descriptive error with path information
- **Missing Columns**: Warnings for missing expected columns
- **Processing Errors**: Graceful handling with informative messages
