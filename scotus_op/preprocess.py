# ====================================================================================== #
# Preprocessing raw data files from CourtListener.
# Authors: Eddie Lee, edlee@csh.ac.at
#          Anna Eaton, aceaton@princeton.edu
# ====================================================================================== #
import os
import json
import re
from string import punctuation
from spacy.lang.en import English
from spacy.language import Language
from textpipe import doc, pipeline
import enchant
from . import path



def extract_plain_txt():
    """Iterate thru all JSON raw files and extract plain text for each json from HTML
    if plain_text field doesn't already exist. Do a little bit of format cleaning to
    the text from the PDF format that it came it.
    
    Saves the text into a text file for each case.
    """
    files = [i for i in os.listdir(path.data+'/scotus') if i.split('.')[-1]=='json']

    for f in files:
        # load json
        with open(f'{path.data}/scotus/{f}', 'r') as fpipe:
            jtext = json.load(fpipe)
            
        # either extract plain text (if it already exists) or extract from HTML
        if jtext['plain_text']:
            out_text = jtext['plain_text']
        elif jtext['html']:
            out_text = doc.Doc(jtext['html']).clean
        else:
            if 'certiorari is denied' in jtext['html_lawbox']:
                print(f"File {f} has no text. Certiorari denied.")
            elif 'is dismissed' in jtext['html_lawbox']:
                print(f"File {f} has no text. Appeal dismissed.")
            else:
                print(f"File {f} has no text.")

            out_text = ''
        
        # connect words split over row breaks, line breaks, and file end
        out_text = re.sub(r'-\\n+\s+', '', out_text).replace(r'\n', ' ').replace(r'\f', '')
        out_text = re.sub('\s+', ' ', out_text)

        # replace U. S. acronym with U.S.
        out_text = re.sub('U. S.', 'U.S.', out_text)

        # replace D. C. acronym with D.C. when it appears with Washington
        out_text = re.sub('Washington, D. C.', 'Washington D.C.', out_text)
        
        # punctuation changes
        # standardize ellipses to be ...
        out_text = re.sub('\s*\.\s*\.\s*\.\s*', '...', out_text)
        # remove quotation marks
        out_text = re.sub(r'[\"\']', '', out_text)
        # remove square brackets (as used in altered quotations)
        out_text = re.sub(r'[\[\]]', '', out_text)

        if out_text:
            with open(f'{path.data}/extracted_text/{f.split(".")[0]}.txt', 'w') as fout:
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
    text = re.split(r'([A-Z]{3,}.{0,10}concurring\.{,1}[ ]*)', text)
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
    dtext = re.split(r'([A-Z]{3,}.{0,10}dissenting\.{,1}[ ]*)', text[-1])
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

def cut_conclusion(sents):
    """Remove concluding remark when it's present.

    Parameters
    ----------
    sents : list str

    Returns
    -------
    list of str
    bool
        True if something was cut.
    """
    phrase = r'(((it be |reversed and |)so order$)|it be so order)'
    
    not_found = True
    i = 0
    # finds the first one
    while (not_found and i <len(sents)):
        if re.search(phrase, sents[i]):
            not_found = False
        i += 1
        
    if (i == len(sents) and not_found):
        return sents, False
    return sents[:i-1], True

def cut_lines(sents): 
    """Remove lines that have to do with Lumber case and say "opinion of the court".

    Parameters
    ----------
    sents : list of str

    Returns
    -------
    list of str
    bool
    """
    phrase = (r'the sya?llabus constitute no part of the opinion of the court but have be prepare '+
              'by the reporter of decisions for the con ?venience of the reader {0,3}$|see united '+
              'states v detroit lumber co  ?200 u ?s 321 337|see united states v detroit timber  '+
              'lumber co')
    phrase2 = r'opinion of the court'
    not_found = True
    i = 0
    inds = []

    # finds the first one
    while (i<len(sents)):
        if re.search(phrase, sents[i]):
            not_found = False
            inds.append(i)
        sents[i] = re.sub(phrase2,'',sents[i])
        i += 1
        
    if (not_found):
        return sents, False

    for i in inds:
        sents[i] = ''
    return sents, True

def cut_lemmatized_syllabus(sents):
    """Remove the syllabus header of the opinion. Only works after lemmatization.

    Parameters
    ----------
    sents : list of str

    Returns
    -------
    list of str
    bool
        True if the syllabus was detected.
    """
    phrase = (r'((deliver|announce) the ([oO]pinion|judge?ment) (for a unanimous|of the|for the) [cC]ourt|'+
              '[wW]e note probable jurisdiction under)')

    not_found = True
    i = len(sents) - 1
    while (not_found and i > -1):
        if re.search(phrase, sents[i]):
            not_found = False
        i -= 1
    if (i == -1 and not_found):
        return sents, False
    return sents[i+2:], True

def sentencize(text, return_filtered=False):
    """Sentencize and clean opinion text using spacy pipeline.

    Parameters
    ----------
    text : str
    return_filtered : bool, False
        If True, return sentences that were filtered b/c they were mostly citations.

    Returns
    -------
    list of str
        Lemmatized sentences.
    list of str (optional)
        Lemmatized sentences that were removed. This can be useful for debugging.
    """
    # configure auto parsing
    nlp = English()
    sent = nlp.add_pipe('sentencizer', config={'punct_chars':['.','?','!','"',';']})
    nlp.add_pipe('lemmatizer', config={'mode':'lookup'})
    nlp.initialize()
    doc = nlp(text)
    
    # loop through each sentence and clean them up
    cleaned_text = []
    filtered_text = []
    for s in doc.sents:
        # extract lemmatized sentence
        t = s.lemma_

        # remove new string
        t = t.replace('\n', ' ')

        # remove punctuation but only in words, e.g. acronyms
        t = re.sub(r'([a-zA-Z]+)[!#$%&\(\)*+,-./:;=@\[\\\]~]+([a-zA-Z])', r'\1\2', t)
        t = re.sub(r'([a-zA-Z]+)[,."]+', r'\1', t)
        t = re.sub(r'\"([a-zA-Z]+)', r'\1', t)

        # check if mostly capital letters or mostly numbers
        count = sum([1 for i in t if i.isupper() or i in '0123456789'])

        # removed starting number + space (page no.?)
        t = re.sub('^[0-9]*\s*', '', t)
        
        # don't consider some defective sentences pulled out by spacy
        if ' ' in t:
            cleaned_text.append(t.strip())

        # potentially unhelpful filtering
        #if count<(.3*len(t)) or len(t)-count>5:
        #    cleaned_text.append(t.strip())
        #else:
        #    filtered_text.append(t)
    
    if return_filtered:
        return cleaned_text, filtered_text
    return cleaned_text

def combine_split_words(text):
    """Fix words that have been split across lines of text (and expected to be
    hyphenated).

    Parameters
    ----------
    text : str

    Returns
    -------
    str
    """
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
    return revised_text[0]
