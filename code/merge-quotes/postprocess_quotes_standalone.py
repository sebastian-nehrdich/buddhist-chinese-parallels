from quotes_constants import *
from postprocess_quotes import postprocess_quotes_tib
import sys
import gzip
import json

def process_file(filename):
    with gzip.open(filename,'rt') as f:
        segments,quotes = json.load(f)
        quotes = postprocess_quotes_tib(quotes)
        with open(filename[:-5] +"_cleaned.json", 'w') as outfile:        
            json.dump([segments,quotes], outfile,indent=4,ensure_ascii=False)

#process_file(sys.argv[1])

#process_file("/mnt/output/tib/tab/folder4/T01TD1127E.json.gz")
#process_file("/mnt/output/tib/tab/folder1/T06TD4032E-9.json.gz")
process_file("/mnt/output/tib/json/T06TD4032E.json.gz")
#process_file("/mnt/output/tib/json_gap7_final/T06D4032.json.gz")
