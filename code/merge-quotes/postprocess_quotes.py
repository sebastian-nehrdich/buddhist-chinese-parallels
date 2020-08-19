import re
from quotes_constants import *
import pprint
from tqdm import tqdm as tqdm
from merge_quotes_tools import remove_punc
pp = pprint.PrettyPrinter(indent=4)


chn_stopfile = open(CHINESE_STOPWORDS,'r')


list_of_chinese_stopwords = []
for line in chn_stopfile:
    list_of_chinese_stopwords.append(line.strip())
    

    
def get_len_tib(string):
    string = re.sub(r"\[.+\]","",string)
    string = re.sub("[^ a-zA-Z]","",string)
    string = re.sub("[^ ]+@[^ ]+","",string)
    return len(string.split())

def test_pattern(string):
    if "//" in string or re.search(r"g.{0,2}/",string):
        return True
    else:
        return False


def check_pattern(segtext,offset_beg,offset_end):
    segtext_string = ' '.join(segtext)
    offset_end = len(segtext_string) - (len(segtext[-1]) - offset_end)
    flag = False

    while segtext_string[offset_beg-1] == " " or segtext_string[offset_beg-1] == "/":
        offset_beg -= 1
    if offset_end < len(segtext_string)-1:
        while segtext_string[offset_end] == " " or segtext_string[offset_end] == "/" and offset_end < len(segtext_string)-1:
            offset_end += 1
    offset_end += 1
    if offset_beg < 0:
        offset_beg = 0
    shortened_string = segtext_string[offset_beg:offset_end]
    if shortened_string.count("/") > 2:
        shortened_string = re.sub("^[^/]+"," ",shortened_string)
    # first make sure that the beginning is OK

    if len(shortened_string) > 0:
        if offset_beg < 3 or shortened_string.startswith(' / ') or shortened_string.startswith(' // '):
            shortened_string = re.sub("^[ /]+","",shortened_string)            
            count = 0
            flag = False
            for element in shortened_string.split(' '):

                if "//" in element:
                    if count == 7 or count == 9 or count == 11:
                        flag = True
                    else:
                        count = 1
                        # reset if we only find single /
                elif "/" in element:
                    count = 1
                count += 1
    return flag 


    
def test_quote_tib(quote):
    add_flag = 0
    # very important: remove multiple occurences in / to make sure that the length of quote_strings + par_segtext match up
    quote_strings = re.sub("/+","/",quote['par_string']).split('/')
    root_strings = re.sub("/+","/",quote['root_string']).split('/')

    half_add_flag = check_pattern(quote['par_segtext'],quote['par_offset_beg'],quote['par_offset_end'])
    add_flag = False 
    if half_add_flag:
        add_flag = check_pattern(quote['root_segtext'],quote['root_offset_beg'],quote['root_offset_end'])
    if not add_flag:
        half_add_flag = False
        tokens = []
        stripped_tokens = []
        for string in quote_strings:
            tokens.extend(string.split())
        for token in tokens:
            if not token in list_of_tibetan_stopwords:
                stripped_tokens.append(token)
        if len(stripped_tokens) > 7 and len(tokens) > 13:
            half_add_flag = True
        if len(tokens) < 7:
            half_add_flag = False
        if half_add_flag:
            tokens = []
            stripped_tokens = []
            for string in root_strings:
                tokens.extend(string.split())
            for token in tokens:
                if not token in list_of_tibetan_stopwords:
                    stripped_tokens.append(token)                        
            if len(stripped_tokens) > 7 and len(tokens) > 13:
                add_flag = True
    if quote['root_length'] < 7 or quote['par_length'] < 7:
        add_flag = False
    # avg_length = (quote['root_length'] + quote['par_length']) / 2
    # min_score = 70 - avg_length
    # if min_score < 40:
    #     min_score = 40
    # if quote['score'] < min_score:
    #     add_flag = False
    return add_flag

def get_chn_stopword_ratio(string):
    c = 0 
    for char in string:
        if char in list_of_chinese_stopwords:
            c += 1
    return c / len(string) 

def test_quote_chn(quote):
    quote_string = remove_punc(quote['par_string'])
    root_string = remove_punc(quote['root_string'])
    quote_ratio = get_chn_stopword_ratio(quote_string)
    root_ratio = get_chn_stopword_ratio(root_string)
    avg_ratio = (quote_ratio + root_ratio) / 2
    avg_len = (len(quote_string) + len(root_string)) / 2
    if avg_len >= 10:
        return True
    else:
        len_diff = 10 - avg_len
        score = avg_ratio * ((len_diff+3)/10)
        if score < 0.2:
            return True
    # print(quote_string)
    # print(root_string)





    
def postprocess_quotes_tib(quotes):        
    result_quotes = []
    lost_count = 0 
    for quote in quotes:
        if test_quote_tib(quote):
            result_quotes.append(quote)
    return result_quotes

def postprocess_quotes_chn(quotes):        
    result_quotes = []
    lost_count = 0 
    for quote in quotes:
        if test_quote_chn(quote):
            result_quotes.append(quote)
        else:
            lost_count += 1
    if lost_count > 0 and len(quotes) > 0:
        print("TOTAL LOST",lost_count / len(quotes))
    return result_quotes



# current_quote =  {'score': 96, 'par_length': 16, 'root_length': 17, 'id': 'T06TD4055E:10', 'par_pos_beg': 3329998, 'par_pos_end': 3330026, 'root_pos_beg': 537, 'root_pos_end': 560, 'par_offset_beg': 77, 'par_offset_end': 28, 'par_segnr': ['T06TD4064E:165b-22', 'T06TD4064E:165b-23', 'T06TD4064E:165b-24', 'T06TD4064E:165b-25'], 'par_segtext': ["de'i phyir 'dzin pa gnyis kyi bag chags dang bcas pas zhes bya ba smos so //", "snga ma'i /", 'rnam par smin pa zad nas gzhan //', 'rnam smin skyed pa de yin no //'], 'root_segtext': ['bag chags bcas pas snga ma yis //', 'rnam par smin pa zad nas gzhan //', 'rnam smin skyed pa de yin no //'], 'par_string': "snga ma'i / rnam par smin pa zad nas gzhan // rnam smin skyed pa de yin no", 'root_string': 'snga ma yis // rnam par smin pa zad nas gzhan // rnam smin skyed pa de yin no ', 'root_offset_beg': 19, 'root_offset_end': 29, 'root_segnr': ['T06TD4055E:2b-24', 'T06TD4055E:2b-25', 'T06TD4055E:2b-26'], 'src_lang': 'tib', 'tgt_lang': 'tib'}


# result = test_quote(current_quote)
# print("RESULT",result)
