import os
import pandas as pd
from urllib.parse import urlparse
from datetime import datetime

def find_column_case_insensitive(df, possible_names):
    """Ищет колонку в DataFrame, игнорируя регистр."""
    df_cols_lower = {col.lower(): col for col in df.columns}
    for name in possible_names:
        if name.lower() in df_cols_lower: return df_cols_lower[name.lower()]
    return None

def read_file_safely(filepath):
    """Умное чтение CSV с перебором разделителей и кодировок."""
    separators = [',', ';', '\t', '|']
    encodings = ['utf-8', 'latin1', 'cp1252', 'utf-8-sig']

    for sep in separators:
        for enc in encodings:
            try:
                df = pd.read_csv(filepath, sep=sep, encoding=enc, low_memory=False)
                if len(df.columns) > 1: return df
            except Exception:
                continue
    
    # Fallback to python engine
    try:
        return pd.read_csv(filepath, sep=None, engine='python', encoding='utf-8', low_memory=False)
    except:
        print(f"!!! ERROR: Could not read file {os.path.basename(filepath)}")
        return None

def clean_match_string(text):
    """Очищает строку для создания ключа поиска."""
    if pd.isna(text): return ""
    s = str(text).strip().split(',')[0].strip().split('(')[0].strip()
    s = s.replace('.', '').replace("'", "").replace("-", " ")
    return ' '.join(s.split()).lower()

def extract_domain(url):
    """Извлекает домен из URL."""
    if pd.isna(url): return ""
    url = str(url).lower().strip()
    if not url.startswith(('http://', 'https://')): url = 'http://' + url
    try: return urlparse(url).netloc.replace('www.', '')
    except: return ""

def remove_duplicates_by_linkedin(df, linkedin_col_name='Person Linkedin Url'):
    """Удаляет дубликаты по LinkedIn URL."""
    if linkedin_col_name not in df.columns: return df
    initial_count = len(df)
    df_deduped = df.drop_duplicates(subset=[linkedin_col_name], keep='first')
    removed = initial_count - len(df_deduped)
    if removed > 0:
        print(f"--- Deduplication ---")
        print(f"Removed {removed} duplicates based on '{linkedin_col_name}'.")
    return df_deduped

def save_excel(df, campaign_path, suffix):
    """Сохраняет DataFrame в Excel."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_filename = f"{os.path.basename(campaign_path)}_{suffix}_{date_str}.xlsx"
    output_path = os.path.join(campaign_path, output_filename)
    try:
        df.to_excel(output_path, index=False, engine='openpyxl')
        return f"SUCCESS!\nFile saved: {output_filename}"
    except Exception as e:
        return f"!!! SAVE ERROR: {e}"