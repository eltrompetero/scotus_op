import os

if os.path.expanduser('~').split('/')[-1]=='anna':
    DATADR = '/fastcache/anna/scotus_big'
else:
    DATADR = '../data/cl_scotus'
