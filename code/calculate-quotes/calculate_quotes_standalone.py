from calculate_quotes_sanskrit import read_file as read_file_sanskrit
from calculate_quotes_tibetan import read_file as read_file_tibetan
from calculate_quotes import calculate_all
from quotes_constants import *
import gzip
import faiss
import pickle
from tqdm import tqdm as tqdm
k = 100
lang = "skt"
windowsize = 0
cutoff = 0.1
current_file = ""
current_file_words = []
current_file_vectors = []
index_path = ""
words_path = ""

if lang == "skt":
    windowsize = 5
    index_path = '../../vectordata/sktvectors.idx'
    words_path = '../../vectordata/sktwords.p'
    current_file = "../../test/edition_etext_7_4.tsv"

    current_file_words, current_file_vectors = read_file_sanskrit(current_file)
    
if lang == "tib":    
    windowsize = 7
    index_path = '../../vectordata/tibvectors.idx'
    words_path = '../../vectordata/tibwords.p'
    current_file = "../../test/4032_chap4.tsv"
    
    current_file_words, current_file_vectors = read_file_tibetan(current_file)
    
words = pickle.load( open( words_path, "rb" ) )
index = faiss.read_index(index_path)
faiss.normalize_L2(current_file_vectors)

def process_individual_result(result):
    result_score = result[0]
    result_position = result[1]
    if result[1]+windowsize < len(words):
        if result_score < cutoff and  words[result[1]][0] == words[result[1]+windowsize][0]:
            current_result_unsandhied_words = [word[2].strip() for word in words[result_position:result_position+windowsize]]
            current_result_sentence = ' '.join(current_result_unsandhied_words)
            segment = []
            for c in range(windowsize):                    
                segment.append(words[result_position+c][1])
            segment = list(dict.fromkeys(segment))
            segment = ';'.join(segment)
            return "\t" + words[result_position][0] + "$" + str(result_position) + "$" + segment +  "$" + str(result_score) + "$" + current_result_sentence.strip().replace("\n"," ")
        else:
            return ""

def process_result(results,current_main_sentence_position):
    total_length = len(current_file_words)
    current_main_segment = []
    for c in range(windowsize):
        if current_main_sentence_position+c < len(current_file_words):
            current_main_segment.append(current_file_words[current_main_sentence_position+c][1])        
    current_main_segment = list(dict.fromkeys(current_main_segment))
    current_main_segment = ';'.join(current_main_segment)                                    
    main_unsandhied_words = [word[2].strip() for word in current_file_words[current_main_sentence_position:current_main_sentence_position+windowsize]]
    current_main_sentence = ' '.join(main_unsandhied_words)                                    
    result_string =  current_file_words[current_main_sentence_position][0] + "$" + str(current_main_sentence_position) + "$" + current_main_segment + "$" + current_main_sentence.strip().replace("\n"," ")
    result_pairs = [list(pair) for pair in zip(results[1],results[0])]
    for result_pair in sorted(result_pairs):
        result_string += process_individual_result(result_pair)

    return result_string.replace("\n"," ")
        
def get_results():
    results = index.search(current_file_vectors,k)
    return_results = []
    for scores,positions in zip(results[0],results[1]):
        return_results.append([positions.astype('int32'),scores.astype('float32')])
    return return_results

def create_result_string(results):
    result_string = ''
    current_position = 0 
    for result in tqdm(results):
        result_string += process_result(result,current_position) + "\n"
        current_position += 1
    return result_string

results = get_results()
result_string = create_result_string(results)

with gzip.open(current_file[:-3] + "tab.gz", "wb") as text_file:
    text_file.write(result_string.encode())

