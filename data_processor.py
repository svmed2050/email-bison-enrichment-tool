import os
import pandas as pd
import config
import utils
import loaders

# --- SCENARIO 1: ENRICHMENT ---
def run_enrichment_eb(campaign_path):
    clay_dir = os.path.join(campaign_path, "Clay")
    eb_dir = os.path.join(campaign_path, "EB")

    # 1. Prepare Clay
    df_clay = loaders.process_clay_files(clay_dir)
    if df_clay.empty: return "Error: Clay data missing or invalid."
    
    df_clay['match_key'] = (df_clay['FirstName_std'].apply(utils.clean_match_string) + "|" + 
                            df_clay['LastName_std'].apply(utils.clean_match_string) + "|" + 
                            df_clay['Company_std'].apply(utils.clean_match_string))
    
    df_clay.sort_values(by=['PersonLinkedIn_std', 'CompanyLinkedIn_std'], ascending=False, na_position='last', inplace=True)
    clay_lookup = df_clay.drop_duplicates(subset='match_key', keep='first')
    
    clay_lookup = clay_lookup.rename(columns={
        "PersonLinkedIn_std": "Person Linkedin Url", 
        "CompanyLinkedIn_std": "Company Linkedin Url"
    })
    print(f"Unique lookup profiles in Clay: {len(clay_lookup)}")

    # 2. Prepare EB
    df_eb = loaders.load_simple_folder(eb_dir, "EB")
    if df_eb.empty: return "Error: EB data missing."
    
    col_eb_first = utils.find_column_case_insensitive(df_eb, config.PERSON_FIRST_NAME_COLS)
    col_eb_last = utils.find_column_case_insensitive(df_eb, config.PERSON_LAST_NAME_COLS)
    col_eb_company = utils.find_column_case_insensitive(df_eb, config.COMPANY_NAME_COLS_EB)
    
    if not all([col_eb_first, col_eb_last, col_eb_company]): return "Error: Missing Name/Company columns in EB."
    
    df_eb['match_key'] = (df_eb[col_eb_first].apply(utils.clean_match_string) + "|" + 
                          df_eb[col_eb_last].apply(utils.clean_match_string) + "|" + 
                          df_eb[col_eb_company].apply(utils.clean_match_string))

    # 3. Match
    print("\n--- Matching... ---")
    df_result = pd.merge(df_eb, clay_lookup[['match_key', 'Person Linkedin Url', 'Company Linkedin Url']], on='match_key', how='left')
    df_result.drop(columns=['match_key'], inplace=True)
    
    # Format
    df_result.rename(columns={col_eb_first: 'First Name', col_eb_last: 'Last Name', col_eb_company: 'Company'}, inplace=True)
    col_eb_email = utils.find_column_case_insensitive(df_result, config.EMAIL_COLS)
    if col_eb_email: df_result.rename(columns={col_eb_email: 'Email'}, inplace=True)
    col_eb_title = utils.find_column_case_insensitive(df_result, config.TITLE_COLS)
    if col_eb_title: df_result.rename(columns={col_eb_title: 'Title'}, inplace=True)

    desired_order = ['Email', 'First Name', 'Last Name', 'Person Linkedin Url', 'Title', 'Company', 'Company Linkedin Url']
    final_columns = [col for col in desired_order if col in df_result.columns]

    final_df = utils.remove_duplicates_by_linkedin(df_result[final_columns], 'Person Linkedin Url')
    return utils.save_excel(final_df, campaign_path, "Enriched_EB")

# --- SCENARIO 2: FORMAT CLAY ONLY ---
def run_clay_formatting(campaign_path):
    clay_dir = os.path.join(campaign_path, "Clay")
    
    df_clay = loaders.process_clay_files(clay_dir)
    if df_clay.empty: return "Error: Clay data missing."

    print("\n--- Formatting Clay Data ---")
    df_clay.rename(columns={
        'Email_std': 'Email', 'FirstName_std': 'First Name', 'LastName_std': 'Last Name',
        'PersonLinkedIn_std': 'Person Linkedin Url', 'Title_std': 'Title',
        'Company_std': 'Company', 'CompanyLinkedIn_std': 'Company Linkedin Url'
    }, inplace=True)

    desired_order = ['Email', 'First Name', 'Last Name', 'Person Linkedin Url', 'Title', 'Company', 'Company Linkedin Url']
    final_columns = [col for col in desired_order if col in df_clay.columns]

    final_df = utils.remove_duplicates_by_linkedin(df_clay[final_columns], 'Person Linkedin Url')
    return utils.save_excel(final_df, campaign_path, "Formatted_Clay")

# --- SCENARIO 3: DNC SUPPRESSION ---
def run_dnc_suppression(campaign_path):
    clay_dir = os.path.join(campaign_path, "Clay")
    dnc_dir = os.path.join(campaign_path, "DNC")
    
    if not os.path.exists(dnc_dir): return "Error: 'DNC' folder not found."

    df_clay = loaders.process_clay_files(clay_dir)
    if df_clay.empty: return "Error: Clay data missing."

    df_dnc = loaders.load_simple_folder(dnc_dir, "DNC")
    if df_dnc.empty: return "Error: DNC folder is empty."

    print("\n--- Processing DNC Lists ---")
    dnc_companies = set()
    dnc_domains = set()

    col_dnc_comp = utils.find_column_case_insensitive(df_dnc, config.COMPANY_NAME_COLS_CLAY + config.COMPANY_NAME_COLS_EB)
    col_dnc_web = utils.find_column_case_insensitive(df_dnc, config.WEBSITE_COLS)

    if col_dnc_comp:
        dnc_companies = set(df_dnc[col_dnc_comp].apply(utils.clean_match_string).dropna().unique())
        dnc_companies.discard("")
    if col_dnc_web:
        dnc_domains = set(df_dnc[col_dnc_web].apply(utils.extract_domain).dropna().unique())
        dnc_domains.discard("")

    print(f"DNC Criteria: {len(dnc_companies)} companies, {len(dnc_domains)} domains.")

    df_clay['temp_comp_clean'] = df_clay['Company_std'].apply(utils.clean_match_string)
    df_clay['temp_dom_clean'] = df_clay['Website_std'].apply(utils.extract_domain)

    mask_safe = (~df_clay['temp_comp_clean'].isin(dnc_companies) & ~df_clay['temp_dom_clean'].isin(dnc_domains))
    
    df_clean = df_clay[mask_safe].copy()
    original_count = len(df_clay)
    removed_count = original_count - len(df_clean)
    print(f"Removed {removed_count} records found in DNC.")

    df_clean.rename(columns={
        'Email_std': 'Email', 'FirstName_std': 'First Name', 'LastName_std': 'Last Name',
        'PersonLinkedIn_std': 'Person Linkedin Url', 'Title_std': 'Title',
        'Company_std': 'Company', 'CompanyLinkedIn_std': 'Company Linkedin Url'
    }, inplace=True)

    desired_order = ['Email', 'First Name', 'Last Name', 'Person Linkedin Url', 'Title', 'Company', 'Company Linkedin Url']
    final_columns = [col for col in desired_order if col in df_clean.columns]

    final_df = utils.remove_duplicates_by_linkedin(df_clean[final_columns], 'Person Linkedin Url')
    return utils.save_excel(final_df, campaign_path, "Cleaned_NoDNC")