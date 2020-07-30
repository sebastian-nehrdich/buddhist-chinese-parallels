import copy
import multiprocessing
import itertools
import re
from tqdm import tqdm
import numpy as np
import scipy.spatial
import time




def test_merge_condition(quote,current_quote,max_distance):
    if ((current_quote['quote_position_beg'] >= quote['quote_position_beg']-max_distance) and
        (current_quote['head_position_beg'] >= quote['head_position_beg']-max_distance) and
        (current_quote['quote_position_beg'] <= quote['quote_position_last'] + max_distance)  and
        (current_quote['head_position_beg'] <= quote['head_position_last'] + max_distance)):
        return True

def extend_quote(quote,current_quote,windowsize):
    if current_quote['quote_position_beg'] > quote['quote_position_last']:
        quote['quote_position_last'] = current_quote['quote_position_beg'] 
        quote['quote_segnr'].append(current_quote['quote_segnr'][-1])
    if current_quote['head_position_beg'] > quote['head_position_last']:
        quote['head_position_last'] = current_quote['head_position_beg'] 
        quote['head_segnr'].append(current_quote['head_segnr'][-1])
    if current_quote['quote_position_beg'] < quote['quote_position_beg']:
        quote['quote_position_beg'] = current_quote['quote_position_beg']
        quote['quote_segnr'].insert(0,current_quote['quote_segnr'][0])
    if current_quote['head_position_beg'] < quote['head_position_beg']:
        quote['head_position_beg'] = current_quote['head_position_beg']
        quote['head_segnr'].insert(0,current_quote['head_segnr'][0])
    return quote


def test_query_distance(result_pair,query_pairs,windowsize):
    for query_pair in query_pairs:        
        if (abs(result_pair[0]-query_pair[0]) < (windowsize * 2 + 1) and
            abs(result_pair[1]-query_pair[1]) < (windowsize * 2 + 1)):            
            return True
    return False 

def get_pair_clusters(pair_list,windowsize):
    index = scipy.spatial.cKDTree(pair_list,1000)
    known_results = {}
    clusters = []
    c = 0 
    for query_pair in pair_list:
        known_results[tuple(pair_list[0])] = 1
        if not tuple(query_pair) in known_results:
            query_pairs = [query_pair]
            current_cluster = query_pairs
            while 1==1:
                new_results = []
                query_results = index.query_ball_point(query_pairs, windowsize * 4)
                for query_result in query_results:
                    for result in query_result:
                        result_pair = pair_list[result]
                        if test_query_distance(result_pair,current_cluster,windowsize):
                        #if 1==1:
                            if tuple(result_pair) not in known_results:
                                new_results.append(result_pair)
                                known_results[tuple(result_pair)] = 1
                                current_cluster.append(result_pair)
                if len(new_results) == 0:
                    break
                else:
                    query_pairs = new_results
            if(len(current_cluster) != 0):
                clusters.append(current_cluster)
        c +=1
    return clusters

def construct_quote_from_cluster(cluster,pair_dic,windowsize):
    quote = pair_dic[tuple(cluster[0])]
    for pair in cluster[1:]:
        current_quote = pair_dic[tuple(pair)]
        quote = extend_quote(quote,current_quote,windowsize)
    quote['quote_segnr'] = list(dict.fromkeys(quote['quote_segnr']))
    quote['head_segnr'] = list(dict.fromkeys(quote['head_segnr']))
    return quote
        
def merge_quotes_per_file_batch(quotes,windowsize):
    old_time = time.time()    
    windowsize = windowsize 
    quotes_by_pair = {}
    value_pairs = []
    for quote in quotes:
        quote_position = quote['quote_position_beg']
        head_position = quote['head_position_beg']
        pair = [head_position,quote_position]
        value_pairs.append(pair)
        quotes_by_pair[tuple(pair)] = quote
    #print("LENGTH VALUE PAIRS",len(value_pairs))
    old_time = time.time()
    quote_clusters = get_pair_clusters(value_pairs,windowsize)
    #print("TIME FOR calculating clusters",time.time() - old_time)        
    #old_time = time.time()
    result_quotes = []
    for cluster in quote_clusters:
        result_quotes.append(construct_quote_from_cluster(cluster,quotes_by_pair,windowsize))

    return result_quotes

    
        

def merge_quotes_per_file(parameters):
    quotes,windowsize = parameters
    old_quotes = []
    quotes = merge_quotes_per_file_batch(quotes,windowsize)
    return quotes

def merge_quotes(quotes,windowsize):
    results = []
    quote_buckets = []
    quote_results = []
    old_time = time.time()
    for current_file in list(quotes.keys()):
        #if "4064" in current_file or "4055" in current_file:
        #if 1==1:
            quote_buckets.append(quotes[current_file])
            #quote_results.append(merge_quotes_per_file([quotes[current_file],windowsize])) # uncomment this when running multicore
    pool = multiprocessing.Pool(processes=16)
    quote_results = pool.map(merge_quotes_per_file, zip(quote_buckets,itertools.repeat(windowsize,len(quote_buckets))))
    pool.close()
    for result in quote_results:
        results.extend(result)
    print("TIME FOR calculating quotes alltogether",time.time() - old_time)        

    for quote in results:
        if "4055E:1b-5" in ''.join(quote['quote_segnr']):
            print(quote)
    #     if "T06TD4064E:159a-18" in ''.join(quote['quote_segnr']):
    #         print(quote)        
    return results

def get_data_from_quote(in_quote,windowsize):
    quote = copy.deepcopy(in_quote)
    # this is a small hack: when we don't have any children, we just copy the current quote into the children array and treat it as such
    sorted_children = [quote]    
    if len(quote['children']) > 0:
        sorted_children = quote['children']
    sorted_children.sort(key=lambda x: x['quote_position_beg'])
    quote_segmentnr = quote['quote_segnr']
    head_segmentnr = quote['head_segnr']
    for children in sorted_children:
        for segment in children['quote_segnr']:
            if not segment in quote_segmentnr:
                quote_segmentnr.append(segment)
        for segment in children['head_segnr']:
            if not segment in head_segmentnr:
                head_segmentnr.append(segment)
    return {
        "quote_segnr":quote_segmentnr,
        "head_segnr" : head_segmentnr,
        "quote_position_beg":quote['quote_position_beg'],
        "quote_position_end":quote['quote_position_last']+windowsize,
        "head_position_beg":quote['head_position_beg'],
        "head_position_end":quote['head_position_last']+windowsize,        
    }





    

        
