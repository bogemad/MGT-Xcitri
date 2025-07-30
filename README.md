# MGT-Xcitri forked from https://github.com/LanLab/MGT-local
Install a local blank version of the MGT database for Xanthomonas citri

The MGT database and associated scripts are presented here in a format that should make them installable on a local machine using docker compose. 

Docker is required to run this website.

# Installation
````
   git clone https://github.com/bogemad/MGT-Xcitri.git
   
   cd MGT-Xcitri
   
   docker compose up -d --build
````

## 1. access local mgt database site 
Access the website locally using http://localhost:8000/ by default

## 2. typing isolates
Typing of isolates is in three stages:
1. Run reads_to_alleles.py script to generate an alleles file from reads or genomes following the readme in the /MGT-Xcitri/Mgt/Mgt/MGT_processing/Reads2MGTAlleles folder
2. Upload the alleles files along with associated metadata to the local site (via a project page)
3. run the /MGT-local/Mgt/Mgt/Scripts/cron_pipeline.py script to call final alleles and MGT types (under construction, below should not work currently...)

   ````
   conda activate mgt_env
   
   cd /path/to/MGT-local/Mgt/Mgt/Scripts
   
   python cron_pipeline.py -s /path/to/settings_file.py -d Blankdb --allele_to_db --local
   ````

## 3. Database save/dump
Save (dump) the database from a MGT-Xcitri container for backup or to use on another machine.

````
cd MGT-Xcitri
./dump_db.sh                 # writes xcitri-<timestamp>.sql
````

### 4. Database load/restore
Load a previously saved database to a MGT-Xcitri container

````
cd MGT-Xcitri
./load_db.sh path-or-URL-to-dump.sql
````
