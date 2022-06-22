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

from .dir import *


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
    
    # put into list of text split into sections
    text = re.split(r'(\n        [ ]+.*(?!\n.*)concurring.*\n)', text)
    if len(text)==1:
        return text

    # combine sections that all belong to the same concurrence
    # 0th item is majority op, so start looking for concurrences afterwards
    conc_text = [text[1]]
    # standardize sub-op header for matching later
    conc_head = standardize_header(text[1])
    for i in range((len(text)-1)//2):
        if conc_head==standardize_header(text[i*2+1]):
            conc_text[-1] += text[(i+1)*2]
        else:
            conc_head = standardize_header(text[i*2+1].split())
            conc_text.append(text[(i+1)*2])
    text = text[:1]
    text.extend(conc_text)

    # same process for dissents (presuming they come after)
    dtext = re.split(r'(\n        [ ]+.*(?!\n.*)dissenting.*\n)', text[-1])
    if len(dtext)==1:
        return text

    # combine sections that all belong to the same concurrence
    # 0th item is majority op, so start looking for concurrences afterwards
    dis_text = [dtext[1]]
    dis_head = standardize_header(dtext[1])
    for i in range((len(dtext)-1)//2):
        if dis_head==standardize_header(dtext[i*2+1]):
            dis_text[-1] += dtext[(i+1)*2]
        else:
            dis_head = standardize_header(dtext[i*2+1].split())
            dis_text.append(dtext[(i+1)*2])
    dtext = dtext[:1]
    text.extend(dis_text)

    return text

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

        if count<(.3*len(t)):
            cleaned_text.append(t.lower())
            
    return cleaned_text
