import re
import gzip
import json

def atoi(text):
    return int(text) if text.isdigit() else text

def extend_dic_by_tsv(segment_dic,tsv_path):
    current_file = open(tsv_path,"r")
    for line in current_file:
        segment_id, unsandhied_string = line.split('\t')[:2]
        segment_dic[segment_id.strip()] = unsandhied_string.strip()
    return segment_dic


def get_segment_dic(segment_dic_path,tsv_path = ''):
    def natural_keys(text):
        '''
        alist.sort(key=natural_keys) sorts in human order
        http://nedbatchelder.com/blog/200712/human_sorting.html
        (See Toothy's implementation in the comments)
        '''
        return [ atoi(c) for c in re.split(r'(\d+)', text) ]
    segment_dic = json.load(gzip.open(segment_dic_path,'r'))
    if tsv_path != '':
        segment_dic = extend_dic_by_tsv(segment_dic,tsv_path)
    segment_keys = list(segment_dic.keys())
    segment_keys.sort(key=natural_keys)
    segment_key_numbers = {}
    c = 0
    for key in segment_keys:
        segment_key_numbers[key] = c
        c += 1
    return segment_dic, segment_keys, segment_key_numbers,natural_keys


