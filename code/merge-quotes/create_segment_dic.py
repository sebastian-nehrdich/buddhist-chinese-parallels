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

lang = 'chn'

if lang == 'chn':
    segment_dic_path = CHINESE_SEGMENT_DICT_PATH.replace(".gz","")
    folder =  CHINESE_TSV_DATA_PATH


segment_dic = {}




def process_file(file):
    f = open(file,'r')
    result_string = ''
    filename = ''
    for line in f:
        if len(line.split('\t')) > 1:
            head,entry = line.split('\t')[:2]
            segment_dic[head] = entry


def process_all(folder):

    files = []
    for file in tqdm(os.listdir(folder)):
        filename = os.fsdecode(file)
        if filename.endswith('tsv'):
            process_file(folder+filename)
    with open(segment_dic_path, 'w') as outfile:        
        json.dump(segment_dic, outfile,indent=4,ensure_ascii=False)

print("creating segment dic...")
process_all(folder)

