# define the paths where things are located (use the big file bc thats more data)
cleaned_folder = './scotus_big/cleaned_text/'
json_folder = './scotus_big/scotus/'
scdb_path = '/home/anna/fast/SCDB_2021_01_caseCentered_Citation.csv'
justice_path = '/home/anna/fast/SCDB_2021_01_justiceCentered_Citation.csv'
cluster_path = '/home/anna/fast/scotus_big/clusters/cluster_'
# pickle_df_path = '/home/anna/fast/scotus_big/df' - old path, new one has vecs and scdb attrs up to date
pickle_df_path = './scotus_big/df_final'
pickle_df_path_new = '/home/anna/fast/scotus_big/df_with_normed'
pickle_df_path_with_vecs = '/home/anna/fast/scotus_big/df_vecs' # this is right after the vectors were generated
id_df_path = './scotus_big/df_matched_ids'
# cleaned_and_sentencized_path = '/home/anna/fast/scotus_big/sentence_text/'
# cleaned_and_sentencized_path = '/home/anna/fast/scotus_big/cleaned_text/'
# cleaned_and_sentencized_path = '/home/anna/fast/scotus_big/cleaned_text_1/'
cleaned_and_sentencized_path = './scotus_big/cleaned_text_no_sentence/'
judge_avg_vecs = '/home/anna/fast/scotus_big/judge_avg'
bow_path = '/home/anna/fast/scotus_big/bow'

'''
Attributes we want:
- id
- cluster
- author
(the rest are from cluster)
- citations
- date_filed
- date_filed_is_approximate
- case_name_short
- case_name
- case_name_full
- scdb_id
FROM SCDB
- majOpinWriter
- lawArea
'''  
db_attrs_from_op = ['id','cluster','author']
db_attrs_from_cluster = ['citations','date_filed','date_filed_is_approximate','case_name_short','case_name','case_name_full','scdb_id']
db_attrs_from_scdb = ['majOpinWriter','issueArea']
all_attrs = db_attrs_from_op + db_attrs_from_cluster + db_attrs_from_scdb

# correspondance of citation format names btw cl and scdb
cite_corr = {'U.S.':'usCite','S. Ct.':'sctCite', 'L. Ed. 2d':'ledCite','L. Ed.':'ledCite', 'U.S. LEXIS':'lexisCite'}

'''
Outline of the structures to parse
Assets
- folder of parsed text files
- folder of op search results with attributes (names correspond to text files)
- curl on online clusters?
- scdb with author and case info (also has different types of citations)
- scala db with citations
To do
- loop through the court listener scotus json files
- make an array of their useful attributes (not plain text)
- go up to their opinion cluster and try to get the case id info (5 types)
- 
'''

my_token = 'f9440d22b80b57000ebcd9732fe8d7a246fec813'


issue_areas = ['Criminal Procedure','Civil Rights','First Amendment','Due Process','Privacy','Attorneys','Unions','Economic Activity','Judicial Power','Federalism','Interstate Relations','Federal Taxation','Miscellaneous','Private Action']

judge_names = {'86': 'HHBurton', '84': 'RHJackson', '81': 'WODouglas', '80': 'FFrankfurter', '79': 'SFReed', '78': 'HLBlack', '85': 'WBRutledge', '82': 'FMurphy', '87': 'FMVinson', '88': 'TCClark', '89': 'SMinton', '90': 'EWarren', '91': 'JHarlan2', '92': 'WJBrennan', '93': 'CEWhittaker', '94': 'PStewart', '95': 'BRWhite', '96': 'AJGoldberg', '97': 'AFortas', '98': 'TMarshall', '99': 'WEBurger', '100': 'HABlackmun', '101': 'LFPowell', '102': 'WHRehnquist', '103': 'JPStevens', '104': 'SDOConnor', '105': 'AScalia', '106': 'AMKennedy', '107': 'DHSouter', '108': 'CThomas', '109': 'RBGinsburg', '110': 'SGBreyer', '111': 'JGRoberts', '112': 'SAAlito', '113': 'SSotomayor', '114': 'EKagan', '115': 'NMGorsuch', '116': 'BMKavanaugh', '117': 'ACBarrett'}

judge_apt_party = {'HLBlack': 0,'SFReed': 0,'FFrankfurter': 0,'WODouglas': 0,'FMurphy': 0,'RHJackson': 0,'WBRutledge': 0,'HHBurton': 0,'FMVinson': 0,'TCClark': 0,'SMinton': 0,'EWarren': 1, 'JHarlan2': 1,'WJBrennan': 1,'CEWhittaker': 1,'PStewart': 1,'BRWhite': 0,'AJGoldberg': 0,'AFortas': 0,'TMarshall': 0,'WEBurger': 1,'HABlackmun': 1,'LFPowell': 1,'WHRehnquist': 1,'JPStevens': 1,'SDOConnor': 1,'AScalia': 1,'AMKennedy': 1,'DHSouter': 1,'CThomas': 1,'RBGinsburg': 0,'SGBreyer': 0,'JGRoberts': 1,'SAAlito': 1,'SSotomayor': 0,'EKagan': 0,'NMGorsuch': 1,'BMKavanaugh': 1,'ACBarrett': 1}

judge_years = {'HLBlack': (1937 , 1971),'SFReed': ( 1938, 1957),'FFrankfurter': (1939 , 1962),'WODouglas': (1939 , 1975),'FMurphy': (1940 , 1949),'RHJackson': (1941 , 1954),'WBRutledge': ( 1943, 1949),'HHBurton': ( 1945, 1958),'FMVinson': (1946 ,1953 ),'TCClark': ( 1949, 1967),'SMinton': ( 1949, 1956),'EWarren': ( 1953, 1969),'JHarlan2': (1955 , 1971),'WJBrennan': (1956 ,1990 ),'CEWhittaker': ( 1957, 1962),'PStewart': (1958 ,1981 ),'BRWhite': (1962 , 1993),'AJGoldberg': (1962 ,1965 ),'AFortas': ( 1965, 1969),'TMarshall': (1967 , 1991),'WEBurger': ( 1969, 1986),'HABlackmun': ( 1970, 1994),'LFPowell': ( 1972, 1987),'WHRehnquist': (1972 , 2005),'JPStevens': ( 1975,2010 ),'SDOConnor': (1981 , 2006),'AScalia': ( 1986,2016 ),'AMKennedy': ( 1988,2018 ),'DHSouter': (1990 , 2009),'CThomas': (1991 , 2022),'RBGinsburg': ( 1993,2020 ),'SGBreyer': (1994 , 2022),'JGRoberts': ( 2005, 2022),'SAAlito': ( 2006, 2022),'SSotomayor': (2009 ,2022 ),'EKagan': (2010 ,2022 ),'NMGorsuch': ( 2017, 2022),'BMKavanaugh': (2018 ,2022 ),'ACBarrett': ( 2020, 2022)}



# what i used to get the opinion cluster data (now in the cluster folder). missing the part where it just goes through years
urls=['https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2002&docket__court__id=scotus&date_filed__lt=2002-04-01','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2002&docket__court__id=scotus&date_filed__gte=2002-04-01&date_filed__lt=2002-06-01','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2002&docket__court__id=scotus&date_filed__gte=2002-06-01&date_filed__lt=2002-10-01','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2002&docket__court__id=scotus&date_filed__gte=2002-10-01&date_filed__lt=2002-10-10','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2002&docket__court__id=scotus&date_filed__gte=2002-10-10','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2003&docket__court__id=scotus&date_filed__lt=2003-02-01','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2003&docket__court__id=scotus&date_filed__gte=2003-02-01&date_filed__lt=2003-04-01','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2003&docket__court__id=scotus&date_filed__gte=2003-04-01&date_filed__lt=2003-06-01','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2003&docket__court__id=scotus&date_filed__gte=2003-06-01&date_filed__lt=2003-10-01','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2003&docket__court__id=scotus&date_filed__gte=2003-10-01&date_filed__lt=2003-10-10','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2003&docket__court__id=scotus&date_filed__gte=2003-10-10','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2004&docket__court__id=scotus&date_filed__lt=2004-02-01','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2004&docket__court__id=scotus&date_filed__gte=2004-02-01&date_filed__lt=2004-04-01','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2004&docket__court__id=scotus&date_filed__gte=2004-04-01&date_filed__lt=2004-06-01','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2004&docket__court__id=scotus&date_filed__gte=2004-06-01&date_filed__lt=2004-10-01','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2004&docket__court__id=scotus&date_filed__gte=2004-10-01&date_filed__lt=2004-10-10','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2004&docket__court__id=scotus&date_filed__gte=2004-10-10','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2005&docket__court__id=scotus&date_filed__lt=2005-02-01','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2005&docket__court__id=scotus&date_filed__gte=2005-02-01&date_filed__lt=2005-04-01','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2005&docket__court__id=scotus&date_filed__gte=2005-04-01&date_filed__lt=2005-06-01','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2005&docket__court__id=scotus&date_filed__gte=2005-06-01&date_filed__lt=2005-10-01','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2005&docket__court__id=scotus&date_filed__gte=2005-10-01&date_filed__lt=2005-10-10','https://www.courtlistener.com/api/rest/v3/clusters/?date_filed__year=2005&docket__court__id=scotus&date_filed__gte=2005-10-10']
