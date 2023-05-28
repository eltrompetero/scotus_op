import pandas as pd

import sys
sys.path.append('/home/anna/judiciary/nlp/')

from scotus_op.df_params import *

import glob
import os

import nlp.api

import logging
from gensim.models import Doc2Vec
import pickle
import requests

from nlp.utils import OpinionDocumentsIterable, preprocess_sentence

import nltk
nltk.download('punkt')
nltk.download('stopwords')

import numpy as np

import math

import matplotlib as mpl
import seaborn as sns
import matplotlib.pyplot as plt

import gensim.downloader as api
from gensim.models import TfidfModel
from gensim.corpora import Dictionary

from sklearn.feature_extraction.text import TfidfVectorizer

# cleaned_and_sentencized_path = '/home/anna/fast/scotus_big/sentence_text/'
# cleaned_folder = '/home/anna/fast/scotus_big/cleaned_text/'

def open_scdb():
    return pd.read_csv(scdb_path)

def open_df():
    return pd.read_pickle(pickle_df_path)

# shouldn't be called, the other one has the vectors now
def open_vdf():
    return pd.read_pickle(pickle_df_path_with_vecs)

def save_df(df):
    df.to_pickle(pickle_df_path)
    
def save_df_new(df):
    df.to_pickle(pickle_df_path_new)

def open_j():
    return pd.read_csv(justice_path)

def save_judge_vecs(df):
    df.to_pickle(judge_avg_vecs)
    
def open_judge_vecs():
    return pd.read_pickle(judge_avg_vecs)

def save_bow(df,idx=0):
    df.to_pickle(bow_path+str(idx))
    
def open_bow(idx=0):
    return pd.read_pickle(bow_path+str(idx))

def get_words(id_num):
    print(id_num)
#     path = cleaned_and_sentencized_path + 'final_' + str(id_num) + '.txt'
    path = cleaned_and_sentencized_path + str(id_num) + '.txt'

    try:
        with open(path,'r') as opinion_file:
            words = [w for sentence in opinion_file.readlines() for w in
                             preprocess_sentence(sentence)]
        return words
    except FileNotFoundError:
        return None
        

# def open_plain_text(idx):
#     a = ""
#     with open(

def train_model():
#     config = nlp.api.AnalysisConfig(sentences_root_dir=cleaned_and_sentencized_path,model_path = 'models/d2v_modelclean',model_pathsfile_path = 'models/d2v_modelclean_paths')
#     '../../fast/cl_scotus/txt_opinions')
    config = nlp.api.AnalysisConfig(sentences_root_dir=cleaned_and_sentencized_path)

    print(config)
    
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    doc_iter = OpinionDocumentsIterable(config.sentences_root_dir, minimal_flag=False)
    
    with open(config.model_pathsfile_path, 'wb') as out:
        pickle.dump(doc_iter.paths, out)
    model = Doc2Vec(doc_iter, vector_size=512, workers=4)
    
    model.save(config.model_path)
#     model.save(model_path)
    
# def train_bow():
    
    
def make_sentence_files():
    text_files = glob.glob(cleaned_folder+'*.txt')
    tot_files = len(text_files)
#     print(tot_files)
    num_files = tot_files
    counter = 0
    for i in range(num_files):
        if (i%1000==0): print(str(i)+'/'+str(tot_files))
        with open(text_files[i],'r') as f_read:
            f_string = f_read.read()
            sp = split_sentences(f_string)
            name = text_files[i].split('/')[-1]
#             print(name)
            with open(cleaned_and_sentencized_path + "final_" + name,'w') as f_write:
                f_write.write(sp)
            
# format string with sentences on new lines
def split_sentences(str_to_split):
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    tk = tokenizer.tokenize(str_to_split)
    return '\n'.join(tk)

def get_judge_vectors(df):
    
    norm=False
    
#     df = df.iloc[:10]
    
#     config = nlp.api.AnalysisConfig()
    config = nlp.api.AnalysisConfig(sentences_root_dir=cleaned_and_sentencized_path)#,model_path = 'models/d2v_modelclean',model_pathsfile_path = 'models/d2v_modelclean_paths')
    
    model = Doc2Vec.load(config.model_path)
    
    def get_judge_vector(entry):
        words = get_words(entry)
        if words == None:
            return None
        
        if norm:
            ar = model.dv.get_normed_vectors(words)
        else:
            ar = model.infer_vector(words)
#         print(type(ar))
        return ar


#     jvecs = api.get_judge_vectors_new(config)
    
    vecs = df['id'].apply(get_judge_vector)
    
    return vecs

def update_df_with_vecs():
    df = open_df()
#     df = df.iloc[:30]
#     print(df)
    vs = get_judge_vectors(df)
    df['norm'] = vs
    save_df_new(df)
    
    
def populate_from_scdb(df):
    scdb_df = open_scdb()
    c = df.columns
    
    for key in db_attrs_from_scdb:
        if (key not in c):
            df[key] = np.nan
#             print("added")
    
    def add_attrs(row):
#         print(row)
        if (row['scdb_id'] != ""):
#             print(row.id)
            
            scdb_row = scdb_df.loc[scdb_df['caseId']==row['scdb_id']]
#             print(scdb_row['majOpinWriter'])
#             print(scdb_row)
            for a in db_attrs_from_scdb:
#                 print(a)

#                 print(scdb_row[a])
                try:
                    row[a] = scdb_row[a].values[0]
                except:
                    row[a] = math.nan
#                 print(scdb_row[a].values)
#                 print(type(scdb_row[a]))
                
#                 print("attr")
#                 print(scdb_row[a])
        return row
        
    df = df.apply(add_attrs,axis=1)
    
    return df

def get_shared_tenure2(j1,j2):
    if (j1>j2):
        s = j2
        j2=j1
        j1=s
#     print(j1)
    s1 = jdf.iloc[j1]['year_on']
#     print(j2)
    s2 = jdf.iloc[j2]['year_on']
    e1 = jdf.iloc[j1]['year_off']
    e2 = jdf.iloc[j2]['year_off']
    assert s1<=s2
    if (s2>=e1): return e1-s2 # negative cuz they didn't overlap
    x = min(e2-s2,e1-s2) # positive cuz they did
    return x

def get_sim(v1,v2):
    if np.isnan(v1).any() or np.isnan(v2).any():
        return np.nan
    vn1 = v1/np.linalg.norm(v1)
    vn2 = v2/np.linalg.norm(v2)
    return np.dot(vn1,vn2)

def make_grid(arr):
    return nlp.api.get_judge_similarity_matrix(arr)

def plot_grid(sim_mat,jlabels=None):
    mpl.rcParams['figure.dpi'] = 600
    mpl.rcParams['axes.labelsize'] = 'x-large'
    ax = sns.heatmap(sim_mat, square=True)
#     ax.set(xlabel='judge', ylabel='judge')
    # ax.set_xticks(labels=labels)
    # ax.set_yticks(labels=labels)
    plt.autoscale(enable=False)
    # plt.locator_params(axis="x", nbins=len(jlabels))
    # plt.locator_params(axis="y", nbins=len(jlabels))
#     print(jlabels-jlabels[0])
    if jlabels:
        ax.set(xticks=jlabels-jlabels[0],yticks=jlabels-jlabels[0])
        ax.set_xticklabels(jlabels)
        ax.set_yticklabels(jlabels)
    ax.tick_params(labelsize='x-small')
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)
#     plt.savefig('js.png')
    plt.show()
    return plt

class OpinionStringsIterable:
    def __init__(self, root_dir, minimal_flag):
        self.paths = list(glob.iglob(os.path.join(root_dir, '**/*.txt'), recursive=True))
        self.minimal_flag = minimal_flag
        self.df = open_df()

    def __iter__(self):
        return self.get_opinion_documents()
    
    def check_if_scdb(self,doc_id):
        if doc_id in self.df.index:
            return True
        return False

    def get_opinion_documents(self):
        c = 0
        for i, p in enumerate(self.paths):
            if i%1000==0:
                print(i)
#             print(p)
#             if i>2000:
#                 break
            doc_id = p.split('/')[-1].split('.')[0]
            if self.check_if_scdb(doc_id):
                c+=1
                with open(p, 'r', encoding='utf-8') as opinion_file:
    #                 words = [w for sentence in opinion_file.readlines() for w in
    #                          preprocess_sentence(sentence, self.minimal_flag)]
    #                 yield TaggedDocument(words=words, tags=[i])
                      yield opinion_file.read()
        print(c)
#end OpinionDocumentsIterable

def tf_idf_model(ngrams=(1,2),max_feat=1000,doc_iter=None):
    
    config = nlp.api.AnalysisConfig(sentences_root_dir=cleaned_and_sentencized_path)
#     '../../fast/cl_scotus/txt_opinions')
    
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    if doc_iter==None:
        doc_iter = OpinionStringsIterable(config.sentences_root_dir, minimal_flag=False)
    
    vectorizer = TfidfVectorizer(ngram_range=ngrams,max_features=max_feat,stop_words='english')
    vectors = vectorizer.fit_transform(doc_iter)
    feature_names = vectorizer.get_feature_names()
    dense = vectors.todense()
    denselist = dense.tolist()
    df = pd.DataFrame(denselist, columns=feature_names)

#     dataset = api.load("text8")
# >>> dct = Dictionary(dataset)  # fit dictionary
# >>> corpus = [dct.doc2bow(line) for line in dataset]  # convert corpus to BoW format
    
#     corpus = doc_iter
#     model = TfidfModel(corpus)  # fit model
#     vector = model[corpus[0]]  # apply model to the first corpus document

    return df


#     print(df)
    
#     normed_vectors = model.dv.get_normed_vectors()

# #     def create_judge_vector(x):
# #         print(x)
# #         vecs = normed_vectors(x)
# #         vecs = x.apply(normed_vectors)
# #         return vecs.mean(axis=0)

#     auth_df = auth_df.astype({0: int, 1: str, 'vec':np.ndarray})
#     judge_vecs = auth_df.groupby(1)['vec'].mean() #.astype(float)
    
#     print(judge_vecs)
    
#     grouped_df = auth_df.groupby(0)
#     print(grouped_df)
    
#     new_df = grouped_df.apply(lambda x: (x[1]).mean())
#     print(new_df)

# def get_clusters():

def vstd(x):
    return np.std(x['vec'])
    
def vmean(x, param='vec'):
#     print(x)
    return np.mean(x[param])

def bmean(x,param='bow_vec'):
    return np.mean(x[param])

def get_shared_tenure(j1,j2):
    if (j1>j2):
        s = j2
        j2=j1
        j1=s
#     print(j1)
    s1 = jdf.iloc[j1]['year_on']
#     print(j2)
    s2 = jdf.iloc[j2]['year_on']
    e1 = jdf.iloc[j1]['year_off']
    e2 = jdf.iloc[j2]['year_off']
    assert s1<=s2
    if (s2>=e1): return None#return max(2*(e1-s2)/(e1+e2-s1-s2),-1) # negative cuz they didn't overlap
    x = min(e2-s2,e1-s2) # positive cuz they did
    return 2*x/(e1+e2-s1-s2)

def get_shared_tenure_not_norm(j1,j2):
    if (j1>j2):
        s = j2
        j2=j1
        j1=s
#     print(j1)
    s1 = jdf.iloc[j1]['year_on']
#     print(j2)
    s2 = jdf.iloc[j2]['year_on']
    e1 = jdf.iloc[j1]['year_off']
    e2 = jdf.iloc[j2]['year_off']
    assert s1<=s2
    if (s2>=e1): return e1-s2 # negative cuz they didn't overlap
    x = min(e2-s2,e1-s2) # positive cuz they did
    return x
