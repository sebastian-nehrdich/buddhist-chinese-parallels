import multiprocessing
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
lang = "tib"
cutoff = 0.003
depth = 100
chunk_size = 500

multiprocessing_style = 'single'

def create_tablist(file_path,words,lang):
    print("FILENAME",file_path)    
    results = np.load(gzip.open(file_path,'rb'),allow_pickle=True)
    result_len = len(results)
    print("result len",result_len)
    pool = multiprocessing.Pool(processes=16)
    result_list = pool.imap(process_result, zip(results, itertools.repeat(lang, result_len),itertools.repeat(words, result_len)))
    pool.close()
    return result_list




def process_result(parameters):
    results,lang,words = parameters
    result_string = ''
    result_pairs = [list(pair) for pair in zip(results[1],results[0])]
    for result_pair in sorted(result_pairs):
        result_string += process_individual_result(result_pair,lang,words)
    return result_string.replace("\n"," ")

def process_individual_result(result,lang,words):
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
    result_position = result[1]
    if result[1]+windowsize < len(words):
        if result_score < cutoff and words[result[1]][0] == words[result[1]+windowsize][0]:
            current_result_unsandhied_words = [word[2].strip() for word in words[result_position:result_position+windowsize]]
            current_result_sentence = ' '.join(current_result_unsandhied_words)
            segment = []
            for c in range(windowsize):                    
                segment.append(words[result_position+c][1])
            segment = list(dict.fromkeys(segment))
            segment = ';'.join(segment)
            return "\t" + words[result_position][0] + "$" + str(result_position) + "$" + segment +  "$" + str(result_score) + "$" + current_result_sentence.strip().replace("\n"," ")
        else:
            return ""
    else:
        return ""



class create_tabfile:
    def __init__(self,main_path,lang):
        self.words = []
        self.lang = lang
        if lang == 'tib':
            self.windowsize = TIBETAN_WINDOWSIZE 
        count = 0
        while count < 10:
            print("ADDING BUCKET",count)
            wordlist_path = main_path + "folder" + str(count) + "/wordlist.p"
            self.words.append(pickle.load(open(wordlist_path,'rb')))
            count += 1
            
    def process_file_words(self,file_words_path):
        file_words = (pickle.load(open(file_words_path,'rb')))
        # current_main_bucket_number = int(re.sub(".*folder","",file_words_path)[0:1])
        # current_main_words = self.words[current_main_bucket_number]
        word_count = 0
        result_list = []
        for current_word in file_words:
            filename = current_word[0]
            beg_segment = current_word[1]
            if word_count+self.windowsize < len(file_words):
                end_segment = file_words[word_count+self.windowsize][1]
            else:
                end_segment = beg_segment
            unsandhied_words = [word[2].strip() for word in file_words[word_count:word_count+self.windowsize]]
            current_sentence = ' '.join(unsandhied_words)
            result_list.append(filename + "$" + str(word_count) + "$" + beg_segment + ";" + end_segment + "$" + current_sentence)
            word_count += 1
        return result_list

    def process_file(self,file_words_path):
        main_folder = re.sub('/folder.+','',file_words_path)
        main_filename = re.sub('.+/folder./','',file_words_path)
        main_filename = main_filename.replace('_words.p','')        
        result_list = []
        result_list = self.process_file_words(file_words_path)
        count = 0 
        numpy_filepaths = []
        numpy_results = []
        while count < 10:
            numpy_filepath = (main_folder + "/folder" + str(count) + "/" + main_filename + "_results.npy.gz")
            numpy_results.append(create_tablist(numpy_filepath,self.words[count],self.lang))
            count += 1       
        for result in numpy_results:
            result_list = [a + b for a, b in zip(result_list, result)]
        return result_list

tabfile_instance = create_tabfile("/mnt/output/tib/tab/",'tib')
test = tabfile_instance.process_file("/mnt/output/tib/tab/folder5/T06TD4064E_words.p")





    



def process_result_npys(path,lang):
    files = []
    print("STARTING")
    words = pickle.load( open(path + "wordlist.p", "rb" ) )
    for file in os.listdir(path):
        filename = os.fsdecode(file)
        if "result" in filename: #and not os.path.isfile(path+filename[:-3] + ".tab.gz") and not os.path.isfile(path+filename[:-3] + ".tab"):
            if multiprocessing_style == 'single':
                create_tabfile(filename,path,words,lang)
            else:
                files.append(path+filename)
    if multiprocessing_style == 'many':
        for c in range(0,len(files),chunk_size):
            pool = multiprocessing.Pool(processes=16,maxtasksperchild=1)
            res = pool.imap(create_tabfile, zip(files[c:c+chunk_size],itertools.repeat(lang,chunk_size)))
            pool.close()
            a = list(res)



            
#process_result_npys("/mnt/code/calculate-quotes/vectordata/tibvectors/folder0/",'tib')



