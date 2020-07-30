from main import chn_get_vectors_fast,vector_pool_hier,create_sum_vector
from tqdm import tqdm
import numpy as np
import time
import pickle
import os
import scipy
import matplotlib.pyplot as plt
import sys
import pickle
import re
import os
import json
from fasttext import FastVector
import main
import faiss
import nmslib
import h5py
import multiprocessing
import psutil

path = "/mnt/output_parallel/chn_bench/"

# segmentdict = {}
skip_gap = 1
windowsize = 6
def get_offset(string,word,previous_offset):
    word = word.replace('-','')[:1] # this is for tibetan merged words
    wlen = len(word)
    offset = -1
    for c in range(previous_offset,previous_offset + len(string)+5):
        window = string[c:c+wlen]
        if window == word:
            offset = c
            break
    if offset == -1:
        print(string)
        print(word)
        print(previous_offset)
    return offset

def read_file(filename):
    print("NOW PROCESSING: " + filename)
    chnfile = open(filename,"rb")
    chnweights = []
    chnvectors = []
    chnwords = []
    filename_short = re.sub(".*/","",filename).split(':')[0]
    for line in chnfile:
        line = line.decode('utf8',errors='ignore').strip('\n')
        #line = line.strip('\n')        
        #print(line)
        line_length = len(line)
        if len(line.split('\t')) >= 3:            
            current_id,unstripped,stripped = line.split('\t')
            unstripped = unstripped.strip()
            current_words = stripped.split()
            for i in range(0,len(current_words)):
                # we need to do this in order to avoid the annoying situation that a sentence just consisting of the same characters will break the offset calculation
                chnvectors.append(chn_get_vectors_fast(current_words[i])[0])
                chnwords.append([filename_short,current_id,current_words[i],unstripped])
    sumvectors = []
    for c in range(0,len(chnvectors),skip_gap):
        sumvectors.append(vector_pool_hier(chnvectors[c:c+windowsize]))
        #sumvectors.append(create_sum_vector(chnvectors[c:c+windowsize]))
    print("DONE PROCESSING: " + filename)
    return [chnwords,sumvectors]

def create_data_by_fileindex(fileindex,index,search_vectors):
    print("FILEINDICIES:")
    print(fileindex[0])
    print(fileindex[1])
    #search_vectors = index.reconstruct_n(fileindex[0],(fileindex[1]-fileindex[0]))
    #return_results = index.knnQueryBatch(search_vectors,k=100,num_threads=80)
    faiss.normalize_L2(search_vectors)
    results = index.search(search_vectors[fileindex[0]:fileindex[1]], 100)
    return_results = []
    for scores,positions in zip(results[0],results[1]):
        return_results.append([positions,1-scores])
    return return_results


def split_data(wordlist):
    print("Splitting data")
    split_data = []
    last_filename = ""
    c = 0
    last_c = 0
    for entry in tqdm(wordlist):
        if entry[0] != last_filename or c == len(wordlist)-1:
            split_data.append([last_filename,last_c,c])
            last_filename = entry[0]
            last_c = c
            c += 1
        else:
            c += 1
    return split_data

def process_split_data(split_data,index,sumvectors):
    results = []
    c = 0
    for entry in tqdm(split_data):
        filename = entry[0]
        if "1558" in filename:
            index_start = entry[1]
            index_end = entry[2]                
            result = create_data_by_fileindex([index_start,index_end],index,sumvectors)
            entry.append(result)
            with open("/mnt/code/calculate-quotes/test/1558_flat_ref.pk", "wb") as pickle_file:
                pickle.dump(entry,pickle_file)


chnfiles = []
def populate_index(chnfolder):
    sumvectors = []
    chnwords = []
    list_of_ids = []
    for file in os.listdir(chnfolder):
        chnfilename = os.fsdecode(file)
        if "TEST" in chnfilename or "TEST" in chnfilename:
            chnfiles.append(chnfolder+chnfilename)
    chnfiles.sort()
    print(chnfiles)
    pool = multiprocessing.Pool(processes=80)            
    file_data = pool.map(read_file, chnfiles)
    pool.close()
    for data_entry in file_data:
        chnwords.extend(data_entry[0])
        sumvectors.extend(data_entry[1])
    print(len(chnwords))
    print(len(sumvectors))
    list_of_ids = list(range(len(sumvectors)))
    pickle.dump( chnwords, open( "/mnt/code/calculate-quotes/vectordata/chnwords_bench.p", "wb" ) )
    print("Writing vectors to disc...")
    with h5py.File('/mnt/code/calculate-quotes/vectordata/chnsumvectors_bench.h5', 'w') as hf:
        hf.create_dataset("chnsumvectors",  data=sumvectors)    
    return 1

        
def benchmark_split_data(split_data,index,ref,sumvectors):
    results = []
    ref_results = ref[3]
    c = 0
    for entry in tqdm(split_data):
        filename = entry[0]
        if "1558" in filename:
            index_start = entry[1]
            index_end = entry[2]
            old_time = time.time()
            results = create_data_by_fileindex([index_start,index_end],index,sumvectors)
            new_time = time.time()
            print("TIME FOR INDEX SEARCH:",new_time-old_time)
            count_n1 = 0
            count_n50 = 0
            for current_ref_result,current_result in zip(ref_results,results):
                ref_positions = current_ref_result[0][:50]
                current_positions = current_result[0][:100]
                if current_ref_result[0][0] == current_result[0][0]:
                    count_n1 += 1
                common_results = len(list(set(ref_positions).intersection(current_positions)))                
                count_n50 += common_results / 50
            print("PRECISION N1:",count_n1 / len(results))
            print("PRECISION N50:",count_n50/len(results))
            process = psutil.Process(os.getpid())
            print(process.memory_info().rss) 




def test_hnsw_index(sumvectors,ref_file,split_words):
    print("BUILDING HNSW INDEX")
    index = faiss.IndexHNSWFlat(100,32)
    index.verbose = True
    index.train(sumvectors)
    index.add(sumvectors)
    # faiss.write_index(index, "/mnt/code/calculate-quotes/vectordata/chn_test_index.idx")
    #index = faiss.read_index("/mnt/code/calculate-quotes/vectordata/chn_test_index.idx")
    index.verbose = True
    index.hnsw.efSearch=128 # 16 ist default, mit 256 kriegt man schon wirklich sehr gute ergebnisse

    benchmark_split_data(split_words[1:],index,ref_file,sumvectors)    

def test_pca_ivf(sumvectors,ref_file,split_words):
    #index = faiss.index_factory(100, "PCA64,IVF1000,SQ8") # this is a compressed index
    #index = faiss.index_factory(100, "OPQ64_128,IVF65536_HNSW32,PQ64") # this is a compressed index
    index = faiss.index_factory(100, "PCA64,IVF4096_HNSW32,SQ8") # this is a compressed index
    index.verbose = True
    index_ivf = faiss.extract_index_ivf(index)
    index_ivf.verbose = True
    clustering_index = faiss.index_cpu_to_all_gpus(faiss.IndexFlatL2(64))
    index_ivf.clustering_index = clustering_index
    index.train(sumvectors[:100000])
    index.add(sumvectors)
    faiss.write_index(index, "/mnt/code/calculate-quotes/vectordata/chn_test_index_ivf.idx")
    
    # this is for setting the nprobe parameter
    main_index = faiss.downcast_index(index.index)
    main_index.make_direct_map()
    main_index.nprobe = 128
    faiss.normalize_L2(sumvectors)
    benchmark_split_data(split_words[1:],index,ref_file,sumvectors)    
    

#populate_index("/mnt/data/chinese/segmented/tsv/")
#populate_index("/mnt/data/chinese/segmented/extract/")
print("LOADING FILES")
chnwords = pickle.load( open( "/mnt/code/calculate-quotes/vectordata/chnwords_bench.p", "rb" ) )
sumvectordata = h5py.File('/mnt/code/calculate-quotes/vectordata/chnsumvectors_bench.h5', 'r')
sumvectors = sumvectordata.get('chnsumvectors')
sumvectors = np.array(sumvectors).astype('float32')
faiss.normalize_L2(sumvectors)
ref_file = pickle.load(open("/mnt/code/calculate-quotes/test/1558_flat_ref.pk",'rb'))
split_words = split_data(chnwords)

#test_hnsw_index(sumvectors,ref_file,split_words)
test_pca_ivf(sumvectors,ref_file,split_words)




#index = faiss.IndexFlatIP(100)   # build the eindex
#index = faiss.IndexHNSWSQ(100, faiss.ScalarQuantizer.QT_8bit, 32)




# # #index = faiss.index_cpu_to_all_gpus(index)
# # # the next four lines are to train the index on the gpu
# index_ivf = faiss.extract_index_ivf(index)
# index_ivf.verbose = True
# clustering_index = faiss.index_cpu_to_all_gpus(faiss.IndexFlatL2(64))
# index_ivf.clustering_index = clustering_index
# # # # this is to set the efSearch value

# # #index = faiss.index_cpu_to_all_gpus(index_cpu)
# # 
# # quantizer = faiss.downcast_index(main_index)
# 


# faiss.normalize_L2(sumvectors)

# index.train(sumvectors)
# index.add(sumvectors)
#





#process_split_data(split_words[1:],index,sumvectors)


#test = pickle.load(open("/mnt/output_parallel/chn_bench/T31_T1600.pk",'rb'))

