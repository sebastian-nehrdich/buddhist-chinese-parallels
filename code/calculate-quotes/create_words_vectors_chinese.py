from tqdm import tqdm
from main import chn_get_vectors_fast,vector_pool_hier_weighted,read_stopwords
import numpy as np
import pickle
import re
import faiss
import os
import h5py
import multiprocessing
from random import randint

from quotes_constants import *
from numpy import save as npsave

windowsize = CHINESE_WINDOWSIZE

chn_stop =  read_stopwords(CHINESE_STOPWORDS)
def get_weight(word):
    if word in chn_stop or len(word) <=2:
        return 0.1
    else:        
        return 1
    
def read_file(filename):
    print("NOW PROCESSING: " + filename)
    chnfile = []
    with open(filename,"r") as f:
        chnfile = [line.rstrip('\n') for line in f]
    chnwords = []
    chnweights = []
    chnvectors = []
    filename_short = re.sub(".*/","",filename).replace(".tsv","")
    for line in chnfile:
        line_length = len(line.rstrip('\n'))
        if line_length > 1 and line_length < 2000:
            if len(line.split('\t')) == 3:
                current_id,unstripped,stripped_with_stopwords = line.split('\t')
                current_words = stripped_with_stopwords.strip().split(' ')
                last_word = ""
                for i in range(0,len(current_words)):
                    word = current_words[i]
                    chnwords.append([filename_short,current_id,word,unstripped])
                    chnweights.append(get_weight(word))
                    chnvectors.append(chn_get_vectors_fast(word)[0])
    sumvectors = []
    for c in range(len(chnvectors)):
         sumvectors.append(vector_pool_hier_weighted(chnvectors[c:c+windowsize],chnweights[c:c+windowsize]))
    print("DONE PROCESSING: " + filename)
    random_number = 0#randint(0,9)
    npsave(CHINESE_DATA_PATH + "folder" + str(random_number) + "/" +  filename_short + "_vectors.npy",np.array(sumvectors).astype('float32'))
    pickle.dump(chnwords,open(CHINESE_DATA_PATH + "folder" + str(random_number) + "/" + filename_short + "_words.p","wb"))
    return 1

def calculate_words_and_vectors(chnfolder):
    chnwords = []
    list_of_ids = []
    chnfiles = []
    sumvector_list = []
    for file in os.listdir(chnfolder):
        chnfilename = os.fsdecode(file)
        print(chnfilename)
        chnfiles.append(chnfolder+chnfilename)
    pool = multiprocessing.Pool(processes=16,maxtasksperchild=1)
    file_data = pool.imap(read_file, chnfiles)
    pool.close()
    test = list(file_data)


calculate_words_and_vectors(CHINESE_TSV_DATA_PATH)
