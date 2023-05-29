# judge sim matrix with scotus data
import api
import pandas as pd
import json

import numpy as np

from gensim.models import Doc2Vec
from utils import AnalysisConfig, preprocess_sentence

def main():
    config = api.AnalysisConfig()
    
    model = Doc2Vec.load(config.model_path)
    
    auth_df = pd.read_json('file_list_author.txt')
    print(auth_df)
    
    partial_path = '../../fast/cl_scotus/txt_opinions/opinions_'
    
    auth_df = auth_df.iloc[: 10, :]
    
    def get_vec(row):
        
        path = partial_path + str(row[0]) + '.txt'
        with open(path,'r') as opinion_file:
            words = [w for sentence in opinion_file.readlines() for w in
                         preprocess_sentence(sentence)]
#             doc = TaggedDocument(words=words)
        
        ar = model.infer_vector(words)
        print(type(ar))
        return ar

#     jvecs = api.get_judge_vectors_new(config)
    
    auth_df['vec'] = auth_df.apply(lambda row: get_vec(row), axis=1)
    
#     with open('output.txt', 'w') as f:
#         for row in auth_df.to_dict('records'):
#             f.write(json.dumps(row) + '\n')
    
    normed_vectors = model.dv.get_normed_vectors()

#     def create_judge_vector(x):
#         print(x)
#         vecs = normed_vectors(x)
#         vecs = x.apply(normed_vectors)
#         return vecs.mean(axis=0)

    print(auth_df['vec'])
#     print(auth_df.groupby(1)['vec'])

#     return auth_df.groupby(1)['vec']
    auth_df = auth_df.astype({0: int, 1: str, 'vec':np.ndarray})
    judge_vecs = auth_df.groupby(1)['vec'].mean() #.astype(float)
    
    print(judge_vecs)
    
    grouped_df = auth_df.groupby(0)
    print(grouped_df)
    
    new_df = grouped_df.apply(lambda x: (x[1]).mean())
    print(new_df)
    
    

#     sim_matrix = api.get_judge_similarity_matrix(jvecs)

#     # We show a plot
#     plt = api.plot_judge_similarity_matrix(sim_matrix)
#     plt.show()

#     jvecs_names = api.associate_judge_vectors_with_fjc_names(config, jvecs)

#     print(jvecs_names.shape)
#     print(jvecs_names.head(10))

def get_judge_vecs_new(config: AnalysisConfig):
    model = Doc2Vec.load(config.model_path)
    
    gt = get_gt_new(config)
    
    v1 = model.infer_vector(test_data)
    
    def create_vec(x):
        vecs = model.dv.get_normed_vectors()
        return vecs.mean(axis=0) 

    judge_vecs = merged.groupby('judgeid')['vector_index'].apply(create_judge_vector)
    judge_vecs = judge_vecs.sort_index()

    return judge_vecs
        
    
def get_gt_new(config: AnalysisConfig, reduce_circuit=None):
    df = pd.DataFrame()
#     df['case'] = 
    
def get_opinion_level_ground_truth(config: AnalysisConfig, reduce_circuit=None):  # TODO proper ordering
    """
    NOTE: reduce circuit DOES MORE than reducing to the specified circuit (year and exactly one area annotation)
    :return: ground truth ordered according to the passed path file / the paths
    """
    df = pd.io.stata.read_stata(config.bloomberg_caselevel_path)

    with open(config.model_pathsfile_path, 'rb') as in_file:
        obj = pickle.load(in_file)
        sen_df = pd.DataFrame({'path': obj})
    split_paths = sen_df.path.str.replace('\\', '/', regex=False).str.split('/').str[-1].str.split('_')
    sen_df['case'] = split_paths.str[0]
    sen_df['opinion_type'] = split_paths.str[1]

    merged_df = sen_df.reset_index().merge(df, how='inner', left_on='case', right_on='caseid', sort=False).set_index(
        'index')
    assert len(merged_df.index) == len(set(merged_df.index))
    areas_of_law = get_areas_of_law_column_names()
    merged_df['area_count'] = merged_df[areas_of_law].sum(axis=1)
    merged_df['area'] = merged_df[areas_of_law].idxmax(axis=1)
    if reduce_circuit is not None:
        merged_df = merged_df[(merged_df.Circuit == reduce_circuit) & (merged_df.year >= 1925)].copy()
        merged_df = merged_df[merged_df['area_count'] == 1].copy()
        merged_df = merged_df[
            ~merged_df['area'].isin(['First_Amendment', 'Privacy', 'Due_Process', 'Miscellanous'])].copy()
    return merged_df


def get_judge_vectors(config: AnalysisConfig, majority_authorship_only=True, norm_vec_before_aggregation=True):
    model = Doc2Vec.load(config.model_path)
    gt = get_opinion_level_ground_truth(config)

    dis_map = dict.fromkeys([el for el in gt.opinion_type.unique() if 'Dis' in el], 'contentDisOp')
    con_map = dict.fromkeys([el for el in gt.opinion_type.unique() if 'Dis' not in el and 'Con' in el], 'contentConOp')

    rename_map = {**dis_map, **con_map, 'contentMajOp': 'contentMajOp'}

    gt['opinion_type'] = gt.opinion_type.map(rename_map)
    vector_index_map = gt.reset_index().set_index(['caseid', 'opinion_type'])['index']

    judge_df = pd.read_csv(config.bloomberg_votelevel_path)
    df = judge_df[judge_df.caseid.isin(gt.caseid)]
    maj = df[df.Author != 'PER CURIAM'].dropna(subset=['Author']).copy()

    maj['conc'] = maj[['songer_judge1', 'songer_judge2', 'songer_judge3']].eq(maj['songer_Author'], axis=0).idxmax(
        axis=1)
    maj['judgeid'] = maj.apply(lambda x: x[x.conc.replace('_', 'ID_')], axis=1)
    maj = maj.set_index('caseid')['judgeid'].to_frame('judgeid')
    maj['opinion_type'] = 'contentMajOp'
    maj = maj.set_index('opinion_type', append=True)

    dis_df = df[~df.JudgeDISSENTING.isna()].dropna(subset=['Dissenting'])
    dis_df['judgeid'] = dis_df.apply(
        lambda x: x[f'songerID_judge{int(x.Dissenting)}'], axis=1
    )
    dis_df['opinion_type'] = 'contentDisOp'
    dis_df = dis_df.set_index(['caseid', 'opinion_type'])[['judgeid']]

    con_df = df[~df.JudgeCONCURRING.isna()].copy()
    con_df['conc'] = con_df[['songer_judge1', 'songer_judge2', 'songer_judge3']].eq(con_df['songer_JudgeCONCURRING'],
                                                                                    axis=0).idxmax(axis=1)
    con_df['judgeid'] = con_df.apply(lambda x: x[x.conc.replace('_', 'ID_')], axis=1)
    con_df['opinion_type'] = 'contentConOp'
    con_df = con_df.set_index(['caseid', 'opinion_type'])[['judgeid']].dropna()

    if majority_authorship_only:
        j = maj
    else:
        j = pd.concat([maj, dis_df, con_df])

    merged = vector_index_map.to_frame('vector_index').merge(j, left_index=True, right_index=True)
    merged = merged.dropna()

    normed_vectors = model.dv.get_normed_vectors()

    def create_judge_vector(x):
        vecs = normed_vectors[x] if norm_vec_before_aggregation else model.dv[x]
        return vecs.mean(axis=0)

    judge_vecs = merged.groupby('judgeid')['vector_index'].apply(create_judge_vector)
    judge_vecs = judge_vecs.sort_index()

    return judge_vecs


if __name__ == '__main__':
    grouped = main()