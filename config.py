import os

# --- SETTINGS ---
DEFAULT_PATH = os.path.join(os.path.expanduser('~'), 'Desktop')

# Column mapping (Case insensitive search)
PERSON_FIRST_NAME_COLS = ['First Name', 'FirstName', 'First', 'Given Name']
PERSON_LAST_NAME_COLS = ['Last Name', 'LastName', 'Last', 'Surname']

# LinkedIn Columns (Both Clay and EB variations)
PERSON_LINKEDIN_COLS = [
    'Person Linkedin Url', 'Personal LinkedIn', 'Linkedin', 'Person Linkedin', 
    'LinkedIn Profile URL', 'Linkedin Profile Url', 'LI Profile'
]

# Company Columns (Added 'Account Name' and simple 'Company')
COMPANY_NAME_COLS_CLAY = [
    'FINAL Company Name', 'Company Name', 'Company', 'Organization', 
    'Account Name', 'Account', 'Organization Name'
]
COMPANY_NAME_COLS_EB = ['Company', 'Company Name', 'Account', 'Account Name']

COMPANY_LINKEDIN_COLS = [
    'Company Linkedin Url', 'Company Linkedin', 'Organization Linkedin Url', 
    'Company LI', 'Corporate LinkedIn'
]

# Additional columns
EMAIL_COLS = ['Email', 'Work Email', 'Contact Email', 'Email Address', 'Mail']
TITLE_COLS = ['Title', 'Job Title', 'Position', 'Role']
WEBSITE_COLS = ['Website', 'Website URL', 'Company Domain Name', 'Domain', 'Company Website']