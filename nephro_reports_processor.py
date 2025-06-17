import pandas as pd
import numpy as np
import os
import re
from pathlib import Path
from datetime import datetime
import shutil
import glob

# Set working directory (using current directory)
# os.chdir("C:/projects/copy_lb_reports_to_cerkid")
print(f"Working directory: {os.getcwd()}")

# Find all PDF files in the network folders
pdf_lb = []
network_path = r"//10.28.149.154/hum/HGDiag/Befunde/Nephro/20[0-9][0-9]"
print(f"Searching for PDF files in: {network_path}")

try:
    for year_folder in glob.glob(network_path):
        print(f"Found year folder: {year_folder}")
        pdf_files = list(Path(year_folder).rglob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files in {year_folder}")
        pdf_lb.extend(pdf_files)
    
    print(f"Total PDF files found: {len(pdf_lb)}")
    
    if len(pdf_lb) == 0:
        print("Warning: No PDF files found. This might be due to network access issues.")
        print("Creating empty DataFrame to continue script execution...")
        pdf_lb = pd.DataFrame({'value': []})
    else:
        pdf_lb = pd.DataFrame({'value': [str(f) for f in pdf_lb]})
        
except Exception as e:
    print(f"Error accessing network path: {e}")
    print("Creating empty DataFrame to continue script execution...")
    pdf_lb = pd.DataFrame({'value': []})

# Process PDF file paths
def get_subfolder_and_file(path):
    match = re.sub(r"//10.28.149.154/hum/HGDiag/Befunde/Nephro/20[0-9][0-9]/", "", path)
    return match

pdf_reports = pdf_lb.copy()

if len(pdf_reports) > 0:
    pdf_reports['subfolder_and_file'] = pdf_reports['value'].apply(get_subfolder_and_file)
    pdf_reports = pdf_reports[~pdf_reports['subfolder_and_file'].str.contains("Falscher", na=False)]
    pdf_reports[['subfolder', 'file']] = pdf_reports['subfolder_and_file'].str.split("/", 1, expand=True)
    pdf_reports['Blutbuch_Nummer'] = pdf_reports['subfolder'].str.replace(r"[_| ].+", "", regex=True)
    pdf_reports = pdf_reports[pdf_reports['file'].str.contains("[Bb]efund", na=False)]
    pdf_reports = pdf_reports[~pdf_reports['file'].str.contains("Laufzettel", na=False)]
    print(f"Processed PDF reports: {len(pdf_reports)} files")
else:
    print("No PDF files to process")
    # Create empty DataFrame with required columns
    pdf_reports = pd.DataFrame(columns=['value', 'subfolder_and_file', 'subfolder', 'file', 'Blutbuch_Nummer'])

# Load Excel files
try:
    Einsender_charite_fixed = pd.read_excel("data/Einsender_charite.fixed.xlsx")
    print("Loaded Einsender_charite_fixed successfully")
except FileNotFoundError:
    print("Warning: Einsender_charite.fixed.xlsx not found, creating empty DataFrame")
    Einsender_charite_fixed = pd.DataFrame()

try:
    Sub_panel_fixed = pd.read_excel("data/Sub_panel.fixed.xlsx")
    print("Loaded Sub_panel_fixed successfully")
except FileNotFoundError:
    print("Warning: Sub_panel.fixed.xlsx not found, creating empty DataFrame")
    Sub_panel_fixed = pd.DataFrame()

try:
    Uebersicht_Nierenfaelle = pd.read_excel(r"H:\HGDiag\Befunde\Nephro\Übersicht_Nierenfälle.xlsx", dtype=str)
    print("Loaded Uebersicht_Nierenfaelle successfully")
    print(f"Shape: {Uebersicht_Nierenfaelle.shape}")
    print(f"Columns: {list(Uebersicht_Nierenfaelle.columns)}")
except FileNotFoundError:
    print("Error: Uebersicht_Nierenfälle.xlsx not found at H:/HGDiag/Befunde/Nephro/")
    exit(1)
except Exception as e:
    print(f"Error loading Excel file: {e}")
    exit(1)

# Fill down columns
Uebersicht_Nierenfaelle = Uebersicht_Nierenfaelle.fillna(method='ffill')

# Select and rename columns
columns_to_keep = {
    'Geburtsjahr': 'Geburtsjahr',
    'Eingang/Freigabe': 'Eingang',
    'Geschlecht': 'Geschlecht',
    'einsender': 'Einsender',
    'Blutbuch-Nummer': 'Blutbuch_nummer',
    'Index-Nummer': 'Index_nummer',
    'AF-Nummer (MEDAT)': 'AF_nummer',
    'Panel / Segregation': 'Panel_oder_segregation',
    'Sub-Panel': 'Sub_panel',
    'Klinik': 'Klinik',
    'Befunddatum': 'Befunddatum',
    'Datenübertragung ans CUBI gewünscht und korrekt ausgefüllt, Datum der Übermittelung wenn erledigt !': 'Datatransfer',
    'Befunder': 'Befunder',
    'Bemerkung': 'Bemerkung',
    'Gen...17': 'Gen',
    'cDNA': 'cDNA',
    'Protein...19': 'Protein',
    'Klassifizierung': 'Klassifizierung'
}
Uebersicht_Nierenfaelle = Uebersicht_Nierenfaelle[list(columns_to_keep.keys())]
Uebersicht_Nierenfaelle = Uebersicht_Nierenfaelle.rename(columns=columns_to_keep)

# Data cleaning and recoding
def recode_datatransfer(x):
    return "yes" if x in ["X", "x"] else "no"

def recode_befunder(x):
    if x in ["Johannes", "Johannes/Angela", "Grünhagen ablegen validieren", "in Arbeit Grünhagen", "Privat KVA erstellt am 13.12", "Grünhangen"]:
        return "Grünhagen"
    elif x in ["Angela/ Johannes", "Angela/Johannes", "Angela", "Abad/Grünhagen", "Privat KVA erstellt am 13.12."]:
        return "Abad"
    else:
        return x

def recode_einsender(x):
    mapping = {
        "Bachmann": "Bachmann Charité",
        "Bachmann / Weber / Seelow": "Bachmann Charité",
        "Canaan-Kühl": "Canaan-Kühl Charité",
        "Grün Charité MVZ, gehört zum Cerkid": "Grün Charité",
        "Hawkins": "Hawkins Charité",
        "Liefeldt Charite": "Liefeldt Charité",
        "Rehfeldt Charié": "Rehfeldt Charité",
        "Schreiber Charié": "Schreiber Charité",
        "Schreiber": "Schreiber Charité",
        "Ulrike Weber": "Weber Charité",
        "Weber": "Weber Charité",
        "Ulrike Weber AGZ Charité": "Weber Charité",
        "Zöllner MVZ der Charité": "Zöllner Charité",
        "ZukunftCharité": "Zukunft Charité",
        "Berns Charité Station 32i": "Berns Charité",
        "Sima Charité": "Canaan-Kühl Charité",
        "Otto Charité": "Grün (ehem. Otto) Charité"
    }
    return mapping.get(x, x)

def recode_outcome(row):
    bemerkung = row['Bemerkung']
    gen = row['Gen']
    if pd.isna(bemerkung) and not pd.isna(gen):
        return "positiv"
    if pd.isna(bemerkung) and pd.isna(gen):
        return "in_process"
    if isinstance(bemerkung, str):
        if re.search("negativ|neagiv|neagtiv", bemerkung):
            return "negativ"
        if re.search("positiv|Deletion COL4A4", bemerkung):
            return "positiv"
    return bemerkung

def recode_klassifizierung(row):
    k = row['Klassifizierung']
    cDNA = row['cDNA']
    gen = row['Gen']
    if k in ["Klasse II (Risiko-Poly)", "Klasse II, Risk Factor"]:
        return "Risk factor"
    if k in ["Klasse III", "Klasse III-IV", "Klasse III (heiß)", "Klasse III (kalt)", "Klasse III funct. Poly", "Klasse IIII", "Klasse III-II"]:
        return "VUS"
    if k in ["Klasse IV", "Klasse IV - V", "Klasse IV - V?", "KlasseIV"]:
        return "Likely pathogenic"
    if k == "Klasse V":
        return "Pathogenic"
    if pd.isna(k) and cDNA == "c.4523-1G>A":
        return "Likely pathogenic"
    if pd.isna(k) and cDNA in ["CFHR1 und CFHR3", "c.9661dup"]:
        return "Risk factor"
    if pd.isna(k) and cDNA == "c.110A>C":
        return "VUS"
    if pd.isna(k) and gen == "HBA1/HBA2 Cluster Deletion berichtet":
        return "VUS"
    if pd.isna(k) and cDNA == "c.647C>T hom":
        return "Likely pathogenic"
    return k

def recode_gen(x):
    mapping = {
        "CCDC41(CEP83)": "CEP83",
        "CFHR1 CFHR3 homozygote Deletion": "CFHR1",
        "CFHR1 und CFHR3": "CFHR1",
        "Deletion homozygot": "CFHR1",
        "HBA1/HBA2 Cluster Deletion berichtet": "HBA1",
        "MT-ND5 (nicht bestätigt!)": "MT-ND5",
        "negativ": "",
        "SCNN1G [Ex2]": "SCNN1G"
    }
    return mapping.get(x, x)

Uebersicht_Nierenfaelle['Datatransfer'] = Uebersicht_Nierenfaelle['Datatransfer'].apply(recode_datatransfer)
Uebersicht_Nierenfaelle['Befunder'] = Uebersicht_Nierenfaelle['Befunder'].apply(recode_befunder)
Uebersicht_Nierenfaelle['Einsender'] = Uebersicht_Nierenfaelle['Einsender'].apply(recode_einsender)
Uebersicht_Nierenfaelle['Outcome'] = Uebersicht_Nierenfaelle.apply(recode_outcome, axis=1)
Uebersicht_Nierenfaelle['Klassifizierung'] = Uebersicht_Nierenfaelle.apply(recode_klassifizierung, axis=1)
Uebersicht_Nierenfaelle['Gen'] = Uebersicht_Nierenfaelle['Gen'].apply(recode_gen)
Uebersicht_Nierenfaelle['Gen'] = Uebersicht_Nierenfaelle['Gen'].replace("", np.nan)

# Join with curated tables
Uebersicht_Nierenfaelle_join = Uebersicht_Nierenfaelle.merge(Einsender_charite_fixed, on="Einsender", how="left")
Uebersicht_Nierenfaelle_join = Uebersicht_Nierenfaelle_join.merge(Sub_panel_fixed, on="Sub_panel", how="left")
if 'replace' in Uebersicht_Nierenfaelle_join.columns:
    Uebersicht_Nierenfaelle_join['Sub_panel'] = Uebersicht_Nierenfaelle_join['replace']
    Uebersicht_Nierenfaelle_join = Uebersicht_Nierenfaelle_join.drop(columns=['replace'])

# Filter for cases from Charité with Exome which are finished
Uebersicht_Nierenfaelle_filtered = Uebersicht_Nierenfaelle_join[
    (Uebersicht_Nierenfaelle_join['Panel_oder_segregation'] == "Exom/Nephro") &
    (Uebersicht_Nierenfaelle_join['Einsender'].str.contains("Charité", na=False)) &
    (~Uebersicht_Nierenfaelle_join.get('Standort', pd.Series("")).str.contains("Other", na=False)) &
    (Uebersicht_Nierenfaelle_join['Outcome'] != "in_process")
]

# Summarize the table
group_cols = ['Geschlecht', 'Blutbuch_nummer']
agg_dict = {
    'Einsender': lambda x: " | ".join(x.unique()),
    'Eingang': 'max',
    'Sub_panel': lambda x: " | ".join(x.unique()),
    'Standort': lambda x: " | ".join(x.unique()),
    'Datatransfer': lambda x: " | ".join(x.unique()),
    'Befunder': lambda x: " | ".join(x.unique()),
    'Gen': lambda x: " | ".join(x.unique()),
    'Outcome': 'max',
    'Klassifizierung': lambda x: " | ".join(x.unique())
}
Uebersicht_Nierenfaelle_filtered_summarized = Uebersicht_Nierenfaelle_filtered.groupby(group_cols).agg(agg_dict).reset_index()
Uebersicht_Nierenfaelle_filtered_summarized['Panels_requested_count'] = Uebersicht_Nierenfaelle_filtered_summarized['Sub_panel'].str.count("; ") + 1
Uebersicht_Nierenfaelle_filtered_summarized['Panels_requested'] = np.where(
    Uebersicht_Nierenfaelle_filtered_summarized['Panels_requested_count'] > 1, "multiple", "single"
)

# Filter for cases after 2022-01-01
Uebersicht_Nierenfaelle_filtered_summarized_afterKUE = Uebersicht_Nierenfaelle_filtered_summarized[
    Uebersicht_Nierenfaelle_filtered_summarized['Eingang'] >= '2022-01-01'
][['Blutbuch_nummer']]

# Filter PDF table for transfer
pdf_reports_for_transfer = pdf_reports[
    pdf_reports['Blutbuch_Nummer'].isin(Uebersicht_Nierenfaelle_filtered_summarized_afterKUE['Blutbuch_nummer'])
]

# Copy files
def copy_file(row):
    try:
        dest = r"S:/C13/CeRKiD/Daten/CeRKiD_Genetik Befunde"
        shutil.copy(row['value'], dest)
        return True
    except Exception as e:
        return False

pdf_reports_for_transfer['transfered'] = pdf_reports_for_transfer.apply(copy_file, axis=1)

# Creation date
creation_date = datetime.utcnow().strftime("%Y-%m-%d")

# Create summary table
pdf_reports_for_transferd_summarized = pdf_reports_for_transfer.groupby('Blutbuch_Nummer').agg({
    'value': lambda x: "; ".join(x),
    'transfered': lambda x: "; ".join(map(str, x))
}).reset_index()
pdf_reports_for_transferd_summarized['date_tranfered'] = creation_date

# Save as CSV
output_path = f"results/pdf_reports_for_transferd_summarized.{creation_date}.csv"
pdf_reports_for_transferd_summarized.to_csv(output_path, index=False, na_rep="NULL")

print(f"Script completed successfully! Output saved to: {output_path}")
