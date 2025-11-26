# --- НАСТРОЙКИ ---
# Стартовая папка для Проводника (Рабочий стол)
import os
DEFAULT_PATH = os.path.join(os.path.expanduser('~'), 'Desktop')

# Возможные названия колонок (скрипт будет искать их без учета регистра)
PERSON_FIRST_NAME_COLS = ['First Name', 'FirstName']
PERSON_LAST_NAME_COLS = ['Last Name', 'LastName']
PERSON_LINKEDIN_COLS = ['Person Linkedin Url', 'Personal LinkedIn', 'Linkedin']
COMPANY_NAME_COLS_CLAY = ['FINAL Company Name', 'Company Name', 'Company', 'Organization']
COMPANY_NAME_COLS_EB = ['Company', 'Company Name', 'Account']
COMPANY_LINKEDIN_COLS = ['Company Linkedin Url', 'Company Linkedin', 'Organization Linkedin Url']