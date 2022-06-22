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

from .dir import DATADR


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

def preprocess_plain_txt_op(text):
    """Clean up plain text and turn it into sentences.

    Parameters
    ----------
    text : str

    Returns
    -------
    str
    """
    
    # remove page headers which typically consist of a new line preceded by a line break
    text = ''.join(re.split(r'\x0c.*\n', text))

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

        # remove new strings that simply split words onto two lines
        t = t.replace('-\n', '')

        # remove new string
        t = t.replace('\n', ' ')

        # remove punc
        t = ''.join([i for i in t if not i in punctuation])

        # check if mostly capital letters or mostly numbers
        count = sum([1 for i in t if i.isupper() or i in '0123456789'])

        # removed starting number + space (page no.?)
        t = re.sub('^[0-9]*\s*', '', t)

        if count<(.3*len(t)):
            cleaned_text.append(t.lower())
            
    return cleaned_text
