import pandas as pd
import numpy as np
import os
import json
import argparse
from datetime import datetime

# Set up command line argument parsing
parser = argparse.ArgumentParser(description='Process nephrology reports and output in CSV or Excel format')
parser.add_argument('--format', choices=['xlsx', 'csv'], default='xlsx', 
                   help='Output format: xlsx (default) or csv')
args = parser.parse_args()

# Load configuration
config_path = "config.json"
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    print("✓ Configuration loaded successfully")
except FileNotFoundError:
    print(f"❌ Error: Configuration file not found at {config_path}")
    print("Please ensure config.json exists in the same directory as this script.")
    exit(1)
except Exception as e:
    print(f"❌ Error loading configuration: {e}")
    exit(1)

print("Starting nephro reports processor for Excel data...")
print(f"Output format: {args.format.upper()}")
print("="*50)

# Main Excel file path from config
excel_file_path = config["file_paths"]["input_excel_file"]
print(f"Loading Excel file from: {excel_file_path}")

try:
    Uebersicht_Nierenfaelle = pd.read_excel(excel_file_path, dtype=config["data_types"]["excel_dtype"])
    print("✓ Loaded Uebersicht_Nierenfaelle successfully")
    print(f"  Shape: {Uebersicht_Nierenfaelle.shape}")
    print(f"  Columns available: {list(Uebersicht_Nierenfaelle.columns)}")
except FileNotFoundError:
    print(f"❌ Error: File not found at {excel_file_path}")
    print("Please verify that the file path in config.json is correct and the file exists.")
    exit(1)
except Exception as e:
    print(f"❌ Error loading Excel file: {e}")
    exit(1)

print("\nProcessing Excel data...")

# Define the required columns with possible variations from config
columns_mapping = config["column_mapping"]

# Alternative column names to check for from config
alternative_names = config["alternative_column_names"]

# Find available columns
available_columns = {}
missing_columns = []

for target_col, new_name in columns_mapping.items():
    found = False
    
    # First check exact match
    if target_col in Uebersicht_Nierenfaelle.columns:
        available_columns[target_col] = new_name
        found = True
    else:
        # Check alternative names
        if target_col in alternative_names:
            for alt_name in alternative_names[target_col]:
                if alt_name in Uebersicht_Nierenfaelle.columns:
                    available_columns[alt_name] = new_name
                    found = True
                    print(f"✓ Using '{alt_name}' for '{target_col}'")
                    break
    
    if not found:
        missing_columns.append(target_col)

if missing_columns:
    print(f"⚠ Warning: Missing columns: {missing_columns}")
    print(f"Available columns in file: {list(Uebersicht_Nierenfaelle.columns)}")

# Select only available columns and rename them
if available_columns:
    Uebersicht_Nierenfaelle_selected = Uebersicht_Nierenfaelle[list(available_columns.keys())].copy()
    Uebersicht_Nierenfaelle_selected = Uebersicht_Nierenfaelle_selected.rename(columns=available_columns)
    print(f"✓ Selected and renamed {len(available_columns)} columns")
else:
    print("❌ No required columns found!")
    exit(1)

# Clean whitespace from all cells
print("\nCleaning whitespace from all cells...")
for col in Uebersicht_Nierenfaelle_selected.columns:
    # Strip whitespace from string columns
    Uebersicht_Nierenfaelle_selected[col] = Uebersicht_Nierenfaelle_selected[col].astype(str).str.strip()
    # Convert back 'nan' strings to actual NaN values
    Uebersicht_Nierenfaelle_selected[col] = Uebersicht_Nierenfaelle_selected[col].replace('nan', np.nan)
print("✓ Cleaned whitespace from all cells")

# Special handling for Panel/Segregation column
print("\nHandling Panel/Segregation column...")
if 'Panel_oder_segregation' in Uebersicht_Nierenfaelle_selected.columns:
    # Fill empty cells in Panel/Segregation with value from above (forward fill)
    missing_before = Uebersicht_Nierenfaelle_selected['Panel_oder_segregation'].isna().sum()
    Uebersicht_Nierenfaelle_selected['Panel_oder_segregation'] = Uebersicht_Nierenfaelle_selected['Panel_oder_segregation'].ffill()
    missing_after = Uebersicht_Nierenfaelle_selected['Panel_oder_segregation'].isna().sum()
    
    print(f"✓ Filled missing Panel/Segregation values: {missing_before - missing_after} values filled")
    
    # Filter to keep only lines with "Exom/Nephro"
    rows_before = len(Uebersicht_Nierenfaelle_selected)
    Uebersicht_Nierenfaelle_selected = Uebersicht_Nierenfaelle_selected[
        Uebersicht_Nierenfaelle_selected['Panel_oder_segregation'] == "Exom/Nephro"
    ]
    rows_after = len(Uebersicht_Nierenfaelle_selected)
    
    print(f"✓ Filtered for 'Exom/Nephro' only: {rows_before - rows_after} rows removed, {rows_after} rows remaining")
else:
    print("⚠ Panel/Segregation column not found, skipping panel filtering")

print("✓ Panel/Segregation handling completed")

# Step 1: Fill missing Blutbuch-Nummer with the value from the line above
print("\nStep 1: Filling missing Blutbuch-Nummer values...")
if 'Blutbuch_nummer' in Uebersicht_Nierenfaelle_selected.columns:    # Count missing values before filling
    missing_before = Uebersicht_Nierenfaelle_selected['Blutbuch_nummer'].isna().sum()
    # Forward fill the Blutbuch-Nummer column
    Uebersicht_Nierenfaelle_selected['Blutbuch_nummer'] = Uebersicht_Nierenfaelle_selected['Blutbuch_nummer'].ffill()
    
    # Count missing values after filling
    missing_after = Uebersicht_Nierenfaelle_selected['Blutbuch_nummer'].isna().sum()
    
    print(f"✓ Filled missing Blutbuch-Nummer values: {missing_before - missing_after} values filled")
    print(f"  Total rows: {len(Uebersicht_Nierenfaelle_selected)}, Rows with Blutbuch-Nummer: {len(Uebersicht_Nierenfaelle_selected) - missing_after}")
else:
    print("❌ Blutbuch-Nummer column not found!")
    exit(1)

# Step 1.5: Fill missing AF-Nummer (MEDAT) for identical Blutbuch-Nummer values
print("\nStep 1.5: Filling missing AF-Nummer (MEDAT) values...")
if 'AF_Nummer_MEDAT' in Uebersicht_Nierenfaelle_selected.columns:
    # Count missing values before filling
    missing_before_af = Uebersicht_Nierenfaelle_selected['AF_Nummer_MEDAT'].isna().sum()
    
    # Create a mapping of Blutbuch-Nummer to AF-Nummer (MEDAT) for non-null values
    af_mapping = Uebersicht_Nierenfaelle_selected.groupby('Blutbuch_nummer')['AF_Nummer_MEDAT'].apply(
        lambda x: x.dropna().iloc[0] if not x.dropna().empty else np.nan
    ).to_dict()
    
    # Fill missing AF-Nummer values using the mapping
    mask = Uebersicht_Nierenfaelle_selected['AF_Nummer_MEDAT'].isna()
    Uebersicht_Nierenfaelle_selected.loc[mask, 'AF_Nummer_MEDAT'] = (
        Uebersicht_Nierenfaelle_selected.loc[mask, 'Blutbuch_nummer'].map(af_mapping)
    )
    
    # Count missing values after filling
    missing_after_af = Uebersicht_Nierenfaelle_selected['AF_Nummer_MEDAT'].isna().sum()
    filled_af = missing_before_af - missing_after_af
    
    print(f"✓ Filled missing AF-Nummer (MEDAT) values: {filled_af} values filled")
    print(f"  Total rows: {len(Uebersicht_Nierenfaelle_selected)}, Rows with AF-Nummer: {len(Uebersicht_Nierenfaelle_selected) - missing_after_af}")
    
    # Show some statistics about AF-Nummer coverage per Blutbuch-Nummer
    af_coverage = Uebersicht_Nierenfaelle_selected.groupby('Blutbuch_nummer')['AF_Nummer_MEDAT'].apply(
        lambda x: x.notna().any()
    ).sum()
    total_patients = Uebersicht_Nierenfaelle_selected['Blutbuch_nummer'].nunique()
    print(f"  Blutbuch-Nummer entries with AF-Nummer: {af_coverage}/{total_patients} ({af_coverage/total_patients*100:.1f}%)")
else:
    print("⚠ AF-Nummer (MEDAT) column not found, skipping AF-Nummer filling")

# Step 2: Create long table format
print("\nStep 2: Creating long table format...")

# Remove rows where all genetic information is missing
genetic_cols = config["genetic_columns"]
available_genetic_cols = [col for col in genetic_cols if col in Uebersicht_Nierenfaelle_selected.columns]

print(f"Available genetic columns: {available_genetic_cols}")

# Replace empty strings and 'nan' strings with actual NaN
for col in Uebersicht_Nierenfaelle_selected.columns:
    if col in available_genetic_cols:
        Uebersicht_Nierenfaelle_selected[col] = Uebersicht_Nierenfaelle_selected[col].replace(['', 'nan', 'NaN', 'null', 'NULL'], np.nan)

# Create a comprehensive dataset ensuring each Blutbuch-Nummer appears at least once
if available_genetic_cols:
    # First, get rows with genetic information
    has_genetic_info = Uebersicht_Nierenfaelle_selected[available_genetic_cols].notna().any(axis=1)
    rows_with_genetics = Uebersicht_Nierenfaelle_selected[has_genetic_info].copy()
    
    # Then, get unique Blutbuch-Nummer entries (including those without genetic info)
    unique_blutbuch = Uebersicht_Nierenfaelle_selected.drop_duplicates(subset=['Blutbuch_nummer'])
    
    # For Blutbuch-Nummer entries that don't have genetic info, create empty rows
    blutbuch_with_genetics = set(rows_with_genetics['Blutbuch_nummer'].unique())
    all_blutbuch = set(unique_blutbuch['Blutbuch_nummer'].unique())
    blutbuch_without_genetics = all_blutbuch - blutbuch_with_genetics
    
    if blutbuch_without_genetics:
        # Create rows for Blutbuch-Nummer without genetic info
        empty_genetic_rows = unique_blutbuch[unique_blutbuch['Blutbuch_nummer'].isin(blutbuch_without_genetics)].copy()
        print(f"✓ Found {len(blutbuch_without_genetics)} Blutbuch-Nummer entries without genetic information")
        
        # Combine rows with genetics and rows without genetics
        Uebersicht_Nierenfaelle_filtered = pd.concat([rows_with_genetics, empty_genetic_rows], ignore_index=True)
    else:
        Uebersicht_Nierenfaelle_filtered = rows_with_genetics.copy()
    
    print(f"✓ Created comprehensive dataset: {len(Uebersicht_Nierenfaelle_filtered)} rows")
    print(f"  - Rows with genetic information: {len(rows_with_genetics)}")
    print(f"  - Unique Blutbuch-Nummer entries: {Uebersicht_Nierenfaelle_filtered['Blutbuch_nummer'].nunique()}")
else:
    Uebersicht_Nierenfaelle_filtered = Uebersicht_Nierenfaelle_selected.copy()
    print("⚠ No genetic columns found, keeping all rows")

# Remove duplicates to create unique combinations
print("\nStep 3: Creating unique combinations...")
# Include AF-Nummer (MEDAT) and Panel/Segregation in the output columns if available
identifier_cols = ['Blutbuch_nummer']
if 'AF_Nummer_MEDAT' in Uebersicht_Nierenfaelle_filtered.columns:
    identifier_cols.append('AF_Nummer_MEDAT')
    print("✓ Including AF-Nummer (MEDAT) in output")

# Ensure Panel/Segregation is included in the output
if 'Panel_oder_segregation' in Uebersicht_Nierenfaelle_filtered.columns:
    if 'Panel_oder_segregation' not in identifier_cols:
        identifier_cols.append('Panel_oder_segregation')
    print("✓ Including Panel/Segregation in output")

all_cols = identifier_cols + available_genetic_cols
long_table = Uebersicht_Nierenfaelle_filtered[all_cols].drop_duplicates().reset_index(drop=True)

print(f"✓ Created long table with unique combinations: {len(long_table)} rows")
print(f"  Unique Blutbuch-Nummer values: {long_table['Blutbuch_nummer'].nunique()}")

# Display summary statistics
print("\nSummary of the long table:")
for col in all_cols:
    if col in long_table.columns:
        non_null_count = long_table[col].notna().sum()
        unique_count = long_table[col].nunique()
        print(f"  {col}: {non_null_count} non-null values, {unique_count} unique values")

# Show sample of combinations per Blutbuch-Nummer
blutbuch_counts = long_table['Blutbuch_nummer'].value_counts()
print(f"\nDistribution of combinations per Blutbuch-Nummer:")
print(f"  Mean combinations per patient: {blutbuch_counts.mean():.2f}")
print(f"  Max combinations per patient: {blutbuch_counts.max()}")
print(f"  Patients with multiple combinations: {(blutbuch_counts > 1).sum()}")

# Save results
print("\nSaving results...")
creation_date = datetime.utcnow().strftime("%Y-%m-%d")

# Create results directory if it doesn't exist
output_dir = config["file_paths"]["output_directory"]
os.makedirs(output_dir, exist_ok=True)

# Note: We'll save after applying the Klassifizierung transformations

# Also save a summary showing the first few rows of initial table
print(f"\nFirst 10 rows of the initial long table (before transformations):")
print(long_table.head(10).to_string(index=False))

# Data transformation function for Klassifizierung using config
def recode_klassifizierung(row):
    k = row['Klassifizierung']
    cDNA = row['cDNA']
    gen = row['Gen']
    
    # Load mapping from config
    mapping = config["klassifizierung_mapping"]
    
    # Check class mappings
    for class_key, class_config in mapping.items():
        if k in class_config["input_values"]:
            return class_config["output_value"]
    
    # Check special variant rules
    for rule in config["special_variant_rules"]:
        if rule["condition"] == "missing_klassifizierung_and_cdna_equals":
            if pd.isna(k) and cDNA == rule["cdna_value"]:
                return rule["output_value"]
        elif rule["condition"] == "missing_klassifizierung_and_cdna_in":
            if pd.isna(k) and cDNA in rule["cdna_values"]:
                return rule["output_value"]
        elif rule["condition"] == "missing_klassifizierung_and_gen_equals":
            if pd.isna(k) and gen == rule["gen_value"]:
                return rule["output_value"]
    
    return k

# Apply Klassifizierung recoding
print("\nApplying Klassifizierung transformations...")
if 'Klassifizierung' in Uebersicht_Nierenfaelle_filtered.columns:
    Uebersicht_Nierenfaelle_filtered['Klassifizierung'] = Uebersicht_Nierenfaelle_filtered.apply(recode_klassifizierung, axis=1)
    print("✓ Applied Klassifizierung recoding to standardize variant classifications")
else:
    print("⚠ Klassifizierung column not found, skipping recoding")

# Remove duplicates to create unique combinations
print("\nStep 4: Creating unique combinations after recoding...")
long_table_recode = Uebersicht_Nierenfaelle_filtered[all_cols].drop_duplicates().reset_index(drop=True)

print(f"✓ Created long table after recoding with unique combinations: {len(long_table_recode)} rows")
print(f"  Unique Blutbuch-Nummer values: {long_table_recode['Blutbuch_nummer'].nunique()}")

# Display summary statistics
print("\nSummary of the long table after recoding:")
for col in all_cols:
    if col in long_table_recode.columns:
        non_null_count = long_table_recode[col].notna().sum()
        unique_count = long_table_recode[col].nunique()
        print(f"  {col}: {non_null_count} non-null values, {unique_count} unique values")

# Show sample of combinations per Blutbuch-Nummer
blutbuch_counts_recode = long_table_recode['Blutbuch_nummer'].value_counts()
print(f"\nDistribution of combinations per Blutbuch-Nummer after recoding:")
print(f"  Mean combinations per patient: {blutbuch_counts_recode.mean():.2f}")
print(f"  Max combinations per patient: {blutbuch_counts_recode.max()}")
print(f"  Patients with multiple combinations: {(blutbuch_counts_recode > 1).sum()}")

# Step 5: Handle semicolon-separated values by expanding rows
print("\nStep 5: Expanding rows for semicolon-separated values...")

def expand_semicolon_rows(df):
    """
    Expand rows where cells contain semicolon-separated values.
    Creates new rows for each combination, matching values by position.
    """
    expanded_rows = []
    
    for idx, row in df.iterrows():
        # Check which columns have semicolons
        semicolon_cols = {}
        max_splits = 1
        
        for col in df.columns:
            cell_value = str(row[col]) if pd.notna(row[col]) else ''
            if ';' in cell_value:
                # Split by semicolon and strip whitespace
                split_values = [val.strip() for val in cell_value.split(';')]
                # Filter out empty strings
                split_values = [val for val in split_values if val]
                if split_values:  # Only add if there are non-empty values
                    semicolon_cols[col] = split_values
                    max_splits = max(max_splits, len(split_values))
        
        if semicolon_cols:
            # Create new rows for each split
            for i in range(max_splits):
                new_row = row.copy()
                for col in df.columns:
                    if col in semicolon_cols:
                        # Use the i-th value if available, otherwise use the last available value
                        split_values = semicolon_cols[col]
                        if i < len(split_values):
                            new_row[col] = split_values[i]
                        else:
                            # If this column has fewer values, use the last one
                            new_row[col] = split_values[-1]
                    # For columns without semicolons, keep the original value
                
                expanded_rows.append(new_row)
        else:
            # No semicolons found, keep the row as is
            expanded_rows.append(row)
    
    return pd.DataFrame(expanded_rows).reset_index(drop=True)

# Apply semicolon expansion
rows_before_expansion = len(long_table_recode)
long_table_expanded = expand_semicolon_rows(long_table_recode)
rows_after_expansion = len(long_table_expanded)

print(f"✓ Expanded semicolon-separated values:")
print(f"  Rows before expansion: {rows_before_expansion}")
print(f"  Rows after expansion: {rows_after_expansion}")
print(f"  New rows created: {rows_after_expansion - rows_before_expansion}")

# Remove any duplicate rows that might have been created
long_table_final = long_table_expanded.drop_duplicates().reset_index(drop=True)
rows_after_dedup = len(long_table_final)

if rows_after_dedup < rows_after_expansion:
    print(f"✓ Removed {rows_after_expansion - rows_after_dedup} duplicate rows after expansion")

print(f"  Final unique rows: {rows_after_dedup}")

# Save the final expanded and recoded long table
timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
filename_prefix = config["file_paths"]["output_filename_prefix"]

# Determine output file format and path
output_format = args.format
file_extension = output_format
output_path = f"{output_dir}/{filename_prefix}.{timestamp}.{file_extension}"

# Save in the requested format
if output_format == 'xlsx':
    try:
        long_table_final.to_excel(output_path, index=False, na_rep="")
        print(f"✓ Final long table (with transformations and expansions) saved to Excel file: {output_path}")
    except ImportError:
        print("❌ Error: openpyxl package required for Excel output. Installing...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
        long_table_final.to_excel(output_path, index=False, na_rep="")
        print(f"✓ Final long table (with transformations and expansions) saved to Excel file: {output_path}")
else:  # csv format
    long_table_final.to_csv(output_path, index=False, na_rep="")
    print(f"✓ Final long table (with transformations and expansions) saved to CSV file: {output_path}")

# Show first few rows of the final transformed table
print(f"\nFirst 10 rows of the final transformed and expanded long table:")
print(long_table_final.head(10).to_string(index=False))

print("\n" + "="*50)
print("✅ Script completed successfully!")
print(f"📊 Final summary:")
print(f"   - Original rows: {Uebersicht_Nierenfaelle.shape[0]}")
print(f"   - Rows with genetic info: {len(Uebersicht_Nierenfaelle_filtered)}")
print(f"   - Unique combinations (before expansion): {len(long_table_recode)}")
print(f"   - Final rows (after semicolon expansion): {len(long_table_final)}")
print(f"   - Unique patients: {long_table_final['Blutbuch_nummer'].nunique()}")
print(f"   - Output format: {output_format.upper()}")
print(f"   - Output file: {output_path}")
print("="*50)
