import numpy as np
#from fuzzysearch import levenshtein_ngram
import time
import re 
import random
from skbio.alignment import local_pairwise_align_ssw
import skbio

from Levenshtein import distance as distance2
import sentencepiece as spm
sp = spm.SentencePieceProcessor()
sp.Load("skt-unsandhied.model")

r = open("verbinator_tabfile.txt",'r')
punc = " ！？｡。＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏./.|*_#[]-+-"

replaces_dictionary = {}

for line in r:
     headword = line.split('\t')[0]
     entry = line.split('\t')[2]
     replaces_dictionary[headword] = entry.strip()


def multireplace(string):
    if string in replaces_dictionary:
        string = replaces_dictionary[string]
    return string


from Bio import cpairwise2
from Bio import pairwise2





#stringa = "vā brāhmaṇā vā yaṃ loke piyarūpaṃ sātarūpaṃ taṃ aniccato addakkhuṃ dukkhato addakkhuṃ anattato addakkhuṃ rogato addakkhuṃ bhayato addakkhuṃ,"
stringa = "rnams skye bas 'di la nyes pa med do // slob ma 'chos pa'i phyir bstan bcos te"
stringb = "slob ma 'chos pa'i / phyir bstan"
# stringa = "yaṃ loke piyarūpaṃ sātarūpaṃ taṃ"
# strinb = "vā brāhmaṇā loke piyarūpaṃ sātarūpaṃ addakkhuṃ bhayato addakkhuṃ,"
# stringa = "若如是者則能無倒顯示空相"
chn_stringa = "。若如是者則能無倒顯示空相"
chn_stringb = "二性是有。。。實知以實知故即能無倒顯示空相"


def crude_stemmer(tokens):
     tokens = [multireplace(x) for x in tokens]
     result_tokens = []
     for token in tokens:
          token = re.sub(r"([a-z])\'.*",r"\1",token)
          if "/" in tokens:
               token = token + str(random.randint(1,100))
          result_tokens.append(token)
     return result_tokens
     
          

def get_aligned_offsets(stringa,stringb,lang="tib"):
     alignments = []
     if lang == "tib":# or lang == "pali" or lang == "skt":
          if lang == "tib":
               stringa_tokens_before = stringa.split()
               stringb_tokens_before = stringb.split()
          else:
               stringa = stringa.lower()
               stringb = stringb.lower()
               stringa_tokens_before = sp.encode_as_pieces(stringa)
               stringb_tokens_before = sp.encode_as_pieces(stringb)               
          c = 0 
          stringa_lengths = []
          stringa_tokens_after = []
          for token in stringa_tokens_before:
               if not  "/" in token and not "@" in token and token not in punc:
                    stringa_lengths.append(c)
                    stringa_tokens_after.append(token.replace("▁",""))
               if lang == "tib":
                    c += len(token) + 1
               else:
                    c += len(token)
          c = 0
          stringb_lengths = []
          stringb_tokens_after = []
          for token in stringb_tokens_before:
               if not  "/" in token and not "@" in token and token not in punc:
                    stringb_lengths.append(c)
                    stringb_tokens_after.append(token.replace("▁",""))
               if lang == "tib":
                    c += len(token) + 1
               else:
                    c += len(token)
          stringa_tokens = stringa_tokens_after
          stringb_tokens = stringb_tokens_after
          alignments = []
          if lang == "tib":          
               stringa_tokens = crude_stemmer(stringa_tokens_after)
               stringb_tokens = crude_stemmer(stringb_tokens_after)
               #alignments = pairwise2.align.localms(stringa_tokens,stringb_tokens,1,-1,-0.6,-0.3, gap_char=["-"],one_alignment_only=1) # this is the default that we used for a long time
               alignments = pairwise2.align.localms(stringa_tokens,stringb_tokens,5,-4,-5,-5, gap_char=["-"],one_alignment_only=1)
          else:
               # alignment parameters are slightly different for pali/skt
               alignments = pairwise2.align.localms(stringa_tokens,stringb_tokens,1,-1,-.3,-.3, gap_char=["-"],one_alignment_only=1)

          # 1: score fuer identische elemente
          # 2: bestrafung fuer unidentische elemente
          # 3: bestrafung dafuer, eine neue luecke zu eroeffnen
          # 4: bestrafung dafuer, eine neue luecke zu erweitern
          if len(alignments) > 0:
               if len(alignments[0]) ==5 :
                    resulta,resultb,score,beg,end = alignments[0]
                    score = (score/abs(beg-end))
                    a_beg = resulta[:beg]
                    a_len = len([ x for x in a_beg if x is not '-' ])
                    a_offset_beg = stringa_lengths[a_len]
                    b_beg = resultb[:beg]
                    b_len = len([ x for x in b_beg if x is not '-' ])
                    b_offset_beg = stringb_lengths[b_len]
                    a_end = resulta[:end]
                    a_len = len([ x for x in a_end if x is not '-' ])
                    if a_len < len(stringa_lengths):
                         a_offset_end = stringa_lengths[a_len]
                    else:
                         a_offset_end = len(stringa)
                    b_end = resultb[:end]
                    b_len = len([ x for x in b_end if x is not '-' ])
                    if b_len < len(stringb_lengths):
                         b_offset_end = stringb_lengths[b_len]
                    else:
                         b_offset_end = len(stringb)
                    stringa_last_token = stringa[:a_offset_end].strip().split(' ')[-1]
                    if "/" in stringa_last_token or "@" in stringa_last_token:
                         a_offset_end -= len(stringa_last_token) + 1
                    stringb_last_token = stringb[:b_offset_end].strip().split(' ')[-1]
                    if "/" in stringb_last_token or "@" in stringb_last_token:
                         b_offset_end -= len(stringb_last_token) + 1                                            
                    return a_offset_beg,a_offset_end,b_offset_beg,b_offset_end,score
               else:
                    return 0,0,0,0,0
          else:
               return 0,0,0,0,0               
     if lang == "chn" or lang == "skt" or lang == "pli":
          stringa = stringa.lower()
          stringb = stringb.lower()
          stringa_before = stringa
          stringb_before = stringb
          c = 0 
          stringa_lengths = []
          stringa_after = []
          for token in stringa_before:
               if not  token in punc:
                    stringa_lengths.append(c)
                    stringa_after.append(token)
               c += 1
          c = 0
          stringb_lengths = []
          stringb_after = []
          for token in stringb_before:
               if not  token in punc:
                    stringb_lengths.append(c)
                    stringb_after.append(token)
               c += 1
          if lang == "chn":
               alignments = pairwise2.align.localms(stringa_after,stringb_after,1,-1,-0.8,-0.3, gap_char=["-"],one_alignment_only=1)
          if lang == "pli" or lang == "skt":
               alignments = pairwise2.align.localms(stringa_after,stringb_after,1,-1,-1.5,-0.2, gap_char=["-"],one_alignment_only=1)               
          if len(alignments) > 0:
               if len(alignments[0]) ==5 :
                    resulta,resultb,score,beg,end = alignments[0]
                    score = (score/abs(beg-end))
                    a_beg = resulta[:beg]
                    a_len = len([ x for x in a_beg if x  not in punc])
                    a_offset_beg = stringa_lengths[a_len]
                    b_beg = resultb[:beg]
                    b_len = len([ x for x in b_beg if x not in punc])
                    b_offset_beg = stringb_lengths[b_len]
                    a_end = resulta[:end]
                    a_len = len([ x for x in a_end if x not in punc])
                    if a_len < len(stringa_lengths):
                         a_offset_end = stringa_lengths[a_len]
                    else:
                         a_offset_end = len(stringa)
                    b_end = resultb[:end]
                    b_len = len([ x for x in b_end if x not in punc])
                    if b_len < len(stringb_lengths):
                         b_offset_end = stringb_lengths[b_len]
                    else:
                         b_offset_end = len(stringb)
                    while stringa[a_offset_end-1] in punc and a_offset_end > 2:
                         a_offset_end -= 1
                    while stringb[b_offset_end-1] in punc and b_offset_end > 2:
                         b_offset_end -= 1                         
                    return a_offset_beg,a_offset_end,b_offset_beg,b_offset_end,score
               else:
                    return 0,0,0,0,0
          else:
               return 0,0,0,0,0               
                    

# stringa = " yāvadbhir duṣkaraśatair yāvadbhiḥ kuśalasaṃbhārair yāvatā kālena yāvataḥ kleśajñeyāvaraṇasya prahāṇāt samudāgacchatyayaṃ samudāgamaḥ |"
# stringb = "pudgaladharmanairātmyapratipādanaṃ punaḥ kleśajñeyāvaraṇaprahāṇārtham |" 

def get_substring_levenshtein(stringa,stringb):
     allowed_distance = 0
     match = []
     while len(match) == 0:        
          match = list(levenshtein_ngram.find_near_matches_levenshtein_ngrams(stringa,stringb, max_l_dist=allowed_distance))
          allowed_distance += 1
     match = match[0]
     beg = match.start
     end = match.end
     return beg,end


# def get_substring_edlib(stringa,stringb):
#      allowed_distance = 0
#      match = []
#      while len(match) == 0:        
#           match = list(levenshtein_ngram.find_near_matches_levenshtein_ngrams(stringa,stringb, max_l_dist=allowed_distance))
#           allowed_distance += 1
#      match = match[0]
#      beg = match.start
#      end = match.end
#      return beg,end




def test_sentencepair(sentencepair,lang):
     stringa,stringb = sentencepair
     time_before = time.time()
     a,b,c,d = get_aligned_offsets(stringa,stringb,lang)[:-1]
     time_after = time.time()
     print("TIME",time_after - time_before)
     print("STRINGA A BEFORE:",stringa,"#")
     print("STRINGB B BEFORE:",stringb,"#")
     print("STRINGA A  AFTER:",stringa[a:b],"#")
     print("STRINGB B  AFTER:",stringb[c:d],"#")

def test_sentencepair_levenshtein(sentencepair):
     stringa,stringb = sentencepair
     time_before = time.time()
     a,b = get_substring_levenshtein(stringb,stringa)
     time_after = time.time()
     print("TIME",time_after - time_before)
     print("STRINGA B:",stringa,"#")
     print("STRINGB B:",stringb,"#")
     print("STRINGA A:",stringa[a:b],"#")



     
#test_sentencepair([stringa,stringb],'tib')
# test_sentencepair_levenshtein([stringa,stringb])

tibetan_test_sentences = [
     ["bod skad du / shes rab kyi pha rol tu phyin ma'i bstod pa / bcom ldan 'das ma shes rab kyi pha rol tu phyin ma la phyag 'tshal lo // gang khyod sku kun nyes med la // nyes med rnams kyis gzigs mdzad pa // dpag med shes rab pha rol phyin","bod skad du / shes rab kyi pha rol tu phyin ma'i sgrub thabs / 'phags ma shes rab kyi pha rol tu phyin pa la phyag 'tshal lo // de nas gang zhig bsgoms tsam gyis / rgol ba thams cad tshar gcod par // shes rab pha rol phyin "],
     ["shes rab kyi pha rol tu phyin ma'i bstod pa / bcom ldan 'das ma shes rab kyi pha rol tu phyin ","shes rab kyi pha rol tu phyin pa'o zhes bya ba la sogs pa gsungs pa de dag grub pa yin no zhes bya ba ni / bcom ldan 'das ma shes rab kyi pha rol tu phyin "],
     ["shes rab kyi pha rol tu phyin ma'i bstod pa / bcom ldan 'das ma shes rab kyi pha rol tu phyin ","shes rab kyi pha rol tu phyin pa la spyod pa ma yin no zhes 'byung ba'i phyir ro zhes bya ba smras te / bcom ldan 'das ma shes rab kyi pha rol tu phyin "],
     ["shes rab kyi pha rol tu phyin ma'i bstod pa / bcom ldan 'das ma shes rab kyi pha rol tu phyin ma ","shes rab kyi pha rol tu phyin ma'i nga rgyal dang bcas pa'i nga rgyal can gang yin pa de bcom ldan 'das ma shes rab kyi pha rol tu phyin ma'o"],
     ["shes rab kyi pha rol tu phyin ma'i bstod pa / bcom ldan 'das ma shes rab kyi pha rol tu phyin ma la phyag 'tshal lo ","shes rab kyi pha rol tu phyin ma bsdus pa'i tshig le'ur byas pa / bcom ldan 'das ma shes rab kyi pha rol tu phyin ma la phyag 'tshal lo "],
     ["bod skad du / shes rab kyi pha rol tu phyin ma'i bstod pa / bcom ldan 'das ma shes rab kyi pha rol tu phyin ma la phyag 'tshal lo // gang ","bod skad du / shes rab kyi pha rol tu phyin pa'i snying po'i sgrub thabs zhes bya ba / bcom ldan 'das ma shes rab kyi pha rol tu phyin pa la phyag 'tshal lo // gang "],
     
     ]



def eval_sentences(list_of_sentences,lang):
     for sentencepair in list_of_sentences:
          # print(len(sentencepair[0]) / len(sp.encode_as_pieces(sentencepair[0])))
          # print(len(sentencepair[1]) / len(sp.encode_as_pieces(sentencepair[1])))
          test_sentencepair(sentencepair,lang)
          
eval_sentences(tibetan_test_sentences,'tib')

   
# a,b,c,d = get_aligned_offsets(stringa,stringb,"skt")[:-1]
# print("STRINGA:",stringa[a:b])
# print("STRINGB:",stringb[c:d])

# a,b,c,d, = fix_offset_values_tib([a,b,c,d],stringa,stringb,'ba')
# print("STRINGA:",stringa[a:b])
# print("STRINGB:",stringb[c:d])
