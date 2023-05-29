import anna_utils
import api
import json

def set_up():
    anna_utils.get_plain_text()
    anna_utils.train_model()

def get_judge_matrices():
    jvecs = anna_utils.get_judge_vectors(config, majority_authorship_only=False, norm_vec_before_aggregation=False)

    sim_matrix = api.get_judge_similarity_matrix(jvecs)

    # We show a plot
    plt = api.plot_judge_similarity_matrix(sim_matrix)
    plt.show()

    jvecs_names = api.associate_judge_vectors_with_fjc_names(config, jvecs)

    print(jvecs_names.shape)
    print(jvecs_names.head(10))
    
# def get_area_blobs():
    # modified from api - see how the word2vec computes areas of law

# print(anna_utils.get_var('../../fast/cl_scotus/opinions/opinions_120436.json','download_url','local_path'))
# print(anna_utils.get_var('../../fast/cl_scotus/opinions/opinions_120436.json','html','html_lawbox'))

f_list = anna_utils.count_files('../../fast/cl_scotus/opinions/*.json','author','joined_by',False,True)
with open('file_list_author.txt','w') as fl:
    json.dump(f_list, fl)

# anna_utils.count_files('../../fast/cl_scotus/opinions/*.json','author_str','per_curiam',False)
# anna_utils.count_files('../../fast/cl_scotus/opinions/*.json','scdb_id','per_curiam',False)

# fl = anna_utils.has_aol('../../fast/cl_scotus/opinions/*.json',False)
# print(fl)
# with open('file_list.txt','w') as file_write:
#     json.dump(fl, file_write)
# with open('file_list2.txt','w') as file_write2:
#     file_write2.write(str(fl))


# json_files = glob.glob(path_to_dir)
# tot_files = len(json_files)

# num_files = 100
# file_list = []
# counter = 0
# for i in range(num_files):
#     pt = get_var(json_files[i],'plain_text,next_var)
#     pt1 = get_var(
#     if (pt != '""' and pt != None and pt != 'null'):
#         counter += 1
#         if not old:
#             name = json_files[i][30:-5]
#         else:
#             name = json_files[i][29:-5]
#         file_list.append(name[9:])
#         if (not all_files):
#             print(pt)
#             print(name)
# print("total files: " + str(tot_files))
# print("total files parsed: " + str(num_files))
# print("with variable: " + str(counter))
# print("percent: " + str(counter/num_files*100)+"%")
