from main import chn_get_sentence_vector,chn_words,chn_get_vectors_fast,chn_get_sentence_vector_sif
from functools import reduce
import numpy as np
replaces_dic = []
for word in chn_words:
    replaces_dic.append((' '.join(word),word))

def normalize(v):
    norm = np.linalg.norm(v)
    if norm == 0: 
       return v
    return v / norm

def is_slice_in_list(s,l):
    len_s = len(s) #so we don't recompute length of s on every iteration
    return any(s == l[i:len_s+i] for i in range(len(l) - len_s+1))
    
def multireplace(string):
    string = ' '.join(string)
    return reduce(lambda a, kv: a.replace(*kv), replaces_dic, string)

punc = " ！？｡。＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏./.|*_"

def remove_punc(string):
    result = ''
    for char in string:
        if char not in punc:
            result += char
    return result


def load_eval_data(eval_file,windowsize,method,variance_switch=0):
    eval_file = open(eval_file,"r")
    eval_data_positive = []
    eval_data_negative = []
    count = 0
    count_negative = 0 
    for line in eval_file:
        sentence1,sentence2,label = line.split('\t')[:3]
        sentence1 = remove_punc(sentence1)
        sentence2 = remove_punc(sentence2)
        sentence1 = multireplace(sentence1)
        sentence2 = multireplace(sentence2)
        words1 = sentence1.split(' ');
        words2 = sentence2.split(' ');
        sentence1_vectors = []
        sentence2_vectors = []
        if variance_switch == 1:
            for c in range(0,len(words1)-windowsize+1,1):
                if not is_slice_in_list(words1[c:c+windowsize],words2):
                    sentence1_vectors.append(normalize(chn_get_sentence_vector(words1[c:c+windowsize],method)))
            for c in range(0,len(words2)-windowsize+1,1):
                sentence2_vectors.append(normalize(chn_get_sentence_vector(words2[c:c+windowsize],method)))
        else:
            for c in range(0,len(words1)-windowsize+1,1):
                sentence1_vectors.append(normalize(chn_get_sentence_vector(words1[c:c+windowsize],method)))
            for c in range(0,len(words2)-windowsize+1,1):
                sentence2_vectors.append(normalize(chn_get_sentence_vector(words2[c:c+windowsize],method)))
        if ("0" in label or "1" in label) and len(sentence1_vectors) > 0 and len(sentence2_vectors) > 0:
            if len(words1) > windowsize and len(words2) > windowsize:
                label = int(label)
                if label == 1:
                    eval_data_positive.append([sentence1_vectors,sentence2_vectors,words1,words2,label,line])
                    count += 1
                else:
                    eval_data_negative.append([sentence1_vectors,sentence2_vectors,words1,words2,label,line])            
                    count_negative += 1
        # make sure that negative and positive data has the same length
        len_pos = len(eval_data_positive)
        len_neg = len(eval_data_negative)
        eval_data = []
        if len_pos > len_neg:
            eval_data.extend(eval_data_negative)
            eval_data.extend(eval_data_positive[:len_neg])
        else:
            eval_data.extend(eval_data_negative[:len_pos])
            eval_data.extend(eval_data_positive)
    print("TOTAL SENTENCES: ",len(eval_data))
    return eval_data



        
