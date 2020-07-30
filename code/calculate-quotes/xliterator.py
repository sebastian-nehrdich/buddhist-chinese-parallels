# -*- coding: utf-8 -*-
#!/usr/bin/python
"""
This module takes care of transliteration.
"""
import sys, re, os

SEPARATOR_PRIMARY=";"

class Xlator(dict): # Xlator is initialized through a mapping
	def _make_regex(self):
		"""Build re object based on the keys of the current dict"""
		return re.compile("|".join(map(re.escape, self.keys())))
	def __call__(self, match):
		"""Handler invoked for each regex match"""
		return self[match.group(0)]	
	def xlate(self, text):
		"""Translate text, returns the modified text"""
		return self._make_regex().sub(self, text)

def _transposeDict(d): # returns a dict with key value transposed
	nd = {}
	for (k,v) in d.items():
		nd[v]=k
	return nd
	
DICT_HK_CC = {'RR':'F','lR':'L','lRR':'X','ai':'E','au':'O',\
	'kh':'K','gh':'V','ch':'C','jh':'Y','Th':'q',\
	'Dh':'Q','th':'w','dh':'W','ph':'P','bh':'B'
	} # lRT is not lR+T but l+R+T !!!

def x_HK_to_CC(in_str_HK): # input: HarvardKyoto output: CC
	xlator_Obj = Xlator(DICT_HK_CC)
	return xlator_Obj.xlate(in_str_HK)
	
def x_CC_to_HK(in_str_CC): # output: HarvardKyoto input: CC
	xlator_Obj = Xlator(_transposeDict(DICT_HK_CC))
	return xlator_Obj.xlate(in_str_CC)

DICT_CC_tex = {'A':'\={a}','I':'\={\i}','U':'\={u}','R':'\d r','F':'\d {\= r}','L':'\d l',\
	'X':'\d L','E':'ai','O':'au','K':'kh','V':'gh','G':'\. n',\
	'C':'ch','Y':'jh','J':'\~{n}','T':'\d t','q':'\d th','D':'\d d',\
	'Q':'\d dh','N':'\d n','Z':"\\'{S}",'w':'th','W':'dh','P':'ph',\
	'B':'bh','z':"\\'{s}",'S':'\d s','M':'\d m','H':'\d h', ';':' $|$'
	} # CC to roman diacriticals for Latex
	
def x_CC_to_tex(in_str_CC): # input: CC output: tex
	xlator_Obj = Xlator(DICT_CC_tex)
	return xlator_Obj.xlate(in_str_CC)
	
def x_HK_to_tex(in_str_HK):
	return x_CC_to_tex(x_HK_to_CC(in_str_HK))
	
####

DICT_CC_tex_first_cap = {'a':'A','A':'\={A}','i':'I','I':'\={I}','u':'U','U':'\={U}','R':'\d R','F':'\d {\= R}','L':'\d L',\
	'X':'\d L','e':'E','E':'Ai','o':'O','O':'Au',\
	'k':'K','K':'Kh','g':'G','V':'Gh','G':'\. N',\
	'c':'C','C':'Ch','j':'J','Y':'Jh','J':'\~{N}',\
	'T':'\d T','q':'\d Th','D':'\d D','Q':'\d Dh','N':'\d N',\
	't':'T','w':'Th','d':'D','W':'Dh','n':'N',\
	'p':'P','P':'Ph','b':'B','B':'Bh','m':'M',\
	'y':'Y','r':'R','l':'L','v':'V',\
	'z':"\\'{S}",'S':'\d S','s':'S','h':'H',\
	'M':'\d M','H':'\d H', ';':' $|$'
	} # CC to roman diacriticals for Latex
	
def x_CC_to_tex_first_cap(in_str_CC): # input: CC output: tex

	first_letter=in_str_CC[:1]
	rest_letters=in_str_CC[1:]
	
	xlator_Obj_first_letter = Xlator(DICT_CC_tex_first_cap)
	first_letter_tex = xlator_Obj_first_letter.xlate(first_letter)
	
	xlator_Obj = Xlator(DICT_CC_tex)
	rest_letters_tex = xlator_Obj.xlate(rest_letters)
	return first_letter_tex+rest_letters_tex
	
def x_HK_to_tex_first_cap(in_str_HK):
	return x_CC_to_tex_first_cap(x_HK_to_CC(in_str_HK))

####

DICT_CC_BF = {'a':'a_0 hrasva_0','A':'a_0 dIrgha_0',\
	'i':'i_0 hrasva_0','I':'i_0 dIrgha_0','u':'u_0 hrasva_0',\
	'U':'u_0 dIrgha_0','R':'R_1 hrasva_0','F':'R_1 dIrgha_0',\
	'L':'lR_0 hrasva_0','X':'lR_0 dIrgha_0',\
	'e':'e_0','E':'ai_0','o':'o_0','O':'au_0',\
	'k':'k_0','K':'kh_0','g':'g_0','V':'gh_0','G':'G_1',\
	'c':'c_0','C':'ch_0','j':'j_0','Y':'jh_0','J':'J_1',\
	'T':'T_1','q':'Th_1','D':'D_1','Q':'Dh_1','N':'N_1',\
	't':'t_0','w':'th_0','d':'d_0','W':'dh_0','n':'n_0',\
	'p':'p_0','P':'ph_0','b':'b_0','B':'bh_0','m':'m_0',\
	'y':'y_0','r':'r_0','l':'l_0','v':'v_0',\
	'z':'z_0','S':'S_1','s':'s_0','h':'h_0','M':'M_1','H':'H_1'
	}

def x_HK_to_BF(in_str_HK): # input:HK output:Base format 
	xlator_Obj = Xlator(DICT_CC_BF)
	sL=list(x_HK_to_CC(in_str_HK))
	sL1=[xlator_Obj.xlate(p) for p in sL]
	return SEPARATOR_PRIMARY.join(sL1)
	
DICT_iTrans_CC = {'aa':'A','ii':'I','uu':'U','.r':'R','*r':'F','.l':'L',\
	'*l':'X','ai':'E','au':'O', 'kh':'K','gh':'V','.g':'G',\
	'ch':'C','jh':'Y','.j':'J','.t':'T','.th':'q','.d':'D',\
	'.dh':'Q','.n':'N','*n':'Z','th':'w','dh':'W','ph':'P',\
	'bh':'B','sh':'z','.s':'S','.m':'M','.h':'H'
	}# *n as in agnimii*ne, *r:diirgha R, .l:lR, *l:lRR
	
def x_iTrans_to_CC(in_str_iTrans): # input: iTrans output: CC
	# - All letters in iTrans are case insensitive BUT not in CC
	# - x is not used in CC, used as syllable seperator	
	xlator_Obj = Xlator(DICT_iTrans_CC)
	return xlator_Obj.xlate(in_str_iTrans.lower())
	# iTrans is case insensitive
	
def x_CC_to_iTrans(in_str_CC): # input:CC output: iTrans
	xlator_Obj = Xlator(_transposeDict(DICT_iTrans_CC))
	return xlator_Obj.xlate(in_str_CC)
	
DICT_iTrans_tex_cs = {'aa':'\={a}','.j':'\~{n}', 'ii':'\={\i}', 'z':"\\'{s}",\
	'uu':'\={u}','.d':'\d d', '.h':'\d h','.m':'\d m', '.s':'\d s','.t':'\d t',\
	'.r':'\d r', '.l' : '\d l',	".g":'\. n','.n':'\d n', 'AA':'\={A}','.J':'\~{N}',\
	'II':'\={I}', 'Z':"\\'{S}", 'UU':'\={U}','.D':'\d D', '.H':'\d H','.M':'\d M',\
	'.S':'\d S','.T':'\d T', '.R':'\d R', '.L' : '\d L', ".G":'\. N','.N':'\d N',\
	';':' $|$','*r':'\d {\=r}','*l':'\d {\=l}','*n':'{\l}',
	}

def x_iTrans_to_tex_CS(in_str_iTrans): # input:iTrans Case Sensitive
	xlator_Obj = Xlator(DICT_iTrans_tex_cs)
	return xlator_Obj.xlate(in_str_iTrans) # Case sensitive
	
DICT_iTrans_dn = {'.g':'"n','.j':'~n','z':'"s','.m':'M','.h':'H',"'":'.a', ';':'|'
	}
	
def x_iTrans_to_dn(in_str_iTrans): # input:iTrans output:devanagari dn for Latex
	xlator_Obj = Xlator(DICT_iTrans_dn)
	return xlator_Obj.xlate(in_str_iTrans)

DICT_CC_dn = {'A':'aa','I':'ii','U':'uu','R':'.r','F':'.R','L':'.l',\
	'X':'.L','E':'ai','O':'au','K':'kh','V':'gh','G':'"n',\
	'C':'ch','Y':'jh','J':'~n','T':'.t','q':'.th','D':'.d',\
	'Q':'.dh','N':'.n','Z':'L','w':'th','W':'dh','P':'ph',\
	'B':'bh','z':'"s','S':'.s','.m':'M','.h':'H',"'":'.a', ';':'|'
	} # CC to devanagari dn for Latex
	
def x_CC_to_dn(in_str_CC): # input:CC output:devanagari dn for Latex
	xlator_Obj = Xlator(DICT_CC_dn)
	return xlator_Obj.xlate(in_str_CC)
	
def x_phSet_to_Tex(phSet): # 
	# here udAtta_0 can also be tackled
	if 'dIrgha_0' in phSet:
		if 'a_0' in phSet: return '\={a}'
		elif 'i_0' in phSet: return '\={\i}'
		elif 'u_0' in phSet: return '\={u}'
		elif 'R_1' in phSet: return '\d r'
		elif 'lR_0' in phSet: return '\d l'
	elif 'a_0' in phSet: return 'a'
	elif 'i_0' in phSet: return 'i'
	elif 'u_0' in phSet: return 'u'
	elif 'R_1' in phSet: return '\d r'
	elif 'lR_0' in phSet: return '\d l'
	elif 'e_0' in phSet: return 'e'
	elif 'o_0' in phSet: return 'o'
	elif 'ai_0' in phSet: return 'ai'
	elif 'au_0' in phSet: return 'au'
	elif 'h_0' in phSet: return 'h'
	elif 'y_0' in phSet: return 'y'
	elif 'v_0' in phSet: return 'v'
	elif 'r_0' in phSet: return 'r'
	elif 'l_0' in phSet: return 'l'
	elif 'J_1' in phSet: return '\~{n}'
	elif 'm_0' in phSet: return 'm'
	elif 'G_1' in phSet: return '\. n'
	elif 'N_1' in phSet: return '\d n'
	elif 'n_0' in phSet: return 'n'
	elif 'jh_0' in phSet: return 'jh'
	elif 'bh_0' in phSet: return 'bh'
	elif 'gh_0' in phSet: return 'gh'
	elif 'Dh_1' in phSet: return '\d dh'
	elif 'dh_0' in phSet: return 'dh'
	elif 'j_0' in phSet: return 'j'
	elif 'b_0' in phSet: return 'b'
	elif 'g_0' in phSet: return 'g'
	elif 'D_1' in phSet: return '\d d'
	elif 'd_0' in phSet: return 'd'
	elif 'kh_0' in phSet: return 'kh'
	elif 'ph_0' in phSet: return 'ph'
	elif 'ch_0' in phSet: return 'ch'
	elif 'Th_1' in phSet: return '\d th'
	elif 'th_0' in phSet: return 'th'
	elif 'c_0' in phSet: return 'c'
	elif 'T_1' in phSet: return '\d t'
	elif 't_0' in phSet: return 't'
	elif 'k_0' in phSet: return 'k'
	elif 'p_0' in phSet: return 'p'
	elif 'z_0' in phSet: return "\\'{s}"
	elif 'S_1' in phSet: return '\d s'
	elif 's_0' in phSet: return 's'
	elif 'H_1' in phSet: return '\d h'
	elif 'M_1' in phSet: return '\d m'
	else: return ' '

def x_phSet_to_CC(phSet): # 
	# here udAtta_0 can also be tackled
	if 'dIrgha_0' in phSet:
		if 'a_0' in phSet: return 'A'
		elif 'i_0' in phSet: return 'I'
		elif 'u_0' in phSet: return 'U'
		elif 'R_1' in phSet: return 'F'
		elif 'lR_0' in phSet: return 'X'
	elif 'a_0' in phSet: return 'a'
	elif 'i_0' in phSet: return 'i'
	elif 'u_0' in phSet: return 'u'
	elif 'R_1' in phSet: return 'R'
	elif 'lR_0' in phSet: return 'L'
	elif 'e_0' in phSet: return 'e'
	elif 'o_0' in phSet: return 'o'
	elif 'ai_0' in phSet: return 'E'
	elif 'au_0' in phSet: return 'O'
	elif 'h_0' in phSet: return 'h'
	elif 'y_0' in phSet: return 'y'
	elif 'v_0' in phSet: return 'v'
	elif 'r_0' in phSet: return 'r'
	elif 'l_0' in phSet: return 'l'
	elif 'J_1' in phSet: return 'J'
	elif 'm_0' in phSet: return 'm'
	elif 'G_1' in phSet: return 'G'
	elif 'N_1' in phSet: return 'N'
	elif 'n_0' in phSet: return 'n'
	elif 'jh_0' in phSet: return 'Y'
	elif 'bh_0' in phSet: return 'B'
	elif 'gh_0' in phSet: return 'V'
	elif 'Dh_1' in phSet: return 'Q'
	elif 'dh_0' in phSet: return 'W'
	elif 'j_0' in phSet: return 'j'
	elif 'b_0' in phSet: return 'b'
	elif 'g_0' in phSet: return 'g'
	elif 'D_1' in phSet: return 'D'
	elif 'd_0' in phSet: return 'd'
	elif 'kh_0' in phSet: return 'K'
	elif 'ph_0' in phSet: return 'P'
	elif 'ch_0' in phSet: return 'C'
	elif 'Th_1' in phSet: return 'q'
	elif 'th_0' in phSet: return 'w'
	elif 'c_0' in phSet: return 'c'
	elif 'T_1' in phSet: return 'T'
	elif 't_0' in phSet: return 't'
	elif 'k_0' in phSet: return 'k'
	elif 'p_0' in phSet: return 'p'
	elif 'z_0' in phSet: return 'z'
	elif 'S_1' in phSet: return 'S'
	elif 's_0' in phSet: return 's'
	elif 'H_1' in phSet: return 'H'
	elif 'M_1' in phSet: return 'M'
	else: return ' '	
##############
# For websites
##############

DICT_V_X = {'a':'ax', 'A':'Ax', 'i':'ix','I':'Ix','u':'ux','U':'Ux',\
	'e':'ex','E':'Ex','o':'ox','O':'Ox', 'R':'Rx','F':'Fx','M':'Mx','H':'Hx','f':'fx',\
	'L':'Lx',' ':'x x',';':'x;x',',':'x,x','.':'x.x','\n':'x\nx'}
	
def _CC_To_V_X(inStrCC):
	xlator_Obj=Xlator(DICT_V_X)
	return xlator_Obj.xlate(inStrCC)

def _treat_MH(inStr):
	pat = re.compile('xMx')
	inStr1=pat.sub('Mx',inStr)
	pat = re.compile('xHx')
	inStr2 = pat.sub('Hx',inStr1)
	return inStr2.replace('xx','x')
	
def get_syllables(inStrCC):
	return _treat_MH(_CC_To_V_X(inStrCC))
	
devDict = {
	'k':'&#x915;',\
	'K':'&#x916;',\
	'g':'&#x917;',\
	'V':'&#x918;',\
	'G':'&#x919;',\
	'c':'&#x91A;',\
	'C':'&#x91B;',\
	'j':'&#x91C;',\
	'Y':'&#x91D;',\
	'J':'&#x91E;',\
	'T':'&#x91F;',\
	'q':'&#x920;',\
	'D':'&#x921;',\
	'Q':'&#x922;',\
	'N':'&#x923;',\
	't':'&#x924;',\
	'w':'&#x925;',\
	'd':'&#x926;',\
	'W':'&#x927;',\
	'n':'&#x928;',\
	'p':'&#x92A;',\
	'P':'&#x92B;',\
	'b':'&#x92C;',\
	'B':'&#x92D;',\
	'm':'&#x92E;',\
	'y':'&#x92F;',\
	'r':'&#x930;',\
	'rSTi':'&#x0930;&#x094d;&#x0937;&#x094d;&#x091f;&#x093f;',\
	'l':'&#x932;',\
	'v':'&#x935;',\
	'z':'&#x936;',\
	'S':'&#x937;',\
	's':'&#x938;',\
	'h':'&#x0939;',\
	"'":'&#x093D;',\
	".":'&#x0964;',\
	';':'&#x0964;',\
	}
mAtrADict = {
	'A':'&#x093e;',\
	'i':'&#x093f;',\
	'I':'&#x0940;',\
	'u':'&#x0941;',\
	'U':'&#x0942;',\
	'R':'&#x0943;',\
	'F':'&#x0944;',\
	'e':'&#x0947;',\
	'E':'&#x0948;',\
	'o':'&#x094b;',\
	'O':'&#x094c;',\
	}
MHDict = {'M':'&#x0902;', 'H':'&#x0903;'}
svaraDict = {
	'f':'&#x0950;',\
	'a':'&#x0905;',\
	'A':'&#x0906;',\
	'i':'&#x0907;',\
	'I':'&#x0908;',\
	'u':'&#x0909;',\
	'U':'&#x090a;',\
	'e':'&#x090f;',\
	'E':'&#x0910;',\
	'o':'&#x0913;',\
	'O':'&#x0914;',\
	'R':'&#x90B;',\
	'F':'&#x960;',\
	'L':'&#x90C;',\
	'X':'&#x961;',\
	}
vyaJjanaDict={
	'k':'&#x915;&#x094d;',\
	'K':'&#x916;&#x094d;',\
	'g':'&#x917;&#x094d;',\
	'V':'&#x918;&#x094d;',\
	'G':'&#x919;&#x094d;',\
	'c':'&#x91A;&#x094d;',\
	'C':'&#x91B;&#x094d;',\
	'j':'&#x91C;&#x094d;',\
	'Y':'&#x91D;&#x094d;',\
	'J':'&#x91E;&#x094d;',\
	'T':'&#x91F;&#x094d;',\
	'q':'&#x920;&#x094d;',\
	'D':'&#x921;&#x094d;',\
	'Q':'&#x922;&#x094d;',\
	'N':'&#x923;&#x094d;',\
	't':'&#x924;&#x094d;',\
	'w':'&#x925;&#x094d;',\
	'd':'&#x926;&#x094d;',\
	'W':'&#x927;&#x094d;',\
	'n':'&#x928;&#x094d;',\
	'p':'&#x92A;&#x094d;',\
	'P':'&#x92B;&#x094d;',\
	'b':'&#x92C;&#x094d;',\
	'B':'&#x92D;&#x094d;',\
	'm':'&#x92E;&#x094d;',\
	'y':'&#x92F;&#x094d;',\
	'r':'&#x930;&#x094d;',\
	'rSTi':'&#x0930;&#x094d;&#x0937;&#x094d;&#x091f;&#x093f;',\
	'l':'&#x932;&#x094d;',\
	'v':'&#x935;&#x094d;',\
	'z':'&#x936;&#x094d;',\
	'S':'&#x937;&#x094d;',\
	's':'&#x938;&#x094d;',\
	'h':'&#x0939;&#x094d;',\
	"'":'&#x093D;',\
	':':':',\
	'?':'?',\
	'_':'_',\
	'-':'-',\
	';':'&#x0964;',\
	' ':' ',\
	}
	
svara='faAiIuUeEoORFLX' # f for aum
MH='MH' # anusvAra visarga
vyaJjana='kKgVGcCjYJTqDQNtwdWnpPbBmyrlvzSsh'
pause=';'
signs='_-?;,. '+'\n'+'0123456789'

def treat1syl(syl):
	if syl in svara:
		return svaraDict.get(syl,'')
	elif syl in vyaJjana:
		return vyaJjanaDict.get(syl,'')
	elif syl in MH:
		return MHDict.get(syl,'')
	elif syl in pause:
		return vyaJjanaDict.get(syl,'')
	elif syl in signs:
		return syl
		
def treat2syl(syl):
	if ((syl[1] in svara and syl[1]!='a') and 
		(syl[0] in vyaJjana)):
		return devDict.get(syl[0],'')+mAtrADict.get(syl[1],'')
	elif ((syl[1]=='a') and 
		(syl[0] in vyaJjana)):
		return devDict.get(syl[0])
	elif (syl[1] in MH) and (
		syl[0] in svara):
		return svaraDict.get(syl[0])+MHDict.get(syl[1])
	else:
		return '??'
			
def treat3syl(syl):
	if (syl[2] in svara) and (
		syl[2]!='a'): #vvs vaJjana-vyaJjana-svara except 'a'
		return vyaJjanaDict.get(syl[0])+devDict.get(
			syl[1])+mAtrADict.get(syl[2])
	elif syl[2]=='a': #vva
		return (vyaJjanaDict.get(syl[0])+devDict.get(
			syl[1]))
	elif ((syl[2] in MH) and (syl[1] in svara)):
		if (syl[1] !='a'):
			return (devDict.get(syl[0])+mAtrADict.get(
				syl[1])+MHDict.get(syl[2]))
		elif (syl[1]=='a'):
			return (devDict.get(syl[0])+
				MHDict.get(syl[2]))
		else:
			return '???'
	
	else:
		return '???'

def treat4syl(syl):
	return vyaJjanaDict.get(syl[0])+treat3syl(syl[1:])
	
def treat5syl(syl):
	return vyaJjanaDict.get(syl[0])+treat4syl(syl[1:])

def treat6syl(syl):
	return vyaJjanaDict.get(syl[0])+treat5syl(syl[1:])

def treatOneSyllable(syl):
#takes one syllable and 
#returns the corresponding devanAgarI unicode string
	devSyl=syl
	if len(syl)==1:
		devSyl=treat1syl(syl)
	elif len(syl)==2:
		devSyl=treat2syl(syl)
	elif len(syl)==3:
		devSyl=treat3syl(syl)
	elif len(syl)==4:
		devSyl=treat4syl(syl)
	elif len(syl)==5:
		devSyl=treat5syl(syl)
	elif len(syl)==6:
		devSyl=treat6syl(syl)
	return devSyl

def xlate_a_word_from_HK_to_dev_for_web(word_in_HK):
	syl_str_CC=get_syllables(x_HK_to_CC(word_in_HK))
	dev_str="".join([treatOneSyllable(s) for s in syl_str_CC.split('x') if s])
	return dev_str

def xlate_many_words_from_HK_to_dev_for_web(words_list_HK):
	return [xlate_a_word_from_HK_to_dev_for_web(w) for w in words_list_HK]
	
def xlate_sentence_from_HK_to_dev_for_web(sen_in_HK):# no tags
	words_list_HK=sen_in_HK.split()
	print(str(words_list_HK))
	return " ".join(xlate_many_words_from_HK_to_dev_for_web(words_list_HK))
#Unicode to HK	
DICT_UNI_HK = {'ā':'A','Ā':'A','ī':'I','Ī':'I','ū':'U','Ū':'U',\
	'ṛ':'R','Ṛ':'R','ṝ':'RR','ḷ':'L','Ḷ':'L','ḹ':'LL',\
	'ṃ':'M','Ṃ':'M','ḥ':'H','Ḥ':'H','ṅ':'G','Ṅ':'G',\
	'ñ':'J','Ñ':'J','ṭ':'T','Ṭ':'T','ḍ':'D','Ḍ':'D',\
	'ṇ':'N','Ṇ':'N','ś':'z','Ś':'z','ṣ':'S','Ṣ':'S',
	} 

def x_UNI_to_HK(in_str_UNI): # input: 
	xlator_Obj = Xlator(DICT_UNI_HK)
	return xlator_Obj.xlate(in_str_UNI)	

DICT_UNI_SL1 = {'ph':'P','bh':'B','ḍh':'Q','th':'T',"Th":'T','ṭh':'W','ch':'C','kh':'K',\
        'gh':'G','jh':'J','dh':'D','ai':'E','au':'O',\
        'ā':'A','Ā':'A','ī':'I','Ī':'I','ū':'U','Ū':'U',\
	'ṛ':'f','Ṛ':'f','ṝ':'F','ḷ':'x','Ḷ':'x','ḹ':'X',\
	'ṃ':'M','Ṃ':'M','ḥ':'H','Ḥ':'H','ṅ':'N','Ṅ':'N',\
	'ñ':'Y','Ñ':'Y','Ṭ':'w','ḍ':'q','Ḍ':'q',\
	'ṇ':'R','Ṇ':'R','ś':'S','Ś':'S','ṣ':'z','Ṣ':'z','ṭ':'w',
	} 

def x_UNI_to_SL1(in_str_UNI): # input: 
	xlator_Obj = Xlator(DICT_UNI_SL1)
	return xlator_Obj.xlate(in_str_UNI)	
