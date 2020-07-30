import sys
import re
import gzip
import pprint
import numpy as np
import os
import string
import json
import multiprocessing
from Levenshtein import distance as distance2
import numpy as np
from tqdm import tqdm as tqdm
from quotes_constants import *

segment_dic_path = ''
folder = ''
lang = 'pli'
skt_replaces_dic = {}

if lang == 'skt':
    segment_dic_path = '/home/basti/data/segments/sanskrit_segments.json'
    folder = '/home/basti/data/sanskrit/tsv/'
    r = open('gretil-replaces.tab','r')
    for line in r:
        headword = line.split('\t')[0]
        entry = line.split('\t')[1]
        skt_replaces_dic[headword] = entry

if lang == 'pli':
    segment_dic_path = '/home/basti/data/segments/pali_segments.json'
    folder = '/home/basti/data/segmented-pali/tsv/'
if lang == 'tib':
    segment_dic_path = '/home/basti/data/segments/tibetan_segments.json'
    folder =  '/home/basti/data/tibetan/tsv/'

if lang == 'chn':
    segment_dic_path = '/home/basti/data/segments/chinese_segments.json'
    folder =  CHINESE_TSV_DATA_PATH


segment_dic = {}




def process_file(file):
    f = open(file,'r')
    result_string = ''
    filename = ''
    for line in f:
        if len(line.split('\t')) > 1:
            head,entry = line.split('\t')[:2]
            # if lang == 'skt':
            #     head_name,number = head.split(':')
            #     new_headname = head_name
            #     if head_name in skt_replaces_dic:
            #         new_headname = skt_replaces_dic[head_name].rstrip()
            #     head = new_headname + ":" + number
            #     new_line = new_headname + ":" + number + "\t" + '\t'.join(line.split('\t')[1:])
            #     filename = new_headname
            #     result_string += new_line
            # if head in segment_dic:
            #     print(file)
            #     print(head)
            segment_dic[head] = entry
    # with open("fixed/" + filename + ".tsv", 'w') as outfile:        
    #     outfile.write(result_string)

            
#process_file(filename)

def process_all(folder):

    files = []
    for file in tqdm(os.listdir(folder)):
        filename = os.fsdecode(file)
        if filename.endswith('txt'):
            #print(folder+filename)
            #process_file(folder+filename)
            process_file(folder+filename)
    with open(segment_dic_path, 'w') as outfile:        
        json.dump(segment_dic, outfile,indent=4,ensure_ascii=False)
process_all(folder)

