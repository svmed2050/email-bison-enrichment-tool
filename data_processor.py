import os
import pandas as pd
import glob
from urllib.parse import urlparse
import config

# --- HELPER FUNCTIONS ---

def find_column_case_insensitive(df, possible_names):
    df_cols_lower = {col.lower(): col for col in df.columns}
    for name in possible_names:
        if name.lower() in df_cols_lower: return df_cols_lower[name.lower()]
    return None

def read_file_safely(filepath):
    try: return pd.read_csv(filepath, low_memory=False)
    except Exception:
        try: return pd.read_csv(filepath, encoding='latin1', low_memory=False)
        except Exception as e:
            print(f"!!! ERROR reading file {os.path.basename(filepath)}: {e}")
            return None

def clean_match_string(text):
    """Cleans text for loose matching (names/companies)."""
    if pd.isna(text): return ""
    s = str(text).strip().split(',')[0].strip().split('(')[0].strip()
    s = s.replace('.', '').replace("'", "").replace("-", " ")
    return ' '.join(s.split()).lower()

def extract_domain(url):
    """Extracts 'google.com' from 'https://www.google.com/contact'."""
    if pd.isna(url): return ""
    url = str(url).lower().strip()
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    try:
        parsed = urlparse(url).netloc
        return parsed.replace('www.', '')
    except:
        return ""

# --- FILE LOADERS ---

def process_clay_files(folder_path):
    print("\n--- Reading Clay Folder ---")
    all_files = glob.glob(os.path.join(folder_path, "*.csv"))
    if not all_files: return pd.DataFrame()
    
    processed_dfs = []
    total_rows = 0
    
    for filename in all_files:
        df = read_file_safely(filename)
        if df is None: continue
        df.columns = df.columns.str.strip()
        print(f"File: {os.path.basename(filename)} -> {len(df)} rows")
        
        # Identify columns
        first_name = find_column_case_insensitive(df, config.PERSON_FIRST_NAME_COLS)
        last_name = find_column_case_insensitive(df, config.PERSON_LAST_NAME_COLS)
        company = find_column_case_insensitive(df, config.COMPANY_NAME_COLS_CLAY)
        person_linkedin = find_column_case_insensitive(df, config.PERSON_LINKEDIN_COLS)
        company_linkedin = find_column_case_insensitive(df, config.COMPANY_LINKEDIN_COLS)
        
        # Optional columns (Email/Title/Website) - important for Output and DNC
        email = find_column_case_insensitive(df, config.EMAIL_COLS)
        title = find_column_case_insensitive(df, config.TITLE_COLS)
        website = find_column_case_insensitive(df, config.WEBSITE_COLS)

        if not all([first_name, last_name, company, person_linkedin]):
            print(f"  -> Warning: Skipped '{os.path.basename(filename)}' (missing mandatory columns).")
            continue
            
        # Create a standardized DF
        clean_df = pd.DataFrame()
        clean_df['FirstName_std'] = df[first_name]
        clean_df['LastName_std'] = df[last_name]
        clean_df['Company_std'] = df[company]
        clean_df['PersonLinkedIn_std'] = df[person_linkedin]
        clean_df['CompanyLinkedIn_std'] = df[company_linkedin] if company_linkedin else None
        
        # Add optional columns if found
        clean_df['Email_std'] = df[email] if email else None
        clean_df['Title_std'] = df[title] if title else None
        clean_df['Website_std'] = df[website] if website else None

        processed_dfs.append(clean_df)
        total_rows += len(df)

    if not processed_dfs: return pd.DataFrame()
    print(f"Total rows loaded from Clay: {total_rows}")
    return pd.concat(processed_dfs, ignore_index=True)

def load_simple_folder(folder_path, folder_name):
    print(f"\n--- Reading {folder_name} Folder ---")
    all_files = glob.glob(os.path.join(folder_path, "*.csv"))
    if not all_files: return pd.DataFrame()
    df_list = []
    for filename in all_files:
        df = read_file_safely(filename)
        if df is not None:
            df.columns = df.columns.str.strip()
            print(f"File: {os.path.basename(filename)} -> {len(df)} rows")
            if len(df) > 0: df_list.append(df)
    return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()

# --- MAIN LOGIC ---

def save_excel(df, campaign_path, suffix):
    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_filename = f"{os.path.basename(campaign_path)}_{suffix}_{date_str}.xlsx"
    output_path = os.path.join(campaign_path, output_filename)
    try:
        df.to_excel(output_path, index=False, engine='openpyxl')
        return f"SUCCESS!\nFile saved: {output_filename}"
    except Exception as e:
        return f"!!! SAVE ERROR: {e}"

def run_enrichment_eb(campaign_path):
    """Mode 1: Enrich EB using Clay data."""
    clay_dir = os.path.join(campaign_path, "Clay")
    eb_dir = os.path.join(campaign_path, "EB")

    # 1. Prepare Clay (Source)
    df_clay = process_clay_files(clay_dir)
    if df_clay.empty: return "Error: Clay data missing or invalid."
    
    df_clay['match_key'] = (df_clay['FirstName_std'].apply(clean_match_string) + "|" + 
                            df_clay['LastName_std'].apply(clean_match_string) + "|" + 
                            df_clay['Company_std'].apply(clean_match_string))
    
    # Sort: PersonLI > CompanyLI
    df_clay.sort_values(by=['PersonLinkedIn_std', 'CompanyLinkedIn_std'], ascending=False, na_position='last', inplace=True)
    clay_lookup = df_clay.drop_duplicates(subset='match_key', keep='first')
    
    clay_lookup = clay_lookup.rename(columns={
        "PersonLinkedIn_std": "Person Linkedin Url", 
        "CompanyLinkedIn_std": "Company Linkedin Url"
    })
    print(f"Unique lookup profiles in Clay: {len(clay_lookup)}")

    # 2. Prepare EB (Target)
    df_eb = load_simple_folder(eb_dir, "EB")
    if df_eb.empty: return "Error: EB data missing."
    
    col_eb_first = find_column_case_insensitive(df_eb, config.PERSON_FIRST_NAME_COLS)
    col_eb_last = find_column_case_insensitive(df_eb, config.PERSON_LAST_NAME_COLS)
    col_eb_company = find_column_case_insensitive(df_eb, config.COMPANY_NAME_COLS_EB)
    
    if not all([col_eb_first, col_eb_last, col_eb_company]): return "Error: Missing Name/Company columns in EB."
    
    df_eb['match_key'] = (df_eb[col_eb_first].apply(clean_match_string) + "|" + 
                          df_eb[col_eb_last].apply(clean_match_string) + "|" + 
                          df_eb[col_eb_company].apply(clean_match_string))

    # 3. Merge
    print("\n--- Matching... ---")
    df_result = pd.merge(df_eb, clay_lookup[['match_key', 'Person Linkedin Url', 'Company Linkedin Url']], on='match_key', how='left')
    df_result.drop(columns=['match_key'], inplace=True)
    
    matched_count = df_result['Person Linkedin Url'].notna().sum()
    print(f"Enriched records: {matched_count} out of {len(df_result)}")

    # 4. Format Columns
    df_result.rename(columns={col_eb_first: 'First Name', col_eb_last: 'Last Name', col_eb_company: 'Company'}, inplace=True)
    
    # Ensure Email column exists in EB
    col_eb_email = find_column_case_insensitive(df_result, config.EMAIL_COLS)
    if col_eb_email: df_result.rename(columns={col_eb_email: 'Email'}, inplace=True)
    
    col_eb_title = find_column_case_insensitive(df_result, config.TITLE_COLS)
    if col_eb_title: df_result.rename(columns={col_eb_title: 'Title'}, inplace=True)

    desired_order = ['Email', 'First Name', 'Last Name', 'Person Linkedin Url', 'Title', 'Company', 'Company Linkedin Url']
    final_columns = [col for col in desired_order if col in df_result.columns]
    
    return save_excel(df_result[final_columns], campaign_path, "Enriched_EB")

def run_clay_formatting(campaign_path):
    """Mode 3: Just format Clay files to the standard Output format."""
    clay_dir = os.path.join(campaign_path, "Clay")
    
    # 1. Load Clay using the existing standardized loader
    df_clay = process_clay_files(clay_dir)
    if df_clay.empty: return "Error: Clay data missing."

    print("\n--- Formatting Clay Data ---")

    # 2. Rename standardized internal columns to Final Output names
    df_clay.rename(columns={
        'Email_std': 'Email',
        'FirstName_std': 'First Name',
        'LastName_std': 'Last Name',
        'PersonLinkedIn_std': 'Person Linkedin Url',
        'Title_std': 'Title',
        'Company_std': 'Company',
        'CompanyLinkedIn_std': 'Company Linkedin Url'
    }, inplace=True)

    # 3. Select columns in specific order
    desired_order = ['Email', 'First Name', 'Last Name', 'Person Linkedin Url', 'Title', 'Company', 'Company Linkedin Url']
    
    # Only keep columns that actually exist (in case Title or Email was missing in source)
    final_columns = [col for col in desired_order if col in df_clay.columns]

    # 4. Save
    return save_excel(df_clay[final_columns], campaign_path, "Formatted_Clay")

def run_dnc_suppression(campaign_path):
    """Mode 2: Clean Clay data by removing DNC matches."""
    clay_dir = os.path.join(campaign_path, "Clay")
    dnc_dir = os.path.join(campaign_path, "DNC")
    
    if not os.path.exists(dnc_dir): return "Error: 'DNC' folder not found in this campaign."

    # 1. Load Clay
    df_clay = process_clay_files(clay_dir)
    if df_clay.empty: return "Error: Clay data missing."
    original_count = len(df_clay)

    # 2. Load DNC
    df_dnc = load_simple_folder(dnc_dir, "DNC")
    if df_dnc.empty: return "Error: DNC folder is empty."

    print("\n--- Processing DNC Lists ---")
    dnc_companies = set()
    dnc_domains = set()

    # Find DNC columns
    col_dnc_comp = find_column_case_insensitive(df_dnc, config.COMPANY_NAME_COLS_CLAY + config.COMPANY_NAME_COLS_EB)
    col_dnc_web = find_column_case_insensitive(df_dnc, config.WEBSITE_COLS)

    if col_dnc_comp:
        # Normalize and add to set
        dnc_companies = set(df_dnc[col_dnc_comp].apply(clean_match_string).dropna().unique())
        dnc_companies.discard("")
    
    if col_dnc_web:
        # Extract domains and add to set
        dnc_domains = set(df_dnc[col_dnc_web].apply(extract_domain).dropna().unique())
        dnc_domains.discard("")

    print(f"DNC Criteria: {len(dnc_companies)} companies, {len(dnc_domains)} domains.")

    # 3. Filter Clay
    # Prepare Clay columns for checking
    df_clay['temp_comp_clean'] = df_clay['Company_std'].apply(clean_match_string)
    df_clay['temp_dom_clean'] = df_clay['Website_std'].apply(extract_domain)

    # Filtering Logic: Keep if Company NOT in DNC AND Domain NOT in DNC
    mask_safe = (
        ~df_clay['temp_comp_clean'].isin(dnc_companies) & 
        ~df_clay['temp_dom_clean'].isin(dnc_domains)
    )
    
    df_clean = df_clay[mask_safe].copy()
    removed_count = original_count - len(df_clean)
    print(f"Removed {removed_count} records found in DNC.")

    # 4. Format Output (Same columns as EB result)
    # Rename standard columns to friendly names
    df_clean.rename(columns={
        'Email_std': 'Email',
        'FirstName_std': 'First Name',
        'LastName_std': 'Last Name',
        'PersonLinkedIn_std': 'Person Linkedin Url',
        'Title_std': 'Title',
        'Company_std': 'Company',
        'CompanyLinkedIn_std': 'Company Linkedin Url'
    }, inplace=True)

    desired_order = ['Email', 'First Name', 'Last Name', 'Person Linkedin Url', 'Title', 'Company', 'Company Linkedin Url']
    final_columns = [col for col in desired_order if col in df_clean.columns]

    return save_excel(df_clean[final_columns], campaign_path, "Cleaned_NoDNC")