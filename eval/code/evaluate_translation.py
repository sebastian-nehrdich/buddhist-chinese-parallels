translation_file = "../data/eval_data_translation.tsv"
from load_eval_data import multireplace,normalize
from tqdm import tqdm
from main import chn_get_sentence_vector,chn_words,chn_get_vectors_fast,chn_get_sentence_vector_sif
from Levenshtein import distance
import multiprocessing
import textdistance

from sklearn.metrics.pairwise import cosine_similarity
from load_eval_data import load_eval_data,multireplace
import numpy as np
from tqdm import tqdm
import faiss
from scipy.stats import linregress


def validate_translation(translation_file,windowsize,method):
       # def align_files(sktname,tibname):    
    translation_file = open(translation_file,"r")
    pm_vectors = []
    pm_count = []
    xz_vectors = []
    xz_count = []
    count = 0
    lines = [line.rstrip('\n') for line in translation_file]
    xz_sentences = []
    for line in tqdm(lines):
        if len(line.split('\t')) == 2:
            sentence1,sentence2 = line.split('\t')
            sentence1 = multireplace(sentence1)
            sentence2 = multireplace(sentence2)
            words1 = sentence1.split(' ');
            words2 = sentence2.split(' ');
            sentence1_vectors = []
            sentence2_vectors = []
            if len(words1) > windowsize and len(words2) > windowsize:
                for c in range(0,len(words1)-windowsize+1):
                    pm_vectors.append(normalize(chn_get_sentence_vector(words1[c:c+windowsize],method)))
                    pm_count.append(count)
                for c in range(0,len(words2)-windowsize+1):
                    xz_vectors.append(normalize(chn_get_sentence_vector(words2[c:c+windowsize],method)))
                    xz_count.append(count)
                    xz_sentences.append(line)
                count += 1
    print("Building Index")
    #pm_index = faiss.IndexHNSWFlat(100,16)   # build the eindex
    pm_index = faiss.IndexFlatL2(100)   # build the eindex    
    pm_index.add(np.array(pm_vectors).astype('float32'))
    print("predicting results")
    c = 0
    correct = 0
    false = 0
    len_of_k = 1
    results = pm_index.search(np.array(xz_vectors).astype('float32'), len_of_k)
    for result,prediction in zip(results[1],results[0]):
        xz_reference = xz_count[c]
        flag = 0
        has_flag = 0
        for j in range(len_of_k):
            #print(prediction[j])
            if prediction[j] < 100:
                has_flag = 1
                if pm_count[result[j]] == xz_reference:
                    flag = 1
        if flag == 1:
            correct += 1
            #print("CORRECT:", xz_sentences[c])
        else:
            if has_flag == 1:
                false += 1
                #print("FALSE:", xz_sentences[c])
        c +=1
        # print("SKT: " + skt_sentences[c][0])
        # print("TIB PRED: " + tib_sentences_random[result[0]][0])
        # print("TIB REF: " + tib_sentences[c][0])
        # if distance(tib_sentences_random[result[0]][0],tib_sentences[c][0]) < 5:
        #     correct +=1
        # else:
        #     false += 1

    total = correct + false
    print("TOTAL:",total,"C",c)
    print("Right predictions: " + str(correct) + " - " + str((correct/total) * 100) + "%;  False predictions: " + str(false) + " - " + str((false/total) * 100) + "%")

print("TRANSLATION SIMILARITY MEAN")
print("N = 6")
validate_translation(translation_file,6,'mean')
print("N = 10")
validate_translation(translation_file,10,'mean')

print("TRANSLATION SIMILARITY MAX")
print("N = 6")
validate_translation(translation_file,6,'max')
print("N = 10")
validate_translation(translation_file,10,'max')

print("TRANSLATION SIMILARITY POOL")
print("N = 6")
validate_translation(translation_file,6,'pool')
print("N = 10")
validate_translation(translation_file,10,'pool')


