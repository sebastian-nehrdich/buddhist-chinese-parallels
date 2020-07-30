import multiprocessing
import gzip
import numpy as np
import pickle
import time
from tqdm import tqdm as tqdm
import re
import os
import itertools
from quotes_constants import *
from pathlib import Path
from filter_prajnaparamita import test_category_pp
from merge_quotes_algo import merge_quotes,get_data_from_quote


def process_file_words(file_words_path,windowsize):
    file_words = (pickle.load(open(file_words_path,'rb')))
    word_count = 0
    result_list = []
    for current_word in file_words:
        filename = current_word[0]
        beg_segment = current_word[1]
        if word_count+windowsize < len(file_words):
            end_segment = file_words[word_count+windowsize][1]
        else:
            end_segment = beg_segment
        unsandhied_words = [word[2].strip() for word in file_words[word_count:word_count+windowsize]]
        current_sentence = ' '.join(unsandhied_words)
        result_list.append(filename + "$" + str(word_count) + "$" + beg_segment + ";" + end_segment + "$" + current_sentence)
        word_count += 1
    return result_list

def get_average_filesize(list_of_filepaths):
    sizes = []
    for filepath in list_of_filepaths:
        sizes.append(Path(filepath).stat().st_size)
    return sum(sizes) / len(sizes)


def load_tabfiles(file_words_path,word_result,windowsize,threshold,bucket_number):
    main_path = re.sub("folder.*","",file_words_path)
    main_filename = re.sub("^.*folder./","",file_words_path)
    main_filename = main_filename.replace('_words.p','')
    count = 0
    quote_results = []
    filepath_list = []
    quotes = []
    root_segtext = []
    print("BUCKET NUMBER",bucket_number)
    if bucket_number == 11:
        while count < 10:
            current_filepath = main_path + "folder" + str(count) + "/" + main_filename + ".tab.gz"
            #quote_results.append(process_tabfile([current_filepath, word_result, windowsize,threshold]))
            filepath_list.append(current_filepath)
            count += 1
        average_size = get_average_filesize(filepath_list)
        print("AVERAGE SIZE",average_size)
        print("STARTING POOL PROCESSING")
        number_of_thread = 10
        pool = multiprocessing.Pool(processes=10,maxtasksperchild=1)    
        quote_results = pool.imap(process_tabfile, zip(filepath_list, itertools.repeat(word_result, len(filepath_list)),itertools.repeat(windowsize, len(filepath_list)),itertools.repeat(threshold, len(filepath_list))))
        pool.close()
        print("POOL PROCESSING FINISHED")
        for result in quote_results:
            root_segtext = result[0]
            quotes.extend(result[1])
    else:
        current_filepath = main_path + "folder" + str(bucket_number) + "/" + main_filename + ".tab.gz"
        #current_filepath = main_filename + ".tab.gz" # uncomment this for test runs on the _extract folder
        root_segtext,quotes = process_tabfile([current_filepath, word_result, windowsize,threshold])
        print("DONE PROCESSING TABFILE")
    return root_segtext, quotes


def process_tabfile(parameters):
    current_filepath,file_words,windowsize,threshold = parameters
    print("PROCESSING TABFILE", current_filepath)
    result_lines = []
    with gzip.open(current_filepath,'rt') as current_file:
        count = 0 
        for line in current_file:
            current_results = line.rstrip('\n').split('\t')
            current_results = list(filter(None, current_results))[:20]
            result_lines.append([file_words[count], current_results])
            count += 1
    root_segtext, quotes = transform_lines_to_list(result_lines,threshold)
    del result_lines
    quotes = merge_quotes(quotes,windowsize)
    return [root_segtext,quotes]


def transform_lines_to_list(results,threshold):
    quotes = {}
    root_segtext = []
    last_segments = ""
    for result in results:
        head = result[0].split("$")
        head_filename = head[0]
        head_position = int(head[1])
        head_segments = head[2]
        head_segments = head_segments.replace("#","_").split(';')
        head_word = head[3].split(' ')[0]
        if len(result[1]) > 0:
            for quote in result[1]:
                quote_list = quote.split("$")
                add_flag = 0
                quote_filename = quote_list[0].replace("#","_")
                if head_filename != quote_filename:
                    # this step is to filter out recursive pp-quotes
                    if test_category_pp(head_filename,quote_filename):
                        quote_position = int(quote_list[1])
                        quote_segnr = quote_list[2].split(';')
                        quote_score = float(quote_list[3])
                        if quote_filename == head_filename:                        
                            add_flag = 0                            
                        if quote_score < threshold:
                            add_flag = 1                   
                        if add_flag == 1:
                            quote = {
                                "filename": quote_filename,
                                "quote_score": [quote_score],                            
                                "quote_position_beg": quote_position,
                                "quote_position_last": quote_position,
                                "head_position_beg": head_position,
                                "head_position_last": head_position,
                                "quote_segnr":quote_segnr,
                                "position_pairs":[[quote_position,head_position]],
                                "children":[],
                                "head_segnr":head_segments}
                            if not quote_filename in quotes:
                                quotes[quote_filename] = [quote]
                            else:
                                quotes[quote_filename].append(quote)
        if head_segments[0] != last_segments: 
            root_segtext.append({
                "head_filename":head_filename.replace("#","_"),
                "head_position":head_position,
                "head_segments":head_segments})
            last_segments = head_segments[0]
    return root_segtext,quotes



def load_file(file_words_path,windowsize,threshold,bucket_number):
    print("NOW LOADING", file_words_path)
    word_result = process_file_words(file_words_path,windowsize)
    root_segtext_json, quotes = load_tabfiles(file_words_path,word_result,windowsize,threshold,bucket_number)
    return root_segtext_json,quotes


# time_before = time.time()
#root_segtext_json, quotes = load_file("/mnt/output/tib/tab/folder1/T06TD4055E_words.p",7,TIBETAN_THRESHOLD,5)
#root_segtext_json, quotes = load_file("/mnt/output/tib/tab/folder5/T06TD4064E_words.p",7,TIBETAN_THRESHOLD,1)
# time_after = time.time()
# print("CONSUMED TIME",time_after - time_before)
