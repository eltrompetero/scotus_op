DATADR = '/home/anna/fast/scotus_big'

# ====================================================================================== #
# Preprocessing raw data files such as from CourtListener.
# Author: Eddie Lee, edlee@csh.ac.at
# ====================================================================================== #
from html2text import html2text
import os
import json
import re
from string import punctuation
from spacy.lang.en import English

import enchant


def extract_plain_txt():
    """Iterate thru all JSON raw files and extract plain text for each json from HTML
    if plain_text field doesn't already exist.
    """

    files = [i for i in os.listdir(DATADR+'/original_json')]

    for f in files:
        # load json
        with open(f'{DATADR}/original_json/{f}', 'r') as fpipe:
            jtext = json.load(fpipe)
            
        # either extract plain text (if it already exists) or extract from HTML
        if jtext['plain_text']:
            out_text = jtext['plain_text']
        elif jtext['html']:
            out_text = html2text(jtext['html'])
        else:
            print("No text.")
            out_text = ''
            
        if out_text:
            with open(f'{DATADR}/extracted_text/{f.split(".")[0]}.txt', 'w') as fout:
                fout.write(out_text)

def split_by_sub_op(text):
    """Split given opinion text by start of dissenting or concurring opinions using a
    simple lookup table.

    Assumes that concurrences come before dissents.

    Parameters
    ----------
    text : str

    Returns
    -------
    list of str
    """
    
    
    
    labels = ['maj']
    
    # put into list of text split into sections
    text = re.split(r'(\n.*[A-Z]{3,}.{0,10}concurring\.{,1}[ ]*\n)', text)
    if len(text)!=1:
        # combine sections that all belong to the same concurrence
        # 0th item is majority op, so start looking for concurrences afterwards
        conc_text = [text[1]]
        labels.append('conc')
        # standardize sub-op header for matching later
        cheaders = [standardize_header(text[1])]
        conc_head = cheaders[-1]
        for i in range((len(text)-1)//2):
            if conc_head==standardize_header(text[i*2+1]):
                conc_text[-1] += text[(i+1)*2]
            else:
                conc_head = standardize_header(text[i*2+1])
                if conc_head in cheaders:
                    # combine everything from that point in the past onwards
                    ix = cheaders.index(conc_head)
                    conc_text[ix] = ''.join(conc_text[ix:])+text[(i+1)*2]

                    del conc_text[ix+1:]
                    del labels[ix+2:]
                    del cheaders[ix+1:]
                else:
                    conc_text.append(text[i*2+1]+text[(i+1)*2])
                    labels.append('conc')
        text = text[:1]
        text.extend(conc_text)
    
    # same process for dissents (presuming they come after)
    dtext = re.split(r'(\n.*[A-Z]{3,}.{0,10}dissenting\.{,1}[ ]*\n)', text[-1])
    if len(dtext)==1:
        return (labels,text)
    text[-1] = dtext[0]

    # combine sections that all belong to the same concurrence
    # 0th item is majority op, so start looking for concurrences afterwards
    dlabels = ['dis']
    dis_text = [dtext[1]]
    dheaders = [standardize_header(dtext[1])]
    dis_head = dheaders[-1]
    for i in range((len(dtext)-1)//2):
        if dis_head==standardize_header(dtext[i*2+1]):
            dis_text[-1] += dtext[(i+1)*2]
        else:
            dis_head = standardize_header(dtext[i*2+1])
            # check that this head has not already appeared in the past
#             print(dis_head)
            if dis_head in dheaders:
                # combine everything from that point in the past onwards
                ix = dheaders.index(dis_head)
                dis_text[ix] = ''.join(dis_text[ix:])+dtext[(i+1)*2]
                
                del dis_text[ix+1:]
                del dlabels[ix+1:]
                del dheaders[ix+1:]
            else: 
                dis_text.append(dtext[i*2+1]+dtext[(i+1)*2])
                dlabels.append('dis')
    dtext = dtext[:1]
    text.extend(dis_text)
    labels.extend(dlabels)

    return (labels,text)

def standardize_header(s):
    return ''.join(s.split()).replace(',', '').replace('.', '')

def start_at_start(text):

#     t1 = text.replace('\n',' ')
#     text.replace(/\s*/g,"").match(/mycats/g)
    s1 = r'((d'
    s = 'eliveredtheopinion|announcedthejudgement)oftheCourt)'
    s = s1+s.replace('','\\s*')
#     print(s)
#     s = '((delivered the opinion|announced the judgement) of the Court)'
#     s = s.replace('','\\s*')
    text = re.split(s, text)
#     text = re.split(r'(\n.*[A-Z]{3,}.{0,10}concurring\.{,1}[ ]*\n)', text)
    if (len(text) <4):
        return False
#     print(''.join(text[0:2])[-200:])
#     return ''.join(text[3:])
    num = (len(text)-1)//3
        
    return text[-1],num

def cut_weird_conc(sents):
    phrase = r'(((it be |reversed and |)so order$)|it be so order)'
    
#     print(phrase)
   # |(judge?ment|conviction|decision).{,80}be affirm|be affirm(ed)?$'#(.|\n)*concur'
#     "^(reversed and )?so order$"
#     print(s)
#     s = '((delivered the opinion|announced the judgement) of the Court)'
#     s = s.replace('','\\s*')
    not_found = True
    i = 0
    # finds the first one
    while (not_found and i <len(sents)):
#         print(sents[i])
        if re.search(phrase, sents[i]):
            not_found = False
            
        i += 1
        
#     print(i)
    if (i == len(sents) and not_found):
        return sents, False
    return sents[:i-1], True

def cut_lines(sents): 
    phrase = r'the sya?llabus constitute no part of the opinion of the court but have be prepare by the reporter of decisions for the con ?venience of the reader {0,3}$|see united states v detroit lumber co  ?200 u ?s 321 337|see united states v detroit timber  lumber co'
    phrase2 = r'opinion of the court'
    not_found = True
    i = 0
    inds = []
    # finds the first one
    while (i <len(sents)):
#         print(sents[i])
        if re.search(phrase, sents[i]):
            not_found = False
            inds.append(i)
        sents[i] = re.sub(phrase2,'',sents[i])
            
        i += 1
        
#     print(i)
    if (not_found):
        
        return sents, False
        

    for i in inds:
        
        sents[i] = ''
    return sents, True
#     return sents[:i-1]+sents[i+1:], True

def cut_lemmatized_syllabus(sents):
#     t1 = text.replace('\n',' ')
#     text.replace(/\s*/g,"").match(/mycats/g)
#     s1 = r'((d'
#     s = 'eliveredtheopinion|announcedthejudgement)oftheCourt)'
#     s = s1+s.replace('','\\s*')
    phrase = r'(deliver|announce) the (opinion|judge?ment) (for a unanimous|of the|for the) court'
#     print(s)
#     s = '((delivered the opinion|announced the judgement) of the Court)'
#     s = s.replace('','\\s*')
    not_found = True
    i = len(sents) - 1
    while (not_found and i > -1):
#         print(sents[i])
        if re.search(phrase, sents[i]):
            not_found = False
            
        i -= 1
    if (i == -1 and not_found):
        return sents, False
    return sents[i+2:], True


#     garbage


    for i in range(len(sents)):
        if s in sents[i]:
            occs.append(i)
#     text = re.split(s, text)
#     text = re.split(r'(\n.*[A-Z]{3,}.{0,10}concurring\.{,1}[ ]*\n)', text)
    if (len(occs) <1):
        return False
#     print(''.join(text[0:2])[-200:])
#     return ''.join(text[3:])
        
    return sents[occ[-1]+1:],len(occs)

def start_at_start(text):

#     t1 = text.replace('\n',' ')
#     text.replace(/\s*/g,"").match(/mycats/g)
    s1 = r'((d'
    s = 'eliveredtheopinion|announcedthejudgement)oftheCourt)'
    s = s1+s.replace('','\\s*')
#     print(s)
#     s = '((delivered the opinion|announced the judgement) of the Court)'
#     s = s.replace('','\\s*')
    text = re.split(s, text)
#     text = re.split(r'(\n.*[A-Z]{3,}.{0,10}concurring\.{,1}[ ]*\n)', text)
    if (len(text) <4):
        return False
#     print(''.join(text[0:2])[-200:])
#     return ''.join(text[3:])
    num = (len(text)-1)//3
        
    return text[-1],num

def preprocess_plain_txt_op(text):
    """Clean up plain text and turn it into sentences.

    Parameters
    ----------
    text : str

    Returns
    -------
    str
    """

    # configure auto parsing
    nlp = English()
    nlp.add_pipe('sentencizer')
    nlp.add_pipe('lemmatizer', config={'mode':'lookup'})
    nlp.initialize()

    doc = nlp(text)

    cleaned_text = []
    for s in doc.sents:
        # lemmatized
        t = s.lemma_

        # remove new string
        t = t.replace('\n', ' ')

        # remove punc
        t = ''.join([i for i in t if not i in punctuation])

        # check if mostly capital letters or mostly numbers
        count = sum([1 for i in t if i.isupper() or i in '0123456789'])

        # removed starting number + space (page no.?)
        t = re.sub('^[0-9]*\s*', '', t)

        if count<(.3*len(t)) or len(t)-count>5:
            cleaned_text.append(t.lower())
#         else:
#             print(t)
#             print('\n')
            
    return cleaned_text

def combine_split_words(text):
    en_dict = enchant.Dict("en_US")
    
    lines = [el.strip() for el in text.split('\n')]
    revised_text = [lines[0]]

    # concatenate two lines with one another assuming that a word is split over them
    # if (1) the first and last words are not words, (2) one is not a word and the 
    # concatenation is (ignoring punctuation and empty lines)
    # TODO: footnotes not handled
    for i in range(1, len(lines)):
        appended = False

        if lines[i-1] and lines[i]:
            last_word = lines[i-1].split(' ')[-1]
            first_word = lines[i].split(' ')[0]

            if not '.' in last_word and not ';' in last_word:
                last_word = ''.join([i for i in last_word if not i in punctuation])
                first_word = ''.join([i for i in first_word if not i in punctuation])

                if last_word and first_word:
                    # scenario where one has to concat to prev line
                    last_is_real = en_dict.check(last_word)
                    first_is_real = en_dict.check(first_word)            

                    if not last_is_real and not first_is_real:
                        revised_text[-1] += lines[i]
                        appended = True
                    else:
                        concat = last_word + first_word
                        concat_is_real = en_dict.check(concat)
                        if concat_is_real:
                            revised_text[-1] += lines[i]
                            appended = True
        if not appended:
            revised_text.append(lines[i])
    return revised_text
