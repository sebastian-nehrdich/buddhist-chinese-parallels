import sys
import re
import os
import string
import json
import time
import pprint
import time
import gzip
import multiprocessing
from merge_quotes_algo import merge_quotes,get_data_from_quote
from smith_waterman import get_aligned_offsets
from postprocess_quotes import postprocess_quotes_tib,test_pattern
from get_segment_dic import get_segment_dic,extend_dic_by_tsv
from merge_quotes_tools import remove_punc,normalized_levenshtein,create_json_filename
from read_tabfiles import load_file 
from quotes_constants import *
from pathlib import Path

pp = pprint.PrettyPrinter(indent=4)

from tqdm import tqdm


#multiprocessing_style = sys.argv[2].replace('--','')
multiprocessing_style = 'multi'

#lang = sys.argv[3].replace('--','')
lang='pli'

number_of_threads = 16


max_length = 1000 # max. allowed length per quote
windowsize = 7
threshold = 0.001
min_length = 35
depth = QUERY_DEPTH
segment_dic_path = ''
#tab_folder = sys.argv[1]

max_results = 50000 # number of max results per segment
#tsv_path = '/mnt/code/calculate-quotes/test/edition_etext_7_4.tsv'
tsv_path = ''
#tab_filename = ''
tab_filename = '/mnt/output/tib/tab/T06TD4064E.tab.gz'


# when calling merge_quotes with command line parameters, we run it on single file passed via the parameters:
# if len(sys.argv) == 4:
#     lang = sys.argv[1].replace('--','')    
#     tab_filename = sys.argv[2]
#     tsv_path = sys.argv[3]
    
if lang=='skt':
    threshold = SANSKRIT_THRESHOLD
    min_length = SANSKRIT_MIN_LENGTH
    windowsize = SANSKRIT_WINDOWSIZE
    segment_dic_path = SANSKRIT_SEGMENT_DICT_PATH
if lang=='pli':
    threshold = PALI_THRESHOLD
    min_length = PALI_MIN_LENGTH
    segment_dic_path = PALI_SEGMENT_DICT_PATH
    max_results = 50
if lang=='tib':
    windowsize = TIBETAN_WINDOWSIZE
    threshold = TIBETAN_THRESHOLD    
    segment_dic_path = TIBETAN_SEGMENT_DICT_PATH
    min_length_normal = TIBETAN_MIN_LENGTH
if lang=='chn':
    min_length = CHINESE_MIN_LENGTH
    segment_dic_path = CHINESE_SEGMENT_DICT_PATH
    windowsize = CHINESE_WINDOWSIZE
    threshold = 0.004#CHINESE_THRESHOLD


segment_dic,segment_keys,segment_key_numbers,natural_keys = get_segment_dic(segment_dic_path,tsv_path)

#tab_folder = output_folder + "tab/"





def create_root_json(root_segtext):
    results = []
    last_segnr = ''
    for entry in root_segtext:
        segment_num = segment_key_numbers[entry['head_segments'][0]]
        # das hier brauchen wir um evtl. luecken zu vermeiden: 
        if segment_keys[segment_num-1] != last_segnr and len(results) > 1:            
            results.append({
                "segnr": segment_keys[segment_num-1],
                "segtext":segment_dic[segment_keys[segment_num-1]],
                "position":entry['head_position']-1,
                "lang":lang})
        results.append({
            "segnr": entry['head_segments'][0],
            "segtext":segment_dic[entry['head_segments'][0]],
            "position":entry['head_position'],
            "lang":lang})
        last_segnr = entry['head_segments'][0]
    return results

def shorten_segments(quote_offset_beg,
                     quote_offset_end,
                     root_offset_beg,
                     root_offset_end,                     
                     quote_segtext,
                     quote_segnr,
                     root_segtext,
                     root_segnr):
    acc = 0
    j = 0
    gap_len = 1
    if lang == "chn" or lang == "pli" or lang == "skt":
        gap_len = 0
    quote_offset_end_last_segment = 0
    for cquote in quote_segtext:
        if acc + len(cquote) +2  > quote_offset_end:
            quote_offset_end_last_segment = quote_offset_end - acc
            break
        acc+= len(cquote) + gap_len
        j += 1
    quote_segtext = quote_segtext[0:j+1]
    quote_segnr = quote_segnr[0:j+1]
    acc = 0
    j = 0 
    root_offset_end_last_segment = 0 
    for cquote in root_segtext:
        if acc + len(cquote) +2 > root_offset_end:
            root_offset_end_last_segment = root_offset_end - acc
            break
        acc+= len(cquote) + gap_len
        j += 1
    root_segnr = root_segnr[0:j+1]
    root_segtext = root_segtext[0:j+1]
    acc = 0
    j = 0 
    quote_offset_beg_final = 0
    for cquote in quote_segtext:
        if acc + len(cquote) +2  > quote_offset_beg:
            quote_offset_beg_final = quote_offset_beg - acc
            break
        acc+= len(cquote) + gap_len
        j += 1
    quote_segtext = quote_segtext[j:]
    quote_segnr = quote_segnr[j:]            
    acc = 0
    j = 0 
    root_offset_beg_final = 0 
    for cquote in root_segtext:
        if acc + len(cquote) + 2 > root_offset_beg:
            root_offset_beg_final = root_offset_beg - acc
            break
        acc+= len(cquote) + gap_len
        j += 1
    root_segnr = root_segnr[j:]
    root_segtext = root_segtext[j:]
    return [quote_offset_beg_final,quote_offset_end_last_segment,root_offset_beg_final,root_offset_end_last_segment,quote_segtext,quote_segnr,root_segtext,root_segnr]

def fix_list_of_segments(list_of_segments):
    list_of_segments = list(dict.fromkeys(list_of_segments))
    for segment1,segment2 in zip(list_of_segments,list_of_segments[1:]):
        if segment1 in segment_key_numbers and segment2 in segment_key_numbers:
            segment1_num = segment_key_numbers[segment1]
            segment2_num = segment_key_numbers[segment2]
            distance = segment2_num - segment1_num
            if distance > 1 and distance < 50:
                for i in range(1,distance):
                    list_of_segments.append(segment_keys[segment1_num+i])
    list_of_segments.sort(key=natural_keys)
    return list_of_segments

def get_offsets_and_fulltext(root_segtext,quote_segtext, lang):
    rootfulltext = ""
    parfulltext = ""
    if lang == "tib":
        parfulltext = ' '.join(quote_segtext)
        rootfulltext = ' '.join(root_segtext)
    else:
        parfulltext = ''.join(quote_segtext)
        rootfulltext = ''.join(root_segtext)
    if len(quote_segtext) > 10 and len(root_segtext) > 10:
        root_beginning = ''
        root_end = ''

        for segment in root_segtext[:4]:
            if lang == "tib":
                root_beginning += segment + ' '
            else:
                root_beginning += segment
        for segment in root_segtext[-4:]:
            if lang == "tib":
                root_end += segment + ' '
            else:
                root_end += segment
        par_beginning = ''
        par_end = ''
        if lang == "tib":
            par_beginning = ' '.join(quote_segtext[:4])
            par_end = ' '.join(quote_segtext[-4:])            
        else:
            par_beginning = ''.join(quote_segtext[:4])
            par_end = ''.join(quote_segtext[-4:])                    
        offsets_beg = get_aligned_offsets(root_beginning,par_beginning,lang)
        offsets_end = get_aligned_offsets(root_end,par_end,lang)
        root_offset_beg = offsets_beg[0]
        par_offset_beg = offsets_beg[2]
        root_offset_end = len(rootfulltext) - (len(root_end) - offsets_end[1])
        par_offset_end = len(parfulltext) - (len(par_end) - offsets_end[3])
        return rootfulltext, parfulltext, [root_offset_beg,root_offset_end,par_offset_beg,par_offset_end]
    else:
        new_offsets = get_aligned_offsets(rootfulltext,parfulltext,lang)
    return rootfulltext,parfulltext, new_offsets[:-1]


    
def test_quote(quote_segtext,root_segtext,quote,lang):
    if lang != "tib":
        return True 
    accepted_length = 0
    half_flag = False
    flag = False
    for segtext in quote_segtext:
        segtext_cleaned = segtext.replace("/","")
        clen = len(segtext_cleaned.split())
        if clen == 7 or clen == 9 or clen == 11:
            if test_pattern(segtext):
                half_flag = True                
    if half_flag:
        for segtext in root_segtext:
            segtext_cleaned = segtext.replace("/","")
            clen = len(segtext_cleaned.split())
            if clen == 7 or clen == 9 or clen == 11:
                if test_pattern(segtext):
                    flag = True
    if (quote['quote_position_end']-quote['quote_position_beg']) > windowsize:
    #if (quote['quote_position_end']-quote['quote_position_beg']) > windowsize-20:
        flag = True
    if "4016.3E:62b-4" in quote['quote_segnr'][0] and "195a" in quote['head_segnr'][0]:
        print("FLAG",flag)
        print(quote)
        print("QUOTE SEGTEXT",quote_segtext)
        print("ROOT SEGTEXT",root_segtext)
    return flag 
        

    
def create_quotes_json(quotes):
    results = {}
    c = 0
    for quote in quotes:
        if not 'disabled' in quote.keys() and not "T04TD3859.2E:75b-4" in quote['quote_segnr'][0]:

            quote = get_data_from_quote(quote,windowsize)
            quote_segtext = []
            root_segtext = []
            quote_segnr = fix_list_of_segments(quote['quote_segnr'])
            root_segnr = fix_list_of_segments(quote['head_segnr'])            
            quote_segnr = list(dict.fromkeys(quote_segnr))
            root_segnr = list(dict.fromkeys(root_segnr))
            for seg in quote_segnr:
                if seg in segment_dic:
                    quote_segtext.append(segment_dic[seg])
            for segment in root_segnr:
                if segment in segment_dic:
                    root_segtext.append(segment_dic[segment])
            if test_quote(quote_segtext,root_segtext,quote,lang):
                rootfulltext,parfulltext,new_offsets = get_offsets_and_fulltext(root_segtext,quote_segtext,lang)

                root_offset_beg,root_offset_end,quote_offset_beg,quote_offset_end = new_offsets
                quote_offset_beg_final,quote_offset_end_final,root_offset_beg_final,root_offset_end_final,quote_segtext,quote_segnr,root_segtext,root_segnr = shorten_segments(quote_offset_beg,quote_offset_end,root_offset_beg,root_offset_end,quote_segtext,quote_segnr,root_segtext,root_segnr)
                rootfulltext_before = rootfulltext
                parfulltext_before = parfulltext
                rootfulltext = rootfulltext[root_offset_beg:root_offset_end]                
                parfulltext = parfulltext[quote_offset_beg:quote_offset_end]
                par_cleaned = remove_punc(parfulltext)
                root_cleaned = remove_punc(rootfulltext)
                parlength = 0
                rootlength = 0 
                quote_score = 100
                add_flag = 0
                score =  0
                if len(quote_segnr) > 0 and len(root_segnr) > 0:
                    cfilename = re.sub(r":.*","",root_segnr[0]).replace('#','_')
                    current_id = cfilename + ":" + str(c)
                    c += 1
                    if lang == "tib":
                        add_flag = 1
                        parlength = len(parfulltext.replace('/','').split())
                        rootlength = len(rootfulltext.replace('/','').split())
                    if lang == "pli" or lang == "skt":
                        parlength = len(parfulltext)
                        rootlength = len(rootfulltext)
                        if parlength >= min_length and rootlength >= min_length:
                            add_flag = 1
                    if lang == "chn":
                        parlength = len(par_cleaned)
                        rootlength = len(root_cleaned)
                        if parlength >= 5 and rootlength >= 5:
                            add_flag = 1
                        if re.search(r"[0-9]",rootfulltext) or re.search(r"[0-9]",parfulltext):
                            add_flag = 0 
                    if add_flag == 1 and len(root_cleaned) > 0 and len(par_cleaned) > 0:
                        score = normalized_levenshtein(root_cleaned,par_cleaned)
                        quote_score = int(score * 100)
                        for root_segment in root_segnr:
                            parallel = {
                                "score": quote_score,                        
                                "par_length": parlength,
                                "root_length": rootlength,                        
                                "id":current_id,
                                "par_pos_beg":quote['quote_position_beg'],
                                "par_pos_end":quote['quote_position_end'],
                                "root_pos_beg":quote['head_position_beg'],
                                "root_pos_end":quote['head_position_end'],
                                "par_offset_beg": quote_offset_beg_final,
                                "par_offset_end": quote_offset_end_final,
                                "par_segnr": quote_segnr,
                                "par_segtext":quote_segtext,
                                "root_segtext":root_segtext,
                                "par_string":parfulltext,
                                "root_string":rootfulltext,
                                "root_offset_beg": root_offset_beg_final,
                                "root_offset_end": root_offset_end_final,
                                "root_segnr": root_segnr,
                                "src_lang":lang,
                                "tgt_lang":lang

                            }
                            if not root_segment in results.keys():
                                results[root_segment] = [parallel]
                            else:
                                results[root_segment].append(parallel)
    return create_final_quotes_list(results)


                
def create_final_quotes_list(quotes):
    c = 0
    list_of_quotes = []
    dict_of_used_ids = {}
    for segment in quotes.keys():
        current_quotes = quotes[segment]
        acc = []
        new_quotes = []
        for quote in current_quotes:
            if quote['par_segnr'] not in acc:
                new_quotes.append(quote)
                acc.append(quote['par_segnr'])
        current_quotes = new_quotes
        current_quotes.sort(key=lambda x: (x['score'],x['par_length'])) # we are sorting by the position values
        current_quotes = current_quotes[::-1][:max_results]
        if lang == 'tib':
            current_quotes = postprocess_quotes_tib(current_quotes)
        for quote in current_quotes:
            if quote['id'] not in dict_of_used_ids:
                list_of_quotes.append(quote)
                dict_of_used_ids[quote['id']] = ""
    # for quote in list_of_quotes:
    #     if "4064E:169a-23" in ''.join(quote['par_segnr']):
    #         print("FINAL QUOTE",quote)            
    return list_of_quotes

    
def fix_quotes_ids(quotes,cfilename):
    c = 0
    for quote in quotes:
        current_id = cfilename + ":" + str(c)
        quote['id'] = current_id
        c += 1
    return quotes

def print_quotes(quotes):
    quotes.sort(key=lambda x: (x['score']))
    for quote in quotes:
        if "0451a14" in ''.join(quote['par_segnr']):
            print("SCORE",quote['score'])        
            print("QUOTE TEXT",quote['par_string'])
            print("ROOT  TEXT",quote['root_string'])
            print(quote)

def process_file(filepath,bucket_number):
    
    print("PROCESSING",filepath)
    root_segtext, quotes = load_file(filepath,windowsize,threshold,bucket_number)
    print("LOADED file")
    root_segtext_json = create_root_json(root_segtext)
    print("CREATED ROOT JSON")
    chunksize = 1000

    quotes_chunked = []
    quote_results = []
    for x in range(0,len(quotes),chunksize):
        quotes_chunked.append(quotes[x:x+chunksize])

    time_before = time.time()    
    pool = multiprocessing.Pool(processes=number_of_threads)
    quote_results = pool.map(create_quotes_json, quotes_chunked)
    pool.close()
    return_quotes = []
    print("MERGING RESULT QUOTES")
    for result in quote_results:
        return_quotes.extend(result)
    time_after = time.time()
    print("TOTAL TIME",time_after - time_before)

    print('DONE',filepath)    
    root_segtext = list({v['segnr']:v for v in root_segtext_json}.values())
    cfilename = re.sub(r".*/","",filepath)
    return_quotes.sort(key=lambda x: (x['root_pos_beg']))
    return_quotes = fix_quotes_ids(return_quotes,cfilename)
    filename_json = filepath.replace("_words.p","")
    if bucket_number == 11:
        filename_json = filename_json + ".json"
    else:
        filename_json = filename_json + "-" + str(bucket_number) + ".json"
    print_quotes(return_quotes)
    with open(filename_json, 'w') as json_file:
        json.dump([root_segtext, return_quotes],json_file,indent=4,ensure_ascii=False)
    os.system("pigz -f " + filename_json)

def process_all(tab_folder,bucket_number=11):
    for file in tqdm(os.listdir(tab_folder)):
        filename = os.fsdecode(file)
        if filename.endswith('words.p'):# and not os.path.isfile(tab_folder + "/" + filename.replace("_words.p","") +".json.gz") and not os.path.isfile(tab_folder + "/" + filename.replace("_words.p","-" + str(bucket_number) + "") +".json.gz") and not "4104" in filename:
            #if "4064" in filename: #or "4027" in filename or "4032" in filename or "1127" in filename:
            #if  "0220" in filename:
            #if "1600" in filename:
            if 1==1:
                print(filename)
                current_filesize = Path(tab_folder+ "/" +filename).stat().st_size
                if current_filesize < 1000000000:
                    process_file(tab_folder+ "/" +filename,bucket_number)
 
process_all("/mnt/output/pli/data/folder0",0)
#process_all("/mnt/output/tib/tab/folder9",6)




# for c in range(0,10):
#     process_all(sys.argv[1],c)
# for c in range(0,10):
#     process_all("/mnt/output/chn/data/folder0",c)
            


