import sys
from tqdm import tqdm as tqdm
import json
import gzip
import os
import multiprocessing
from merge_quotes_tools import add_co_value
from postprocess_quotes import postprocess_quotes_chn

lang = "chn"

def process_file(filename):
    list_of_filenames = []
    filename_shortened = filename.replace("-0.json.gz","")
    segments = []
    total_quotes = []
    for c in range(10):
        new_filename = filename_shortened + "-" + str(c) + ".json.gz"
        list_of_filenames.append(new_filename)
    for current_filename in list_of_filenames:
        if os.path.isfile(current_filename):
            print(current_filename)
            try:
                with gzip.open(current_filename,'rt') as f:
                    segments,quotes = json.load(f)
                    total_quotes.extend(quotes)
                    print("SUCCESFULLY OPENED",current_filename)

            except:
                continue
    c = 0
    new_quotes = []
    total_quotes = postprocess_quotes_chn(total_quotes)
    if len(total_quotes) > 0:
        print("calculating")
        id_head = total_quotes[0]['id'].split(':')[0].replace('_words.p','')
        main_filename = segments[0]['segnr'].split(':')[0]
        for quote in total_quotes:
            quote['id'] = id_head + ":" + str(c)
            c += 1
            par_segnr = quote['par_segnr'][0]
            current_filename = par_segnr.split(':')[0]             
            if current_filename != main_filename:
                new_quotes.append(quote)        
                # for quote in tqdm(quotes):
                #     par_segnr = quote['par_segnr'][0]
                #     current_par_category = par_segnr[0:3]
                #     if not current_par_category in list_of_pp_categories:
                #         new_quotes.append(quote)
        new_quotes = add_co_value(new_quotes)
    with open(filename_shortened +".json", 'w') as outfile:        
        json.dump([segments,new_quotes], outfile,indent=4,ensure_ascii=False)
        #os.system("pigz " + filename_shortened +".json")
def process_all(tab_folder):
    filenames = []
    for file in os.listdir(tab_folder):
        filename = os.fsdecode(file)
        if filename.endswith('-0.json.gz'):# and not os.path.isfile(tab_folder + "/" + filename.replace("-0.json.gz",".json")) and not "057-008" in filename:
            #process_file(tab_folder + "/" + filename)
            filenames.append(tab_folder+ "/" + filename)
    pool = multiprocessing.Pool(processes=12)
    quote_results = pool.map(process_file, filenames)
    pool.close()
#process_all(sys.argv[1])
process_all("/mnt/output/pli/data/folder0/")                
# test = gzip.open("/mnt/output/tib/json_unfiltered/K10acip-k_lha_sa-054-004-9.json.gz",'rt')
# segments, quotes = json.load(test)
