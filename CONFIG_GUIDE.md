# Configuration File Documentation

The `config.json` file contains all configurable parameters for the nephro_reports_processor_excel_only.py script.

## Configuration Sections

### 1. File Paths
```json
"file_paths": {
    "input_excel_file": "path/to/your/excel/file.xlsx",
    "output_directory": "results",
    "output_filename_prefix": "nephro_long_table_transformed"
}
```

**Parameters:**
- `input_excel_file`: Full path to the source Excel file containing nephrology data
- `output_directory`: Directory where output files will be saved
- `output_filename_prefix`: Prefix for output CSV files (timestamp will be appended)

### 2. Column Mapping
```json
"column_mapping": {
    "Source-Column-Name": "standardized_column_name"
}
```

Maps source Excel column names to standardized internal column names.

### 3. Alternative Column Names
```json
"alternative_column_names": {
    "Gen": ["Gen...17", "Gen...16", "Gen...15"]
}
```

Provides fallback column names to check when exact matches aren't found.

### 4. Classification Mapping
```json
"klassifizierung_mapping": {
    "class_2_variants": {
        "input_values": ["Klasse II (Risiko-Poly)", "Klasse II, Risk Factor"],
        "output_value": "Risk factor"
    }
}
```

Defines how to transform variant classifications from source format to standardized ACMG terminology.

### 5. Special Variant Rules
```json
"special_variant_rules": [
    {
        "condition": "missing_klassifizierung_and_cdna_equals",
        "cdna_value": "c.4523-1G>A",
        "output_value": "Likely pathogenic"
    }
]
```

Defines rules for handling specific cases where classification is missing but can be inferred from genetic data.

## Customization Guide

1. **Change Input File**: Update `input_excel_file` path to point to your Excel file
2. **Add New Classifications**: Add entries to `klassifizierung_mapping` for new variant classes
3. **Handle New Columns**: Update `column_mapping` if your Excel has different column names
4. **Add Special Cases**: Extend `special_variant_rules` for specific variants that need custom handling

## Example Modifications

### Adding a New Classification
```json
"class_1_variants": {
    "input_values": ["Klasse I", "Benign"],
    "output_value": "Benign"
}
```

### Adding a Special Case Rule
```json
{
    "condition": "missing_klassifizierung_and_gen_equals",
    "gen_value": "NEW_GENE",
    "output_value": "VUS"
}
```
