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
