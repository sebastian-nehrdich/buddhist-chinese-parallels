import multiprocessing
import json
import glob
import re
import os
import sys
import numpy as np
#from pathos.multiprocessing import ProcessingPool as Pool
import multiprocessing
from quotes_constants import *
import pickle
from main import tib_get_vectors_fast_from_list,skt_get_vectors_fast,tib_get_vectors_fast, predict_list_of_sentencepairs,get_sif_tib,vector_pool_hier
from tqdm import tqdm as tqdm
from Levenshtein import distance
import json
import faiss
import itertools
# bucket_path = sys.argv[1]
# main_data_path = sys.argv[2]
#lang = sys.argv[3]

words = []
path = ""
depth = 100 # 100 ist einfach zuviel....
efSearch = 16
lang = "pli"

def clean_results_by_threshold(parameters):
    scores,positions,lang = parameters
    current_positions = []
    current_scores = []
    threshold = 1
    list_of_accepted_numbers = []
    if lang == 'tib':
        threshold = TIBETAN_THRESHOLD
    if lang == 'chn':
        threshold = CHINESE_THRESHOLD        
    if lang == 'pli':
        threshold = PALI_THRESHOLD        
    for current_position,current_score in zip(positions,scores):
        if current_score < threshold:
            is_accepted_flag = 0
            for current_number in list_of_accepted_numbers:
                if abs(current_number-current_position) < 10:
                    is_accepted_flag = 1
            if is_accepted_flag == 0:
                list_of_accepted_numbers.append(current_position)
                current_positions.append(current_position)
                current_scores.append(current_score)
    return [current_positions,current_scores]

    
class calculate_all:
    def __init__(self,current_words,index,output_path,vector_path,lang,custom_word_list=0):
        self.words = current_words
        self.path = output_path
        self.vector_path = vector_path
        self.index = index
        self.index.hnsw.efSearch=efSearch
        self.lang = lang
    def process_folder(self,filepath,vector_path):
        print("FILEPATH",filepath)

        def create_data_by_vectors(vectorlist):
            faiss.normalize_L2(vectorlist)
            len_of_k = depth
            #results = self.index.knnQueryBatch(self.sumvectors[fileindex[0]:fileindex[1]],k=len_of_k,num_threads=80)            
            results = self.index.search(vectorlist, len_of_k)
            pool = multiprocessing.Pool(processes=16)
            return_results = pool.map(clean_results_by_threshold, zip(results[0],results[1],itertools.repeat(lang,len(results[0]))))
            pool.close()
            return return_results
        
        def process_filelist(filelist):
            for current_file in filelist:
                if 1==1:
                    process_file(current_file)                    
                    
        def process_file(current_file):
            filename = re.sub('.*/','',current_file)
            filename = re.sub(r'_[vw].*',r'',filename)
            vectors = np.load(open(current_file,'rb'))
            print("NOW PROCESSING",filename)
            results = create_data_by_vectors(vectors)
            np.save(self.path + filename + "_results.npy",results)
            os.system("pigz " + self.path + filename + "_results.npy")
            
        def create_filelist(filepath,vector_path):
            filelist =  glob.glob(filepath + '/**/*vectors.npy', recursive=True)
            return_list = []
            for current_file in filelist:
                if not os.path.isfile(current_file.replace("vectors.npy","results.npy.gz").replace(filepath,vector_path)):
                    return_list.append(current_file)
            return return_list
                

        filelist = create_filelist(filepath,vector_path)
        process_filelist(filelist)

def process_folder(path,vector_path,lang):
    tibwords = []
    global tibevector_list
    tibvector_list = []
    if not(os.path.isfile(path + "vectors.idx")):
        for file in os.listdir(path):
            if ".p" in file and not "wordlist" in file:
                words_file = file
                vector_file = file.replace("_words.p","") + "_vectors.npy" 
                print(words_file)
                print(vector_file)
                current_tibwords = pickle.load(open(path + words_file,'rb'))
                tibvectors = np.load(open(path + vector_file,'rb'))
                tibwords.extend(current_tibwords)
                tibvector_list.append(tibvectors)        
        tibvectors = np.concatenate(tibvector_list)
        print(len(tibwords))
        print(len(tibvectors))
        list_of_ids = list(range(len(tibvectors)))
        index = faiss.IndexHNSWFlat(100, 32)
        index.hnsw.efConstruction = 40 # 40 is default, higher = more accuracy 
        #index = faiss.index_factory(100, "OPQ64_128,IVF262144_HNSW32,PQ32") # this is a compressed index
        index.verbose = True
        faiss.normalize_L2(tibvectors)
        index.add(tibvectors)
        print("Writing wordlist")
        pickle.dump(tibwords,open(path + "wordlist.p","wb"))
        faiss.write_index(index, path + "vectors.idx")
    else:
        index = faiss.read_index(path + "vectors.idx")
        calculation = calculate_all(tibwords,index,path,vector_path,lang)
        for directory in os.listdir(vector_path):
            calculation.process_folder(vector_path + directory,path)

#process_folder(bucket_path + "/", main_data_path, lang)
        
    
#process_folder("/mnt/code/calculate-quotes/vectordata/tibvectors/folder1/","/mnt/code/calculate-quotes/vectordata/tibvectors/",lang)
process_folder("/mnt/output/pli/data/folder/","/mnt/output/pli/data/",lang)


