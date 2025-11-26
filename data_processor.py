import os
import pandas as pd
import glob
import config  # Импортируем наши настройки

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
            print(f"!!! ОШИБКА чтения файла {os.path.basename(filepath)}: {e}")
            return None

def clean_match_string(text):
    if pd.isna(text): return ""
    s = str(text).strip().split(',')[0].strip().split('(')[0].strip()
    s = s.replace('.', '').replace("'", "").replace("-", " ")
    return ' '.join(s.split()).lower()

def process_clay_files(folder_path):
    print("\n--- Чтение и нормализация папки Clay ---")
    all_files = glob.glob(os.path.join(folder_path, "*.csv"))
    if not all_files: return pd.DataFrame()
    processed_dfs = []
    for filename in all_files:
        df = read_file_safely(filename)
        if df is None: continue
        df.columns = df.columns.str.strip()
        print(f"Файл: {os.path.basename(filename)} -> {len(df)} строк")
        first_name = find_column_case_insensitive(df, config.PERSON_FIRST_NAME_COLS)
        last_name = find_column_case_insensitive(df, config.PERSON_LAST_NAME_COLS)
        company = find_column_case_insensitive(df, config.COMPANY_NAME_COLS_CLAY)
        person_linkedin = find_column_case_insensitive(df, config.PERSON_LINKEDIN_COLS)
        company_linkedin = find_column_case_insensitive(df, config.COMPANY_LINKEDIN_COLS)
        if not all([first_name, last_name, company, person_linkedin]):
            print(f"  -> Предупреждение: файл '{os.path.basename(filename)}' пропущен.")
            continue
        clean_df = pd.DataFrame({'FirstName_std': df[first_name], 'LastName_std': df[last_name], 'Company_std': df[company], 'PersonLinkedIn_std': df[person_linkedin], 'CompanyLinkedIn_std': df[company_linkedin] if company_linkedin else None})
        processed_dfs.append(clean_df)
    if not processed_dfs: return pd.DataFrame()
    return pd.concat(processed_dfs, ignore_index=True)

def load_eb_files(folder_path):
    print("\n--- Чтение папки EB ---")
    all_files = glob.glob(os.path.join(folder_path, "*.csv"))
    if not all_files: return pd.DataFrame()
    df_list = []
    for filename in all_files:
        df = read_file_safely(filename)
        if df is not None:
            df.columns = df.columns.str.strip()
            print(f"Файл: {os.path.basename(filename)} -> {len(df)} строк")
            if len(df) > 0: df_list.append(df)
    return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()

def run_processing(campaign_path):
    """Главная функция, которая выполняет всю работу с данными."""
    print(f"Выбрана кампания: '{os.path.basename(campaign_path)}'")
    clay_dir = os.path.join(campaign_path, "Clay")
    eb_dir = os.path.join(campaign_path, "EB")

    df_clay = process_clay_files(clay_dir)
    if df_clay.empty: return "Ошибка: Данные в папке Clay не найдены или не обработаны."
    df_clay['match_key'] = (df_clay['FirstName_std'].apply(clean_match_string) + "|" + df_clay['LastName_std'].apply(clean_match_string) + "|" + df_clay['Company_std'].apply(clean_match_string))
    df_clay.sort_values(by=['PersonLinkedIn_std', 'CompanyLinkedIn_std'], ascending=False, na_position='last', inplace=True)
    clay_lookup = df_clay.drop_duplicates(subset='match_key', keep='first')
    clay_lookup = clay_lookup.rename(columns={"PersonLinkedIn_std": "Person Linkedin Url", "CompanyLinkedIn_std": "Company Linkedin Url"})
    print(f"Уникальных комбинаций в Clay: {len(clay_lookup)}")

    df_eb = load_eb_files(eb_dir)
    if df_eb.empty: return "Ошибка: Данные в папке EB не найдены."
    
    # Имена колонок в EB могут отличаться, поэтому ищем их гибко
    col_eb_first = find_column_case_insensitive(df_eb, config.PERSON_FIRST_NAME_COLS)
    col_eb_last = find_column_case_insensitive(df_eb, config.PERSON_LAST_NAME_COLS)
    col_eb_company = find_column_case_insensitive(df_eb, config.COMPANY_NAME_COLS_EB)
    
    if not all([col_eb_first, col_eb_last, col_eb_company]): return "Ошибка: В EB файлах нет колонок Имя/Фамилия/Компания."
    df_eb['match_key'] = (df_eb[col_eb_first].apply(clean_match_string) + "|" + df_eb[col_eb_last].apply(clean_match_string) + "|" + df_eb[col_eb_company].apply(clean_match_string))
    
    print("\n--- Поиск совпадений... ---")
    df_result = pd.merge(df_eb, clay_lookup[['match_key', 'Person Linkedin Url', 'Company Linkedin Url']], on='match_key', how='left')
    df_result.drop(columns=['match_key'], inplace=True)
    matched_count = df_result['Person Linkedin Url'].notna().sum()
    print(f"Обогащено записей: {matched_count} из {len(df_result)}")

    # --- ФИНАЛЬНАЯ СОРТИРОВКА КОЛОНОК (НОВЫЙ БЛОК) ---
    # Переименовываем колонки из EB в стандартные для удобства
    # Это нужно, если в EB файле колонка называется "Company Name", а не "Company"
    df_result.rename(columns={
        col_eb_first: 'First Name',
        col_eb_last: 'Last Name',
        col_eb_company: 'Company'
    }, inplace=True)

    desired_order = [
        'Email', 
        'First Name', 
        'Last Name', 
        'Person Linkedin Url', 
        'Title', 
        'Company', 
        'Company Linkedin Url'
    ]

    # Отбираем только те колонки из желаемого списка, что реально существуют в файле
    final_columns = [col for col in desired_order if col in df_result.columns]
    final_df = df_result[final_columns]
    # --------------------------------------------------

    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_filename = f"{os.path.basename(campaign_path)}_Enriched_ByName_{date_str}.xlsx"
    output_path = os.path.join(campaign_path, output_filename)
    try:
        final_df.to_excel(output_path, index=False, engine='openpyxl') # Сохраняем отсортированный DataFrame
        return f"УСПЕШНО!\nФайл сохранен: {output_filename}"
    except Exception as e:
        return f"!!! ОШИБКА СОХРАНЕНИЯ: {e}"