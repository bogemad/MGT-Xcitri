import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# CHANGE App name (usually the database name with a captial letter)
APPNAME='Xcitri'

# CHANGE Species name that you want displayed with the page.
SPECIES = 'Xanthomonas citri'

# CHANGE full path of the reference genome 
REF_GENOME = os.path.join(BASE_DIR, 'setup', 'Xcitri_inputs', 'NCBI_MSCT1_Xcmal_complete.fasta')

# CHANGE full path of the lociLocations file 
LOCI_LOC = os.path.join(BASE_DIR, 'setup', 'Xcitri_inputs', 'lociLocations_MSCT.txt')

# CHANGE full path to folder of schemes 
SCHEME_ACCESSIONS = os.path.join(BASE_DIR, 'setup', 'Xcitri_inputs', 'Schemes/')

# CHANGE number of schemes 
SCHEME_NO = 8

# CHANGE to list of ODCSLS, which is a string of numbers separated by ',' (i.e. "1,2,5,10")
ODCLS = "1,2,5,10"

# CHANGE full path to store the reference files (typically have the App name as the last part of the path)
REF_FILES = os.path.join(BASE_DIR, 'tmp_files', 'Xcitri/')

# CHANGE full path of the settings_template
SETTING_FILE=os.path.join(BASE_DIR, 'Mgt', 'Mgt', 'Mgt', 'settings_template.py')

# CHANGE full path of the root to MGT-local project 
PATH_MGT= BASE_DIR

# CHANGE to settings prefix (relative path separated by dots)
SETTINGS_PREFIX="Mgt.settings_template"

# CHANGE full path of where you want to store species specific alleles that are generated. 
REFALLELES=os.path.join(BASE_DIR, 'species_specific_alleles/')

# CHANGE superusername of the django application 
SUPERUSERNAME="Ref"

# CHANGE superuseremail of the django application 
SUPERUSEREMAIL="daniel.bogema@dpi.nsw.gov.au"
