from tqdm import tqdm
import matplotlib.pyplot as plt 
import re
import numpy as np
from scipy import spatial
import math
from Levenshtein import distance
from fasttext import FastVector
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
import pickle

def get_skt_roots(word):
    word = xliterator.x_UNI_to_SL1(xliterator.internal_to_unicode_transliteration(word))
    roots = []
    results = skt_analyzer.get_tags(word)
    if results is not None:
        for result in results:
            roots.append(xliterator.unicode_to_internal_transliteration(xliterator.x_SL1_to_UNI(result[0]).lower()))
    return roots

def read_dictionary(file):
    f = open(file, 'r')
    dictionary = []
    for line in f:
        m = re.search("([^t]+)\t(.*)", line) # this is for tibetan
        #m = re.search("([^\t]+)\t(.*)", line) # this is for chinese
        if m:
            skt = m.group(1)
            tib = m.group(2)
            dictionary.append((skt,tib))
    return dictionary

def read_weight_dictionary(file):
    f = open(file, 'r')
    dictionary = {}
    for line in f:
        m = re.search("([^ ]+) (.*)", line) # this is for tibetan
        #m = re.search("([^\t]+)\t(.*)", line) # this is for chinese
        if m:
            word = m.group(2)
            count = int(m.group(1))
            dictionary[word] = count
    return dictionary



def read_tib_skt_dic(file):
    f = open(file, 'r')
    dictionary = defaultdict(list)
    count = 0
    for line in f:
        m = re.search("([^ ]+) (.*)", line) # this is for tibetan
        #m = re.search("([^\t]+)\t(.*)", line) # this is for chinese
        if m:
            skt = m.group(1)
            tib = m.group(2)
            dictionary[tib].append(skt)
            count += 1
    print("SKT TIB DIC LENGTH: " + str(count))
    return dictionary

def create_skt_root_dic():
    c = 0
    dictionary = defaultdict(list) 
    for word in skt_words:
        dictionary[word] = list(set(get_skt_roots(word)))
        print(c)
        c+= 1
    return dictionary



def read_stopwords(file):
    f = open(file, 'r')
    dictionary = []
    for line in f:
        m = re.search("(.*)", line) # this is for tibetan
        #m = re.search("([^\t]+)\t(.*)", line) # this is for chinese
        if m:
            if not m[0] == "#":
                dictionary.append(m.group(1).strip())
    return dictionary

def load_data():
    global chn_dictionary
    print("Loading data")
    chn_dictionary = FastVector(vector_file='....//data/chinese.vec')
load_data()

def get_sif_chn(word):
    a = 1e07 # this is the smoothing value 1e04 works great
    if word in wdict_chn:
        freq = wdict_chn[word]
    else:
        freq = 1
    return a / (a + freq)

def get_sif_skt(word):
    a = 5e4 # this is the smoothing value
    if word in wdict_skt:
        freq = int(wdict_skt[word])
    else:
        freq = 1
    return a / (a + freq)

def get_sif_pali(word):
    a = 5e4 # this is the smoothing value
    if word in wdict_skt:
        freq = int(wdict_pali[word])
    else:
        freq = 1
    return a / (a + freq)

def get_freq_pali(word):
    if word in wdict_pali:
        freq = int(wdict_pali[word])
    else:
        freq = 1
    return freq


chn_words = set(chn_dictionary.word2id.keys())
#skt_stop = read_stopwords("../data/skt_stop.txt")



def gen_mean(vals, p):
    p = float(p)
    return np.power(
        np.mean(
            np.power(
                np.array(vals, dtype=complex),
                p),
            axis=0),
        1 / p
    )




def tib_sans_levenshtein_similarity(tibsen, sktsen):
    sum_of_levenshteins = 0
    tibword_num = 0
    if "a" in tibsen and "a" in sktsen:
        for tibword in tibsen.split():
            if tibword in tib_skt_dictionary:
                tibword_num += 1
                current_lowest = 100
                for sktkey in tib_skt_dictionary[tibword]:
                    for sktword in sktsen.split():
                        if distance(sktkey,sktword)  < current_lowest:
                            current_lowest = distance(sktkey,sktword) 
                sum_of_levenshteins += current_lowest
        return sum_of_levenshteins / len(tibsen)
    else:
        return 0

def create_levenshtein_matrix_stemmed(sktsentence,tibsentence):
    sktterms = sktsentence.split()
    tibterms = tibsentence.split()
    actual_skt = []
    actual_tib = []
    for skt_term in sktterms[:39]:
        if skt_term in skt_stems:
            try:
                actual_skt.append(skt_term)
            except:
                print("Word not in dictionary: " + skt_term)
    for tib_term in tibterms[:39]:
        if tib_term in tib_words and len(tib_term) > 2 and not tib_term in tib_stop:
            try:
                actual_tib.append(tib_term)
            except:
                print("Word not in dictionary: " + tib_term)
    result = np.zeros([40,40])
    skt_count = 0
    for skt_term in actual_skt:
        tib_count = 0 
        for tib_term in actual_tib:
            current_lowest = 1
            for sktkey in skt_stems_tib_dictionary[tib_term]:
                current_distance = editdistance.eval(sktkey,skt_term)  / len(skt_term) 
                if current_distance < current_lowest:
                    current_lowest = current_distance
            result[skt_count][tib_count] = 1 - current_lowest
            tib_count += 1
        skt_count += 1
    return result 

def create_levenshtein_matrix(sktsentence,tibsentence):
    sktterms = sktsentence.split()
    tibterms = tibsentence.split()
    actual_skt = []
    actual_tib = []
    for skt_term in sktterms[:39]:
        if skt_term in skt_words:
            try:
                actual_skt.append(skt_term)
            except:
                print("Word not in dictionary: " + skt_term)
    for tib_term in tibterms[:39]:
        if tib_term in tib_words and len(tib_term) > 2 and not tib_term in tib_stop:
            try:
                actual_tib.append(tib_term)
            except:
                print("Word not in dictionary: " + tib_term)
    result = np.zeros([40,40])
    skt_count = 0
    for skt_term in actual_skt:
        tib_count = 0 
        for tib_term in actual_tib:
            current_lowest = 1
            for sktkey in tib_skt_dictionary[tib_term]:
                list_of_skt_terms = [skt_term]
                list_of_skt_terms.extend(skt_roots[skt_term])
                for term in list_of_skt_terms:
                    current_distance = editdistance.eval(sktkey,term)  / len(term) 
                    if current_distance < current_lowest:
                        current_lowest = current_distance
            result[skt_count][tib_count] = 1 - current_lowest
            tib_count += 1
        skt_count += 1
    return result 





def create_frequency_matrix(sktsentence,tibsentence):
    sktterms = sktsentence.split()
    tibterms = tibsentence.split()
    actual_skt = []
    actual_tib = []
    for skt_term in sktterms:
        if skt_term in skt_words:
            try:
                actual_skt.append(skt_term)
            except:
                print("Word not in dictionary: " + skt_term)
    for tib_term in tibterms:
        if tib_term in tib_words and len(tib_term) > 2 and not tib_term in tib_stop:
            try:
                actual_tib.append(tib_term)
            except:
                print("Word not in dictionary: " + tib_term)
    result = np.zeros([40,40])

    skt_count = 0
    for skt_term in actual_skt:
        tib_count = 0 
        for tib_term in actual_tib:
            current_lowest = 1
            result[skt_count][tib_count] = get_sif_skt(skt_term) * get_sif_tib(tib_term)
    return result 



def create_length_difference_matrix(sktsentence,tibsentence):
    sktterms = sktsentence.split()
    tibterms = tibsentence.split()
    actual_skt = []
    actual_tib = []
    for skt_term in sktterms:
        if skt_term in skt_words:
            try:
                actual_skt.append(skt_term)
            except:
                print("Word not in dictionary: " + skt_term)
    for tib_term in tibterms:
        if tib_term in tib_words and len(tib_term) > 2 and not tib_term in tib_stop:
            try:
                actual_tib.append(tib_term)
            except:
                print("Word not in dictionary: " + tib_term)
    result = np.zeros([40,40])
    skt_count = 0
    for skt_term in actual_skt:
        tib_count = 0 
        for tib_term in actual_tib:
            result[skt_count][tib_count] = abs(0.62-(len(skt_term) / len(tib_term)))
            tib_count += 1
        skt_count += 1
    return result 



def create_vectors(sktsentence,tibsentence):
    sktterms = sktsentence.split()
    #sktstems = sktstems.split()
    tibterms = tibsentence.split()
    sktterms_vectors = []
    for skt_term in sktterms:
        if skt_term in skt_words:
            try:
                sktterms_vectors.append(skt_dictionary[skt_term])
            except:
                print("Word not in dictionary: " + skt_term)
    if len(sktterms_vectors) == 0:
        sktterms_vectors.append(skt_dictionary['ca']) # this is a hack for a problem that i don't yet understand
    tibterms_vectors = []
    for tib_term in tibterms:
        if tib_term in tib_words and len(tib_term) > 2 and not tib_term in tib_stop:
            try:
                tibterms_vectors.append(tib_dictionary[tib_term])
            except:
                print("Word not in dictionary: " + tib_term)
    if len(tibterms_vectors) == 0:
        tibterms_vectors.append(tib_dictionary['bzhin']) 
    return sktterms_vectors, tibterms_vectors

def create_vectors_stemmed(sktsentence,tibsentence):
    return skt_get_vectors_fast_stemmed_retrieve(sktsentence),tib_get_vectors_fast_retrieve(tibsentence)
    #return skt_get_vectors_fast_stemmed(sktsentence),tib_get_vectors_fast(tibsentence)


def gen_mean(vals, p):
    p = float(p)
    return np.power(
        np.mean(
            np.power(
                np.array(vals, dtype=complex),
                p),
            axis=0),
        1 / p
    )


operations = dict([
    ('mean', (lambda word_embeddings: [np.mean(word_embeddings, axis=0)], lambda embeddings_size: embeddings_size)),
    ('max', (lambda word_embeddings: [np.max(word_embeddings, axis=0)], lambda embeddings_size: embeddings_size)),
    ('min', (lambda word_embeddings: [np.min(word_embeddings, axis=0)], lambda embeddings_size: embeddings_size)),
    ('p_mean_2', (lambda word_embeddings: [gen_mean(word_embeddings, p=2.0).real], lambda embeddings_size: embeddings_size)),
    ('p_mean_3', (lambda word_embeddings: [gen_mean(word_embeddings, p=3.0).real], lambda embeddings_size: embeddings_size)),
])


def get_sentence_embedding(word_embeddings):
    concat_embs = []
    for o in operations:
        concat_embs += operations[o][0](word_embeddings)
    sentence_embedding = np.concatenate(
        concat_embs,
        axis=0
    )

    return sentence_embedding

def create_sum_vector(vectorlist):
    #return np.average(vectorlist,axis=0)
    return np.add.reduce(vectorlist,axis=0)

def create_weighted_sum_vector(vectorlist,weightlist):
    return np.average(vectorlist,axis=0,weights=weightlist)

    
def skt_get_sentence_vector(sktsen):
    sktvectors = []
    sktweights = []
    for word in sktsen.split():
        if word in skt_words and len(word) > 2:
            sktvectors.append(skt_dictionary[word])
            sktweights.append(get_sif_skt(word))
    try :
        sktmean = np.average(sktvectors,axis=0,weights=sktweights)
        return sktmean 
    except ZeroDivisionError:
        return .0

# def skt_get_sentence_vector_fast(sktsen):
#     return np.add.reduce(sktvector
#     for word in sktsen.split()[1:]:
#         if word in skt_words and len(word) > 1:
#             sktvector += (skt_dictionary[word])
#     return sktvector

    

def tib_get_sentence_vector(tibsen):
    tibvectors = []
    tibweights = []
    for word in tibsen.split():
        if word in tib_words and len(word) > 2:
            tibvectors.append(tib_dictionary[word])
            tibweights.append(get_sif_tib(word))
    try :
        tibmean = np.average(tibvectors,axis=0,weights=tibweights)
        #tibmean = np.average(tibvectors,axis=0)
        return tibmean 
    except ZeroDivisionError:
        return .0

def tib_sentence_similarity(senta,sentb):
    a_vec = np.average(tib_get_vectors_fast(senta),axis=0).reshape(1, -1)
    b_vec = np.average(tib_get_vectors_fast(sentb),axis=0).reshape(1, -1)
    return cosine_similarity(a_vec,b_vec)[0][0]

def tib_sentence_similarity_hier(senta,sentb):
    a_vec = vector_pool_hier(tib_get_vectors_fast(senta)).reshape(1, -1)
    b_vec = vector_pool_hier(tib_get_vectors_fast(sentb)).reshape(1, -1)
    return cosine_similarity(a_vec,b_vec)[0][0]


def tib_get_vectors_fast(tibwords):
    tibwords = tibwords.split()
    tibvectors = []
    for word in tibwords:
        if word in tib_words and len(word) > 2 and not word in tib_stop:
            tibvectors.append(tib_dictionary[word])
    if len(tibvectors) < 1:
        tibvectors.append(tib_dictionary["bzhin"])
    return tibvectors

def chn_get_vectors_fast(chnwords):
    chnvectors = []
    for word in chnwords:
        if word in chn_words:
            chnvectors.append(chn_dictionary[word])            
    if len(chnvectors) < 1:
        chnvectors.append(chn_dictionary["我"])
    return chnvectors

def chn_get_vectors_fast_sif(chnwords):
    chnvectors = []
    chnweights = []
    for word in chnwords:
        if word in chn_words:
            chnvectors.append(chn_dictionary[word])
            chnweights.append(get_sif_chn(word))
    if len(chnvectors) < 1:
        chnvectors.append(chn_dictionary["我"])
    return chnvectors,chnweights



def vector_pool_hier(vectors):
    pool = []
    for i in range(1,len(vectors)+1):
        pool.append(np.mean(vectors[0:i],axis=0))
    #return pool
    return np.max(pool,axis=0)
    
def chn_get_sentence_vector(sentence,method='pool'):
    chn_vectors = chn_get_vectors_fast(sentence)
    if method == 'pool':
        return vector_pool_hier(chn_vectors)
    if method == 'mean':
        return np.mean(chn_vectors,axis=0)
    if method == 'max':
        return np.max(chn_vectors,axis=0)    
    if method == 'sum':
        return np.add.reduce(chn_vectors,axis=0).reshape(-1, 1)

def chn_get_sentence_vector_sif(sentence,method='pool'):
    chn_vectors,chn_weigths = chn_get_vectors_fast_sif(sentence)
    if method == 'pool':
        return vector_pool_hier(chn_vectors)
    if method == 'mean':
        return np.average(chn_vectors,axis=0,weights=chn_weigths)
    if method == 'mean2':
        return np.average(chn_vectors,axis=0)
    if method == 'max':
        return np.max(chn_vectors,axis=0)    
    if method == 'sum':
        return np.add.reduce(chn_vectors,axis=0)#.reshape(1, -1)


    

def tib_get_vectors_fast_retrieve(tibwords):
    tibwords = tibwords.split()
    tibvectors = []
    for word in tibwords:
        if word in tib_words and len(word) > 2 and not word in tib_stop:
            tibvectors.append(tib_retrieve_dictionary[word])
    if len(tibvectors) < 1:
        tibvectors.append(tib_retrieve_dictionary["bzhin"])
    return tibvectors


def tib_get_vectors_fast_from_list(tibwords):
    tibvectors = []
    for word in tibwords:
        if word in tib_words and len(word) > 2 and not word in tib_stop:
            tibvectors.append(tib_dictionary[word])
    if len(tibvectors) < 1:
        tibvectors.append(tib_dictionary["bzhin"])
    return tibvectors

def pali_get_vectors_fast(paliwords):
    paliwords = paliwords.split()
    palivectors = []
    for word in paliwords:
        if word in pali_words:
            palivectors.append(pali_dictionary[word])
        else:
            palivectors.append(pali_dictionary["pe"])
    return palivectors


def skt_get_vectors_fast(sktwords):
    sktwords = sktwords.split()
    sktvectors = []
    for word in sktwords:
        if word in skt_words:
            sktvectors.append(skt_dictionary[word])
        else:
            sktvectors.append(skt_dictionary["ca"])
    return sktvectors

def skt_get_vectors_fast_stemmed(sktwords):
    sktwords = sktwords.split()
    sktvectors = []
    for word in sktwords:
        if word in skt_stems:
            sktvectors.append(skt_stems_dictionary[word])
#        else:
#            sktvectors.append(skt_stems_dictionary["ca"])
    if len(sktvectors) < 1:
        sktvectors.append(skt_stems_dictionary["ca"])

#    print(len(sktvectors))
    return sktvectors



def skt_get_vectors_fast_stemmed_retrieve(sktwords):
    sktwords = sktwords.split()
    sktvectors = []
    for word in sktwords:
        if word in skt_stems:
            sktvectors.append(skt_stems_retrieve_dictionary[word])
        # else:
        #     sktvectors.append(skt_stems_dictionary["ca"])
    if len(sktvectors) < 1:
        sktvectors.append(skt_stems_retrieve_dictionary["ca"])
#    print(len(sktvectors))
    return sktvectors




def skt_get_vectors_fast_from_list(sktwordlist):
    sktvectors = []
    for word in sktwordlist:
        if word in skt_words:
            sktvectors.append(skt_dictionary[word])
        else:
            sktvectors.append(skt_dictionary["ca"])
#    print(len(sktvectors))
    return sktvectors

                         
def skt_tib_sentence_average_similarity(sktsen, tibsen):
    if len(tibsen.split()) > 2 and len(sktsen.split()) > 2:
        skt_vectors,tib_vectors = create_vectors_stemmed(sktsen,tibsen)
        skt_sentence_vector = np.add.reduce(skt_vectors,axis=0).reshape(1, -1)
        tib_sentence_vector = np.add.reduce(tib_vectors,axis=0).reshape(1, -1)
        return cosine_similarity(skt_sentence_vector,tib_sentence_vector)[0][0]
    else:
        return 0

def skt_sentence_average_similarity(sktsen, sktsen2):
    if len(sktsen2.split()) > 2 and len(sktsen.split()) > 2:
        skt_sentence_vector = skt_get_sentence_vector(sktsen)
        ok = 1
        if not isinstance(skt_sentence_vector,float):
            skt_sentence_vector = skt_sentence_vector.reshape(1, -1)
        else:
            ok = 0
        skt2_sentence_vector = skt_get_sentence_vector(sktsen2)
        if not isinstance(skt2_sentence_vector,float):
            skt2_sentence_vector = skt2_sentence_vector.reshape(1, -1)
        else:
            ok = 0
        if ok == 1:
            return cosine_similarity(skt_sentence_vector,skt2_sentence_vector)[0][0]
        else:
            return 0
    else:
        return 0

    
def list_of_sentences_similarity(skt_sentences,tib_sentences,precision):
    skt_max = len(skt_sentences)
    tib_max = len(tib_sentences)
    skt_count = 0
    tib_count = 0
    skt_results = []
    tib_results = []
    precision_list = []
    while skt_count  < skt_max and tib_count + 2 < tib_max:
        skt_sentence = skt_sentences[skt_count]
        tib_sentence = tib_sentences[tib_count]
        current_result = sentence_average_similarity(skt_sentence,tib_sentence)
        if current_result > precision and len(skt_sentence) < 300 and len(skt_sentence):
            while (tib_count  < tib_max and
                   sentence_greedy_similarity(skt_sentence,str(tib_sentence + tib_sentences[tib_count+1])) > current_result and
                   
                   0.25 > abs(0.7-len(skt_sentence)/len(tib_sentence + tib_sentences[tib_count+1])) and
                   0.8 > len(skt_sentence)/len(tib_sentence + tib_sentences[tib_count+1])):
                tib_count += 1
                tib_sentence = tib_sentence + tib_sentences[tib_count]
            if "a" in tib_sentence:
                skt_results.append(skt_sentence)
                tib_results.append(tib_sentence)
                precision_list.append(current_result)
        skt_count += 1
        tib_count += 1
    if len(skt_results) == len(skt_sentences):
        return skt_results, tib_results, precision_list[0], tib_count

def skt_get_segment_coherency(segment):
    segment_vector = skt_get_sentence_vector(segment)
    segment_words = segment.split()
    acc_similarity = 0
    for word in segment_words:
        if word in skt_words:
            acc_similarity += FastVector.cosine_similarity(skt_dictionary[word],segment_vector)
        else:
            acc_similarity += 0 
    return acc_similarity / len(segment_words)

def tib_get_segment_coherency(segment):
    segment_vector = tib_get_sentence_vector(segment)
    segment_words = segment.split()
    acc_similarity = 0
    for word in segment_words:
        if word in tib_words:
            acc_similarity += FastVector.cosine_similarity(tib_dictionary[word],segment_vector)
        else:
            acc_similarity += 0 
    return acc_similarity / len(segment_words)

def skt_get_tibetan_neighbours(sktword):
    sktvector = skt_dictionary[sktword]
    result = []
    for tibterm in tib_words:
        result.append((FastVector.cosine_similarity(tib_dictionary[tibterm],sktvector),tibterm))
    result.sort()
    return list(reversed(result[-20:]))


def get_skt_dic():
    ergebnis = []
    count = 0
    for skt_word in skt_words:
        ergebnis.append(skt_get_tibetan_neighbours(skt_word))
        count += 1
        print(count)
    return ergebnis

def write_skt_dic(result):
    result_string = ""
    for skt_word,entry in zip(skt_words,result):
        entries_string = ""
        for entries in entry:
            entries_string = entries_string + entries[1] + "(" + str(entries[0]) + ")\n"
        result_string = result_string + skt_word + "\t" + entries_string + "\n"
    with open("skt-tib-vector-dic.txt", "w") as text_file:
        text_file.write(result_string)

def skt_get_skt_neighbours(word):
    current_vector = word #skt_dictionary[word]
    result = []
    for skt_word in skt_words:
        result.append((FastVector.cosine_similarity(current_vector,skt_dictionary[skt_word]), skt_word))
    result.sort()
    return list(reversed(result[-20:]))

def create_matrix(sktsentence,tibsentence):
    sktterms = sktsentence.split()
    tibterms = tibsentence.split()
    print(sktsentence)
    print(tibsentence)
    sktterms_vectors = []
    tibterms_vectors = []
    for skt_term in sktterms:
        if skt_term in skt_words:
            sktterms_vectors.append(skt_dictionary[skt_term])
    if len(sktterms_vectors) == 0:
        sktterms_vectors.append(skt_dictionary['ca'])
    tibterms_vectors = []
    for tib_term in tibterms:
        if tib_term in tib_words:
            tibterms_vectors.append(tib_dictionary[tib_term])
    return sktterms_vectors, tibterms_vectors

def turn_sentences_into_matrix(skt_sentence,tib_sentence):
   skt_vector,tib_vector = create_vectors(skt_sentence,tib_sentence)
   if len(skt_vector) < 40 and len(tib_vector) < 40:
      ergebnis = np.array(getDynamicPooledMatrix(getSimilarityMatrix(skt_vector,tib_vector,metric='cos')))
      if ergebnis is None:
         return np.zeros([40,40])
      else:
         return ergebnis
   else:
       return np.zeros([40,40])

def turn_sentences_into_matrix_stemmed(skt_sentence,tib_sentence):
   skt_vector,tib_vector = create_vectors_stemmed(skt_sentence,tib_sentence)
   if len(skt_vector) < 40 and len(tib_vector) < 40:
      ergebnis = np.array(getDynamicPooledMatrix(getSimilarityMatrix(skt_vector,tib_vector,metric='cos')))
      if ergebnis is None:
         return np.zeros([40,40])
      else:
         return ergebnis
   else:
       return np.zeros([40,40])

   
def turn_sentences_into_matrix_euclidean(skt_sentence,tib_sentence):
   skt_vector,tib_vector = create_vectors_stemmed(skt_sentence,tib_sentence)
   if len(skt_vector) < 40 and len(tib_vector) < 40:
      ergebnis = np.array(getDynamicPooledMatrix(getSimilarityMatrixEuclidean(skt_vector,tib_vector,metric='cos')))
      if ergebnis is None:
         return np.zeros([10,10])
      else:
         return ergebnis

     
def turn_sentences_into_matrix_pair(pair):
    skt_stems = pair[0].replace("-"," ")
    skt_sentence = pair[1]
    tib_sentence = pair[2]
    #return np.dstack((create_levenshtein_matrix(skt_sentence,tib_sentence),turn_sentences_into_matrix(skt_sentence,tib_sentence),turn_sentences_into_matrix_euclidean(skt_sentence,tib_sentence)))
    #return np.dstack((turn_sentences_into_matrix(skt_sentence,tib_sentence),turn_sentences_into_matrix_stemmed(skt_stems,tib_sentence)))
    return np.dstack((create_levenshtein_matrix_stemmed(skt_stems,tib_sentence),create_levenshtein_matrix(skt_sentence,tib_sentence),turn_sentences_into_matrix_stemmed(skt_stems,tib_sentence),turn_sentences_into_matrix(skt_sentence,tib_sentence)))


def turn_sentences_into_matrix_pair_one_layer(pair):
    skt_sentence = pair[0]
    tib_sentence = pair[1]
    #return np.dstack((create_levenshtein_matrix(skt_sentence,tib_sentence),turn_sentences_into_matrix(skt_sentence,tib_sentence),turn_sentences_into_matrix_euclidean(skt_sentence,tib_sentence)))
    return np.dstack(turn_sentences_into_matrix_stemmed(skt_sentence,tib_sentence))


def predict_list_of_sentencepairs(sentencelist,sc_flag=0):
    list_of_results = np.zeros(len(sentencelist))
    list_of_matrices = []
    if sc_flag == 1:
        for pair in sentencelist:
            list_of_matrices.append(turn_sentences_into_matrix_pair(pair))
    else:
        pool = multiprocessing.Pool(processes=40)
        list_of_matrices = pool.map(turn_sentences_into_matrix_pair,sentencelist)
        pool.close()
    if sc_flag == 0:
        print("Feeding " + str(len(list_of_matrices)) + " sentence pairs to the GPU")
    list_of_matrices = np.array(list_of_matrices)
    list_of_matrices = list_of_matrices.reshape(list_of_matrices.shape[0],40,40,4)
    global graph # this relates to the hack for using multiple threads of keras at the same time
    with default_graph.as_default():
        if sc_flag == 1:
            return model.predict(list_of_matrices)
        else:
            return model.predict(list_of_matrices,verbose=1)
        
def predict_sentencepair(sentencepair):
    matrices = turn_sentences_into_matrix_pair(sentencepair).reshape(1,40,40,4)
    global graph # this relates to the hack for using multiple threads of keras at the same time
    with default_graph.as_default():
        return model.predict(matrices)[0][1]

def predict_borders_sentencepair(sentencepair):
    matrices = turn_sentences_into_matrix_pair(sentencepair).reshape(1,40,40,4)
    global graph # this relates to the hack for using multiple threads of keras at the same time
    with default_graph.as_default():
        return model_borders.predict(matrices)

    
def predict_borders_list_of_sentencepairs(sentencelist,sc_flag=0):
    list_of_results = np.zeros(len(sentencelist))
    list_of_matrices = []
    if sc_flag == 1:
        for pair in sentencelist:
            list_of_matrices.append(turn_sentences_into_matrix_pair(pair))
    else:
        pool = multiprocessing.Pool(processes=40)
        list_of_matrices = pool.map(turn_sentences_into_matrix_pair,sentencelist)
        pool.close()
    if sc_flag == 0:
        print("Feeding " + str(len(list_of_matrices)) + " sentence pairs to the GPU")
    list_of_matrices = np.array(list_of_matrices)
    list_of_matrices = list_of_matrices.reshape(list_of_matrices.shape[0],40,40,4)
    global graph # this relates to the hack for using multiple threads of keras at the same time
    with default_graph.as_default():
        if sc_flag == 1:
            results =  model_borders.predict(list_of_matrices)
        else:
            results =  model_borders.predict(list_of_matrices,verbose=1)
    return results
    # return_results = []
    # for pair in sentencelist:
    #     if len(pair[0].split()) < 40:
    #         return
    #         else:
            
    

    
def predict_list_of_sentencepairs_one_layer(sentencelist):
    list_of_results = np.zeros(len(sentencelist))
    list_of_matrices = []
    pool = multiprocessing.Pool(processes=40)
    list_of_matrices = pool.map(turn_sentences_into_matrix_pair_one_layer,sentencelist)
    pool.close()
    # for pair in sentencelist:
    #     list_of_matrices.append(turn_sentences_into_matrix_pair([pair[0],pair[1]]))
    print("Feeding " + str(len(list_of_matrices)) + " sentence pairs to the GPU")
    list_of_matrices = np.array(list_of_matrices)
    list_of_matrices = list_of_matrices.reshape(list_of_matrices.shape[0],40,40,1)
    global graph # this relates to the hack for using multiple threads of keras at the same time
    with default_graph.as_default():
        return model_one_layer.predict(list_of_matrices,verbose=1)


    
def create_data_for_classifier(datafile):
    datafile = open(datafile,'r')
    skt_sentences = []
    tib_sentences = []
    skt_stems = []
    is_gold = []
    sentence_matrixes = []
    positive = 0
    negative = 0
    for line in datafile:
        m = re.search("([^\t]+)\t([^\t]+)\t([^\t]+)\t([0-2])", line)
        if m:
            skt_stem = m.group(1).replace("-"," ")
            skt_unsandhied = m.group(2)
            tib = m.group(3)
            if len(skt_unsandhied.split()) < 40 and len(tib.split()) < 40 and len(skt_stem.split()) < 40:
                skt_stems.append(skt_stem)
                skt_sentences.append(skt_unsandhied)
                tib_sentences.append(tib)
                is_gold.append(int(m.group(4)))
                if int(m.group(4)) == 1:
                    positive += 1
                else:
                    negative += 1
    print("Total number of sentences: ")
    print(len(skt_sentences))
    print("Positive/negative ratio: " + str(positive / (positive + negative)))
    pool = multiprocessing.Pool(processes=40)
    sentence_matrixes = pool.map(turn_sentences_into_matrix_pair,zip(skt_stems,skt_sentences,tib_sentences))
    sentence_matrixes = np.array(sentence_matrixes)
    pool.close()
    # for skt_sentence,tib_sentence in zip(skt_sentences,tib_sentences):        
    #     sentence_matrixes.append(turn_sentences_into_matrix_pair([skt_sentence,tib_sentence]))
    return sentence_matrixes.reshape(sentence_matrixes.shape[0],40,40,4), np.array(is_gold)

def create_data_for_classifier_one_layer(datafile):
    datafile = open(datafile,'r')
    skt_sentences = []
    tib_sentences = []
    skt_stems = []
    is_gold = []
    positive = 0
    negative = 0
    for line in tqdm(datafile):
        m = re.search("([^\t]+)\t([^\t]+)\t([^\t]+)\t([0-2])", line)
        if m and len(m.group(2).split()) < 40 and len(m.group(3).split()) < 40 and len(m.group(1).split()) < 40:
            skt_stems.append(m.group(1).replace("-"," "))
            skt_sentences.append(m.group(2))
            tib_sentences.append(m.group(3))
            is_gold.append(int(m.group(4)))
            if int(m.group(4)) == 1:
                positive += 1
            else:
                negative += 1
    print("Total number of sentences: ")
    print(len(skt_sentences))
    print(len(skt_stems))
    print("Positive/negative ratio: " + str(positive / (positive + negative)))
    pool = multiprocessing.Pool(processes=40)
    sentence_matrixes = pool.map(turn_sentences_into_matrix_pair_one_layer,zip(skt_stems,tib_sentences))
    pool.close()
    sentence_matrixes = np.array(sentence_matrixes)
    #o for skt_sentence,tib_sentence in zip(skt_sentences,tib_sentences):        
    #     sentence_matrixes.append(turn_sentences_into_matrix_pair([skt_sentence,tib_sentence]))
    return sentence_matrixes.reshape(sentence_matrixes.shape[0],40,40,1), np.array(is_gold)




