import numpy as np
#from fuzzysearch import levenshtein_ngram
import time
import re 
import random
from skbio.alignment import local_pairwise_align_ssw
import skbio

from Levenshtein import distance as distance2
import sentencepiece as spm


punc = " ！？｡。＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏./.|*_#[]-+-"


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

