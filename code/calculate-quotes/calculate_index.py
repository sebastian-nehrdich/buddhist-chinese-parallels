from numpy import load as npload
from quotes_constants import *
from tqdm import tqdm as tqdm 
import faiss
import os
import random
depth = 200
def train_index(vectors_path,output_path):
    "This trains an index on the GPU based on the files in vectors_path and writes it to disc afterwards."
    file_list = []
    sumvectors = []
    for filename in tqdm(os.listdir(vectors_path)):
        file_list.append(filename)
    random.shuffle(file_list)
    for current_filename in tqdm(file_list[:depth]):
        print(vectors_path + current_filename)
        sumvectors.extend(npload(vectors_path + current_filename))


        
    # tibwords = []
    # list_of_ids = []
    # tibfiles = []
    # sumvector_list = []
    # for file in os.listdir(tibfolder):
    #     tibfilename = os.fsdecode(file)
    #     #if  "T02" in tibfilename or "T03" in tibfilename or "T04" in tibfilename:
    #     if  "T04" in tibfilename:
    #         #read_file(tibfolder+tibfilename)
    #         tibfiles.append(tibfolder+tibfilename)
    # pool = multiprocessing.Pool(processes=12)
    # file_data = pool.imap(read_file, tibfiles)
    # pool.close()
    # for data_entry in file_data:
    #     if data_entry[1].ndim == 2:
    #         tibwords.extend(data_entry[0])
    #         sumvector_list.append(data_entry[1])
    # sumvectors = np.concatenate(sumvector_list)
    # print(len(tibwords))
    # print(len(sumvectors))
    # list_of_ids = list(range(len(sumvectors)))
    # pickle.dump( tibwords, open(TIBETAN_WORDS_PATH, "wb" ) )
    # # print("Writing vectors...")
    # # with h5py.File('../vectordata/tibsumvectors.h5', 'w') as hf:
    # #     hf.create_dataset("tibsumvectors",  data=sumvectors)
    # index = faiss.IndexHNSWFlat(100, 32)
    # #index = faiss.index_factory(100, "OPQ64_128,IVF262144_HNSW32,PQ32") # this is a compressed index
    # index.verbose = True
    # faiss.normalize_L2(sumvectors)
    # index.train(sumvectors)
    # index.add(sumvectors)
    # print("Writing Index")
    # faiss.write_index(index, TIBETAN_INDEX_PATH)        
    # return 1

test = train_index(TIBETAN_VECTORS_PATH,TIBETAN_INDEX_PATH)
