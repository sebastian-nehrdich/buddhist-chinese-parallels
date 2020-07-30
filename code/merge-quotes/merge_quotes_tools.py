import re
from quotes_constants import *
from Levenshtein import distance as distance

def remove_punc(string):
    result = ''
    for char in string:
        if char not in PUNC:
            result += char
    return result

def normalized_levenshtein(string1,string2):
    return 1 - distance(string1,string2)/len(string2)

def create_json_filename(filename):
    #filename = filename.replace("/tab/","/json/") # kann man leider nicht so einfach machen
    filename = filename.replace("#","_") # not really sure where this step is comming from; do we need it?
    filename = filename.replace(".tab.gz","") + ".json"
    return filename

def add_co_value(parallels):
    "this function adds the value for the co-occurrence of parallels to a parallel"
    parallels_dic_by_segnr = {}
    for parallel in parallels:
        segmentnr = parallel['root_segnr'][0]
        if segmentnr not in parallels_dic_by_segnr:
            parallels_dic_by_segnr[segmentnr] = [parallel]
        else:
            parallels_dic_by_segnr[segmentnr].append(parallel)
    for main_parallel in parallels:
        co_count = 0
        segmentnr = main_parallel['root_segnr'][0]            
        for other_parallel in parallels_dic_by_segnr[segmentnr]:
            if other_parallel['root_pos_beg'] <= main_parallel['root_pos_beg'] +2 and other_parallel['root_pos_end'] >= main_parallel['root_pos_end'] -2:
                co_count += 1
        main_parallel['co-occ'] = co_count
    return parallels
