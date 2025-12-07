import os
import glob
import pandas as pd
import config
import utils

def process_clay_files(folder_path):
    """Читает и нормализует файлы из папки Clay."""
    print("\n--- Reading Clay Folder ---")
    all_files = glob.glob(os.path.join(folder_path, "*.csv"))
    if not all_files: return pd.DataFrame()
    
    processed_dfs = []
    total_rows = 0
    
    for filename in all_files:
        df = utils.read_file_safely(filename)
        if df is None: continue
        df.columns = df.columns.str.strip()
        print(f"File: {os.path.basename(filename)} -> {len(df)} rows")
        
        # Поиск колонок
        first_name = utils.find_column_case_insensitive(df, config.PERSON_FIRST_NAME_COLS)
        last_name = utils.find_column_case_insensitive(df, config.PERSON_LAST_NAME_COLS)
        company = utils.find_column_case_insensitive(df, config.COMPANY_NAME_COLS_CLAY)
        person_linkedin = utils.find_column_case_insensitive(df, config.PERSON_LINKEDIN_COLS)
        company_linkedin = utils.find_column_case_insensitive(df, config.COMPANY_LINKEDIN_COLS)
        
        email = utils.find_column_case_insensitive(df, config.EMAIL_COLS)
        title = utils.find_column_case_insensitive(df, config.TITLE_COLS)
        website = utils.find_column_case_insensitive(df, config.WEBSITE_COLS)

        if not all([first_name, last_name, company, person_linkedin]):
            print(f"  -> Warning: Skipped '{os.path.basename(filename)}' (missing mandatory columns).")
            continue
            
        clean_df = pd.DataFrame()
        clean_df['FirstName_std'] = df[first_name]
        clean_df['LastName_std'] = df[last_name]
        clean_df['Company_std'] = df[company]
        clean_df['PersonLinkedIn_std'] = df[person_linkedin]
        clean_df['CompanyLinkedIn_std'] = df[company_linkedin] if company_linkedin else None
        
        clean_df['Email_std'] = df[email] if email else None
        clean_df['Title_std'] = df[title] if title else None
        clean_df['Website_std'] = df[website] if website else None

        processed_dfs.append(clean_df)
        total_rows += len(df)

    if not processed_dfs: return pd.DataFrame()
    print(f"Total rows loaded from Clay: {total_rows}")
    return pd.concat(processed_dfs, ignore_index=True)

def load_simple_folder(folder_path, folder_name):
    """Простая загрузка всех файлов из папки (для EB и DNC)."""
    print(f"\n--- Reading {folder_name} Folder ---")
    all_files = glob.glob(os.path.join(folder_path, "*.csv"))
    if not all_files: return pd.DataFrame()
    df_list = []
    for filename in all_files:
        df = utils.read_file_safely(filename)
        if df is not None:
            df.columns = df.columns.str.strip()
            print(f"File: {os.path.basename(filename)} -> {len(df)} rows")
            if len(df) > 0: df_list.append(df)
    return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()