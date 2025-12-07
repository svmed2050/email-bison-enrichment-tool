import os

# --- SETTINGS ---
# Default starting path for the File Explorer
DEFAULT_PATH = os.path.join(os.path.expanduser('~'), 'Desktop')

# Column mapping (Case insensitive search)
PERSON_FIRST_NAME_COLS = ['First Name', 'FirstName', 'First']
PERSON_LAST_NAME_COLS = ['Last Name', 'LastName', 'Last']

# UPDATED: Added 'LinkedIn Profile URL', 'Linkedin Profile Url'
PERSON_LINKEDIN_COLS = ['Person Linkedin Url', 'Personal LinkedIn', 'Linkedin', 'Person Linkedin', 'LinkedIn Profile URL', 'Linkedin Profile Url'] 

# UPDATED: Added 'Account Name'
COMPANY_NAME_COLS_CLAY = ['FINAL Company Name', 'Company Name', 'Company', 'Organization', 'Account Name', 'Account']
COMPANY_NAME_COLS_EB = ['Company', 'Company Name', 'Account', 'Account Name']
COMPANY_LINKEDIN_COLS = ['Company Linkedin Url', 'Company Linkedin', 'Organization Linkedin Url']

# Additional columns
EMAIL_COLS = ['Email', 'Work Email', 'Contact Email', 'Email Address']
TITLE_COLS = ['Title', 'Job Title', 'Position']
WEBSITE_COLS = ['Website', 'Website URL', 'Company Domain Name', 'Domain', 'Company Website']