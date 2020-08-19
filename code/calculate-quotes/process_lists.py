import multiprocessing
import sys
import gzip
import numpy as np
import pickle
from tqdm import tqdm as tqdm
import re
import os
import itertools
from quotes_constants import * 
words = []
path = ""
windowsize = 6
lang = "chn"
cutoff = 0.003
depth = 100
chunk_size = 500

multiprocessing_style = 'many'

# if lang == "tib":
#     words = pickle.load( open( "vectordata/tibwords.p", "rb" ) )
#     path = "/mnt/output_parallel/tibetan/raw/"
#     depth = 100
#     windowsize = 7
#     skip_gap =1
#     cutoff = 0.02
#     lang = "tib"

# if lang == "skt":
#     words = pickle.load( open( "vectordata/sktwords.p", "rb" ) )
#     path = "/mnt/output_parallel/sanskrit/raw/"
#     windowsize = 5
#     skip_gap = 1
#     cutoff = 0.3
#     lang = "skt"

# if lang == "pali":
#     chunk_size = 25000
#     words = pickle.load( open( PALI_WORDS_PATH, "rb" ) )
#     path = PALI_OUTPUT_FOLDER + "raw/"
#     windowsize = PALI_WINDOWSIZE
#     skip_gap = 1
#     cutoff = PALI_THRESHOLD
#     lang = "pali"

    
# if lang == "chn":
#     words = pickle.load( open( "vectordata/chnwords_bench.p", "rb" ) )
#     path = "/mnt/output_parallel/chinese/"
#     depth = 100
#     windowsize = 5
#     skip_gap = 1
#     cutoff = 0.04
#     lang = "chn"
    

def create_tabfile(parameters):
    filename,current_path,lang = parameters
    print("FILENAME",filename)    
    results = np.load(gzip.open(current_path + filename,'rb'),allow_pickle=True)
    filename_short = re.sub('_result.*','',filename)
    result_len = len(results)
    print("result len",result_len)
    # pool = multiprocessing.Pool(processes=16)
    # result_strings = pool.map(process_result, zip(results, itertools.repeat(lang, result_len)))
    # pool.close()
    result_strings = (process_result([x,lang]) for x in results)
    result_string = "\n".join(result_strings)
    #print(result_string)
    print("FILENAME",filename)
    if len(filename) > 1:
        print("now writing",current_path + filename_short + ".tab.gz")
        with gzip.open(current_path + filename_short + ".tab.gz", "wb") as text_file:
            text_file.write(result_string.encode())
    #os.system("rm " + current_path + filename)
    return 1

def process_result(parameters):
    results,lang = parameters
    result_string = ''
    result_pairs = [list(pair) for pair in zip(results[1],results[0])]
    list_of_accepted_numbers = []
    for result_pair in sorted(result_pairs):
        is_in_list_flag = 0 
        current_position, current_result_string = process_individual_result(result_pair,lang)
        for accepted_number in list_of_accepted_numbers:
            if abs(accepted_number-current_position) < 10:
                is_in_list_flag = 1
        if is_in_list_flag == 0:
            result_string += current_result_string
            
    return result_string.replace("\n"," ")

def process_individual_result(result,lang):
    cutoff = 1
    windowsize = 6
    if lang == "tib":
        cutoff = TIBETAN_THRESHOLD
        windowsize = TIBETAN_WINDOWSIZE
    if lang == "chn":
        cutoff = CHINESE_THRESHOLD
        windowsize = CHINESE_WINDOWSIZE
    if lang == "skt":
        cutoff = SANSKRIT_THRESHOLD
        windowsize = SANSKRIT_WINDOWSIZE
    if lang == "pli":
        cutoff = PALI_THRESHOLD
        windowsize = PALI_WINDOWSIZE
    result_score = result[0]
    result_position = int(result[1])
    if result[1]+windowsize < len(words):
        # print("RESULT",result)
        # print("RESULT POSITION",result_position)
        if result_score < cutoff and words[int(result[1])][0] == words[int(result[1])+windowsize][0]:
            current_result_unsandhied_words = [word[2].strip() for word in words[result_position:result_position+windowsize]]
            current_result_sentence = ' '.join(current_result_unsandhied_words)
            segment = []
            for c in range(windowsize):                    
                segment.append(words[result_position+c][1])
            segment = list(dict.fromkeys(segment))
            segment = ';'.join(segment)
            return [result_position, "\t" + words[result_position][0] + "$" + str(result_position) + "$" + segment +  "$" + str(result_score) + "$" + current_result_sentence.strip().replace("\n"," ")]
        else:
            return [0, ""]
    else:
        return [0, ""]

folderpath = sys.argv[1] + "/"
lang = sys.argv[2]
multiprocessing_style = 'many'
chunk_size = 100
words = pickle.load( open(folderpath + "wordlist.p", "rb" ) )


def process_result_npys(path,lang):
    files = []
    print("STARTING")
    for file in os.listdir(path):
        filename = os.fsdecode(file)
        filename_short = re.sub('_result.*','',filename)
        if "result" in filename and not "tab.gz" in filename and not os.path.isfile(path+filename_short + ".tab.gz") and not os.path.isfile(path+filename[:-3] + ".tab"):
            if multiprocessing_style == 'single':
                create_tabfile([filename,path,lang])
            else:
                files.append(filename)
    if multiprocessing_style == 'many':
        print("starting multiprocessing")
        for c in range(0,len(files),chunk_size):
            print("CHUNK",c)
            pool = multiprocessing.Pool(processes=16,maxtasksperchild=1)
            res = pool.map(create_tabfile, zip(files[c:c+chunk_size],itertools.repeat(path,chunk_size),itertools.repeat(lang,chunk_size)))
            pool.close()






process_result_npys(folderpath,lang)



