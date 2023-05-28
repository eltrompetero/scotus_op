import pandas as pd
import glob
import json
import requests

import math

import fuzzywuzzy
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

import pickle

from df_params import *

# data frame for the scdb info
scdb_df = pd.read_csv(scdb_path)

def put_attrs_in_db(is_test=True):
    # make the pd db with all the attributes
#     df = pd.read_json(path)
    json_files = glob.glob(json_folder+'*.json')

    tot_files = len(json_files)
    
    cluster_files = glob.glob(cluster_path+'*.json')
    
    # strip json strings to make row names for df
    df_indices = [s[len(json_folder):-5] for s in json_files]
    
    if is_test:
        num_files = 2
    else:
        num_files = tot_files
    
    df = pd.DataFrame(columns = all_attrs, index = df_indices[:num_files])
#     print(df)
#     print(json_files[0])
    
    for i in range(num_files):
        if (i%100 == 0):
            print(i)
            print(num_files)
            print(i/num_files)
            print('')
        
#         print(json_files[i])
        row = df.iloc[i]
        
        # get the json object for the original file and get those attributes
        with open(json_files[i]) as f:
            jf = json.load(f)
        for a in db_attrs_from_op:
            row[a] = jf[a]
        
        # get the json object for the corresponding cluster and get those attributes
        cluster = jf['cluster']
        cluster = cluster.split('/')[-2]
        
        
        
        cluster = cluster_path + cluster + '.json'
        
        if cluster in cluster_files:
#             print(cluster)

            with open(cluster) as clust:
                jf_c = json.load(clust)
                jf_c = json.loads(jf_c)

                for a in db_attrs_from_cluster:
                    x = jf_c[a]
                    row[a] = x
        
    return df

def count_with_scdb(df):
    def has_scdb_id(entry):
        if (entry == ""): return 0
        return 1
    
    has_scdb = df['scdb_id'].apply(has_scdb_id)
    return has_scdb.mean()

def fill_scdb_ids(df,is_test=True):
    json_files = glob.glob(json_folder+'*.json')
    tot_files = len(json_files)
    
    # strip json strings to make row names for df
    df_indices = [s[len(json_folder):-5] for s in json_files]
    
    if is_test:
        num_files = 500
    else:
        num_files = tot_files
        
    new_ids = pd.DataFrame(columns = ['new_id','score'], index = df.index)
    new_ids = new_ids.iloc[:num_files,:]
    
    for i in range(num_files):   
        if (i%10==0): print(i)
        # match to scdb using various identifying information
        row=df.loc[df_indices[i]]

        if (type(row['date_filed']) != 'str'):
            if (row['scdb_id'] == ""):
                m = match_scdb(row)
                new_ids.loc[df_indices[i],'new_id'] = m[0]
                new_ids.loc[df_indices[i],'score'] = m[1]
#             if (row['scdb_id'] == ""):
#                 row['scdb_id'] = match_scdb(row)
#             if (row[scdb_id] != None):
#                 scdb_row = scdb_df.loc[scdb_df['caseId']==row[scdb_id]]
#                 for a in db_attrs_from_scdb:
#                     row[a] = scdb_row[a]
    return new_ids

def populate_from_scdb(df):
    def add_attrs(row):
        if (row['scdb_id'] != ""):
            scdb_row = scdb_df.loc[scdb_df['caseId']==row['scdb_id']]
            for a in db_attrs_from_scdb:
                row[a] = scdb_row[a]
    df.apply(add_attrs,axis=1)
    return df
    
def match_scdb(row):
    cs = row['citations']
#     print(cs)
#     print("\ncase info")
#     print("Case name: " + row['case_name'])
#     print("Case date: " + row['date_filed'])
#     print("SCDB id: " + row['scdb_id'])
#     print("Citations: ")
#     print(cs)
    
    # rate the strength of matches based on multiple factors:
    ms = pd.DataFrame(columns = list(cite_corr.keys())+['name','date','score'], index = scdb_df.index)
    
    for c in cs:
        r = c['reporter']
        str_to_match = str(c['volume'])+r+str(c['page'])
        str_to_match = str_to_match.replace(' ', '').lower()
        
        def match_str(entry):
#             print(str(entry).replace(' ', '').lower())
#             print(str_to_match+'\n')
            return str(entry).replace(' ', '').lower() == str_to_match
        
        if (r in cite_corr.keys()):
            ms[r] = scdb_df[cite_corr[r]].apply(match_str)
        
    def score_name(entry):
        a = row['case_name']
        b = entry
        c = row['case_name_full'].replace(' ', '').lower()
        e = a.replace(' ', '').lower()
        f = b.lower()
#         name = fuzz.ratio(a,b)
#         long = fuzz.partial_ratio(b,c)
        # we only want substrings in one direction
        if (len(b)<len(a)): name = fuzz.ratio(e,f)
        else: name = fuzz.partial_ratio(e,f)
        name = fuzz.token_set_ratio(a,b)
        return name
    
#     matches = process.extract(row['case_name'], scdb_df['caseName'], limit=100, scorer=score_name)
#     print(matches)
    ms['name'] = scdb_df['caseName'].apply(score_name)
    
    app = row['date_filed_is_approximate']
    
    def match_date(entry):
        a = row['date_filed']
        b = a.split('-')
        c = str(int(b[1]))+'/'+str(int(b[2]))+'/'+b[0]
        if app:
            return entry[-4:]==a[:4]
        return (entry==c)
                
    # maybe dateFiled? or dateArg or rearg
    ms['date'] = scdb_df['dateDecision'].apply(match_date)   
    
    # include approx in formula?
    def final_score(entry):
        if entry['U.S. LEXIS']==True: return 100
        a = entry['name']
        count = 0.1
        good = 0.1
        # count the number of correct citations
        for c in list(cite_corr.keys()):
            if (math.isnan(entry[c])==False):
                count += 1
                good += entry[c]==True
        a *= good/count
        if not entry['date']:
            a*=.8
        return a
    
    ms['score'] = ms.apply(final_score,axis=1)
    
#     return scdb_df.loc[ms['U.S.']]
#     return scdb_df.loc[ms['name']>96]

    idx = ms['score'].idxmax()
    sc = ms['score'].max()
    
    return [scdb_df.loc[idx,'caseId'],sc]
    
#     if (sc==100):
#         print("\nmax scored case:")
#         print(scdb_df.loc[idx,['caseName','dateDecision','caseId']])
#         print(scdb_df.loc[idx,'caseId'])

#         print("\nscores:")                                        
#         print(ms.loc[idx])
# #     print("max score: "+str(ms['name'].max()))
# #     print(scdb_df.loc[ms['name'].idxmax(),'caseName'])
# #     print(scdb_df.loc[ms['name']>80,'caseName'])
#     return None
# END MATCH SCDB METHOD




# put_attrs_in_db(True)
# df = put_attrs_in_db(False)
# df.to_pickle(pickle_df_path)


df = pd.read_pickle(pickle_df_path)
# print(df)
print('\nwith scdb ids')
print(count_with_scdb(df))

# match_scores = put_scdb_attrs(df,True)

# match_scores.to_pickle(id_df_path)

# print('\navg score')
# print(match_scores['score'].mean())

# def thresh(entry):
#     if (entry > 50): return 1
#     return 0
# print(match_scores['score'].apply(thresh).mean())


scores = pd.read_pickle(id_df_path)
print(scores)

# populate_from_scdb(df).to_pickle(pickle_df_path+'1')

# print(scdb_df['dateArgument'])
# print(scdb_df.columns)
# print(scdb_df.loc[0:2,['usCite','sctCite','ledCite','lexisCite']])
# put_attrs_in_db()


