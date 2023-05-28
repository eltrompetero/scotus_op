import glob
from utils import split_sentences

import api

import logging
import pandas as pd
from gensim.models import Doc2Vec
import pickle
import requests

from df_params import *

from utils import OpinionDocumentsIterable

def prepare_data():
    write_to_sentence_files('../../fast/cl_scotus/opinions/*.json')
    
def train_model():
    config = api.AnalysisConfig(sentences_root_dir='../../fast/cl_scotus/txt_opinions')
    
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    doc_iter = OpinionDocumentsIterable(config.sentences_root_dir, minimal_flag=False)
    with open(config.model_pathsfile_path, 'wb') as out:
        pickle.dump(doc_iter.paths, out)
    model = Doc2Vec(doc_iter, vector_size=512, workers=4)

    model.save(config.model_path)
    
def get_var(path_to_json,var,next_var):
    with open(path_to_json,'r') as f_read:
        file_string = f_read.read()
        idx1 = file_string.find('"'+var+'": ')
        idx2 = file_string.find('"'+next_var+'":')
        if (idx1 == -1 or idx2 == -1):
            print("File not in proper format: " + path_to_json)
            return None
        # changed based on other import 
        
        plain_text = file_string[idx1+len(var)+4:idx2]
        plain_text = plain_text[:plain_text.rfind(',')]
        return plain_text
    
def get_var_from_text(file_string,var,next_var):

        idx1 = file_string.find('"'+var+'":')
        idx2 = file_string.find('"'+next_var+'":')
        if (idx1 == -1 or idx2 == -1):
#             print("File not in proper format: " + path_to_json)
            return None
        # changed based on other import 
        
        plain_text = file_string[idx1+len(var)+3:idx2]
        plain_text = plain_text[:plain_text.rfind(',')]
        return plain_text

def get_plain_text(path_to_json,old):
    with open(path_to_json, 'r') as f_read:
        file_string = f_read.read()
        idx1 = file_string.find('"plain_text": "')
        idx2 = file_string.find('"html":')
        if (idx1 == -1 or idx2 == -1):
            print("File not in proper format: " + path_to_json)
            return None
        # changed based on other import 
        if old:
            plain_text = file_string[idx1+14:idx2-4]
        else:
            plain_text = file_string[idx1+14:idx2-8]
        return plain_text
    
# writes all the json files with plain text attributes to text files in a new folder with each sentence on a new line
def write_to_sentence_files(path_to_dir,path_to_txt,old):
#     print(path_to_txt)
    # this is the place they are currently located: '../../fast/cl_scotus/opinions/*.json'
    json_files = glob.glob(path_to_dir)
    tot_files = len(json_files)
    num_files = tot_files
    counter = 0
    for i in range(num_files):
        pt = get_plain_text(json_files[i],old)
        if (pt != '""' and pt != None):
            counter += 1
            if not old:
                name = json_files[i][30:-5]
            else:
                name = json_files[i][29:-5]
            with open(path_to_txt + name + ".txt",'w') as f_write:
                sp = split_sentences(pt[1:-1])
                f_write.write(sp)
    print("total files: " + str(tot_files))
    print("total files parsed: " + str(num_files))
    print("with plain text: " + str(counter))
    print("percent: " + str(counter/num_files*100)+"%")
    
def count_files(path_to_dir,var,next_var,old,all_files=False):
#     print(path_to_txt)
    # this is the place they are currently located: '../../fast/cl_scotus/opinions/*.json'
    json_files = glob.glob(path_to_dir)
    tot_files = len(json_files)
    if all_files:
        num_files = tot_files
    else:
        num_files = 100#tot_files
    file_list = []
    counter = 0
    for i in range(num_files):
        ptxt = get_var(json_files[i],'plain_text','html')
        if (ptxt != '""' and ptxt != None and ptxt != 'null'):
            pt = get_var(json_files[i],var,next_var)
            if (pt != '""' and pt != None and pt != 'null'):
                counter += 1
                if not old:
                    name = json_files[i][30:-5]
                else:
                    name = json_files[i][29:-5]
                file_list.append([name[9:],pt])
                if (not all_files):
                    print(pt)
                    print(name)
    print("total files: " + str(tot_files))
    print("total files parsed: " + str(num_files))
    print("with variable: " + str(counter))
    print("percent: " + str(counter/num_files*100)+"%")
    return file_list

def has_aol(path_to_dir,all_files=False):
    json_files = glob.glob(path_to_dir)
    tot_files = len(json_files)

    if all_files:
        num_files = tot_files
    else:
        num_files = 100#tot_files
        
    file_list = []
    counter = 0
    c=0
    
    for i in range(num_files):
        c+=1
        pt = get_var(json_files[i],'plain_text','html')
        
        if (pt != '""' and pt != None and pt != 'null'):
            print(c)
            name = json_files[i][30:-5]
            cluster = get_var(json_files[i],'cluster','author')
            
            res = requests.get(cluster[1:-1])
            
#             print(res.text)
            
            scdb_id = get_var_from_text(res.text,'scdb_id','scdb_decision_direction')
            if (scdb_id != '""' and scdb_id != None and scdb_id != 'null'):
                counter += 1
#                 print(scdb_id)
                file_list.append([name[9:],scdb_id])
                
                print(scdb_id)
                print(name)
    print("total files: " + str(tot_files))
    print("total files parsed: " + str(num_files))
    print("with variable: " + str(counter))
    print("percent: " + str(counter/num_files*100)+"%")

    print(file_list)
    return file_list
    


# #     write_to_sentence_files('../../fast/scotus_big/scotus/*.json','../../fast/scotus_big/scotus_txt_opinions/',True)
# #     write_to_sentence_files('../../fast/cl_scotus/opinions/*.json','../../fast/cl_scotus/txt_opinions/',False)

   
# For the smaller dataset (in scotus)  
# total files: 14701 
# total files parsed: 14701
# with plain text: 1349
# percent: 9.176246513842596  

# For the larger dataset (in scotus dump)
# total files: 64344
# total files parsed: 64344
# with plain text: 1773
# percent: 2.7555016784781796