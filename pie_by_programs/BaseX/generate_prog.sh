#!/bin/bash
# bash script for programs data

# Needs a REST connection to BaseX


echo "### Extracting data from Gallica SRU API ###"
python3 ../SRU_prog.py -f xml -t monograph
python3 ../SRU_prog.py -f xml -t periodical

echo "### Creating BaseX databases for each digital collection ###"
python3 create_DB.py -d data/gallica_programs_full_monograph.xml -n gallica_programs_full_monograph
python3 create_DB.py -d data/gallica_programs_ocr_monograph.xml -n gallica_programs_ocr_monograph
python3 create_DB.py -d data/gallica_programs_full_periodical.xml -n gallica_programs_full_periodical
python3 create_DB.py -d data/gallica_programs_ocr_periodical.xml -n gallica_programs_ocr_periodical
