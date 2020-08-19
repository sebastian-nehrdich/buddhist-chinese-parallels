# these are the evaluation scripts for the paper. 
from main import chn_get_sentence_vector,chn_words,chn_get_vectors_fast,chn_get_sentence_vector_sif
from Levenshtein import distance
import multiprocessing
import textdistance

from sklearn.metrics.pairwise import cosine_similarity
from load_eval_data import load_eval_data,multireplace,remove_punc
import numpy as np
from tqdm import tqdm
import faiss
from scipy.stats import linregress




eval_file = "../data/eval_data_phrase_similarity.tsv"

windowsize = 6

method='mean'

def evaluate(eval_data,method,threshold):
    results = []
    true_positive = 0
    true_negative = 0
    false_positive = 0
    false_negative = 0 
    for entry in eval_data:
        current_result = 0
        sentence1_vectors,sentence2_vectors,words1,words2,label,sentence_string = entry
        if method == "jaro":
            jaro_score = 0
            for c in range(len(words1)-windowsize+1):
                window1 = words1[c:c+windowsize]
                for j in range(len(words2)-windowsize+1):
                    window2 = words2[j:j+windowsize]
                    result = textdistance.jaro_winkler(window1,window2)
                    if result > jaro_score:
                        jaro_score = result
            if jaro_score > threshold:
                current_result = 1
        else:
            scores = cosine_similarity(sentence1_vectors,sentence2_vectors)
            best_score = np.max(scores)
            if best_score > threshold:            
                current_result = 1
        if current_result == 0:
            if label == 0:
                true_negative += 1
                #print("TRUE NEGATIVE",sentence_string)
            else:
                false_negative += 1
        else:
            if label == 1:
                true_positive += 1
                #print("TRUE POSITIVE",sentence_string)
            else:
                false_positive += 1
                #print("FALSE POSITIVE",sentence_string)
    accuracy = (true_positive + true_negative) / (true_positive + true_negative + false_positive + false_negative)
    precision = 0
    f1 = 0
    recall = 0 
    if true_positive + false_positive > 0:
        precision = true_positive / (true_positive + false_positive)
        recall = true_positive / (true_positive + false_negative)
        if precision > 0 and recall > 0:
            f1 =  ( (2 * precision * recall) / (precision + recall) )
    #print(accuracy)
    return [[accuracy, precision, recall, f1], [true_positive,true_negative,false_positive,false_negative],threshold]

def eval_range_human(eval_data,method,threshold,step):
    last_accuracy = 0
    current_accuracy = 0.1
    results = []    
    while threshold < 1.0:
        result = evaluate(eval_data,method,threshold);
        results.append(result)
        #print("Threshold: ", threshold, "Accuracies: ",accuracies,"Values: ",result)
        threshold += step
    results.sort()
    print("FINAL RESULT",method)
    print(results[::-1][0])
    return results

method = "mean"
print("MEAN")
eval_data = load_eval_data(eval_file,windowsize,method)    
eval_range_human(eval_data,method,0.96,0.0001) 

print("MAX")
method = "max"
eval_data = load_eval_data(eval_file,windowsize,method)    
eval_range_human(eval_data,method,0.96,0.0001) 

print("POOL")
method = "pool"
eval_data = load_eval_data(eval_file,windowsize,method)    
eval_range_human(eval_data,method,0.96,0.0001) 



# print("POOL")
# evaluate(eval_data,'pool',0.9952)
# print("MAX")
# evaluate(eval_data,'max',0.9952) 
#print("MEAN")
#evaluate(eval_data,'mean',0.981) 

#evaluate(eval_data,'mean',0.996)



# eval_variances_file = "../eval_data/variances.txt"
# windowsize = 6
# method = 'pool'
# step = 0.001
# # #threshold = 0.998 # for pool
# threshold = 0.996 # for mean
# variance_switch=1 
# eval_data_variances = load_eval_data(eval_variances_file,windowsize,method,variance_switch)
# #blah = evaluate(eval_data_variances,'pool',threshold)
# eval_range_human(eval_data_variances,method,0.85,step)

def evaluate_levenshtein(eval_file):
    threshold = 2
    eval_file = open(eval_file,"r")
    eval_data_positive = []
    eval_data_negative = []
    count = 0
    count_negative = 0
    true_positive = 0
    false_positive = 0
    true_negative = 0
    false_negative = 0
    count = 0
    for line in eval_file:
        count += 1
        sentence1,sentence2,label = line.split('\t')[:3]
        sentence1 = remove_punc(sentence1)
        sentence2 = remove_punc(sentence2)
        sentence1 = multireplace(sentence1)
        sentence2 = multireplace(sentence2)
        sentence1 = sentence1.split(' ')
        sentence2 = sentence2.split(' ')
        lowest_result = 10
        for c in range(0,len(sentence1)-windowsize+1,1):
            fragment_a = ''.join(sentence1[c:c+windowsize])
            for c in range(0,len(sentence2)-windowsize+1,1):
                fragment_b = ''.join(sentence2[c:c+windowsize])
                levenshtein =  distance(fragment_a,fragment_b)
                if levenshtein < lowest_result:
                    lowest_result = levenshtein
        if ("0" in label or "1" in label):
                label = int(label)
                if (label ==1):
                    if lowest_result < threshold:
                        true_positive += 1

                    else: 
                        false_negative += 1
                else:                        
                    if lowest_result > threshold:
                        true_negative += 1
                    else:
                        false_positive += 1
    print("Levenshtein results")
    print("TOTAL NUMBER OF SENTENCES",count)
    print("TRUE POSITIVE",true_positive)
    print("TRUE NEGATIVE",true_negative)
    print("FALSE POSITIVE",false_positive)
    print("FALSE NEGATIVE",false_negative)
    accuracy = (true_positive + true_negative) / (true_positive + true_negative + false_positive + false_negative)
    precision = 0
    f1 = 0
    recall = 0 
    if true_positive + false_positive > 0:
        precision = true_positive / (true_positive + false_positive)
        recall = true_positive / (true_positive + false_negative)
        if precision > 0 and recall > 0:
            f1 =  ( (2 * precision * recall) / (precision + recall) )
    print("accuracy,precision,recall,f1")            
    print(accuracy,precision,recall,f1)

    
evaluate_levenshtein(eval_file)
