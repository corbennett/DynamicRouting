# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 17:16:03 2022

@author: svc_ccg
"""

import pandas as pd
import json, os
import get_sessions as gs
import numpy as np
import glob
from query_lims import query_lims, ECEPHYS_SESSION_QRY, PROJECT_QRY
from behavior_analysis import get_trials_df

get_mouse_id = lambda s: os.path.basename(s).split('_')[1]

session_paths =  gs.get_sessions(r"\\allen\programs\mindscope\workgroups\np-exp", mouseID='!366122', rig='NP1')
mice = [get_mouse_id(c) for c in session_paths]
full_id = [os.path.basename(c) for c in session_paths]

stim_name = []
project = []
pkl_format = []
for isess, s in enumerate(session_paths):
    print(isess)
    platform_file = glob.glob(os.path.join(s, '*platformD1.json'))[0]
    with open(platform_file, 'r') as f:
        platform_info = json.load(f)

    stim_name.append(platform_info.get('stimulus_name', ''))
    
    lims_id = full_id[isess].split('_')[0]
    project_id = query_lims(ECEPHYS_SESSION_QRY.format(lims_id))[0]['project_id']
    project_name = query_lims(PROJECT_QRY.format(project_id))[0]['code']
    project.append(project_name)
    
    
    pkl_file = glob.glob(os.path.join(s,'*behavior.pkl'))
    if len(pkl_file)==0:
        pkl_format.append('no pickle')
        continue
    
    pkl_data = pd.read_pickle(pkl_file[0])
    try:
        trials = get_trials_df(pkl_data)
        pkl_format.append('DoC')
    except:
        pkl_format.append('non-DoC')
    
    print(pkl_format)
        
df = pd.DataFrame(zip(mice, full_id, stim_name, project, pkl_format, session_paths), 
                  columns = ['mouse_id', 'exp_id', 'stim', 'project', 'pkl_format', 'local_path'])


anno = pd.read_excel(r"C:\Users\svc_ccg\ccb_onedrive\OneDrive - Allen Institute\Neuropixels Pipeline Behavior Annotations.xlsx", sheet_name=1) #experiment sessions
anno = anno.rename(columns={'Location ': 'Location'})

anno = anno.dropna(subset=['Mouse # '])
for ir, row in anno.iterrows():
    
    mouseID = str(int(row['Mouse # ']))
    date = row['Date ']
    if isinstance(date, float):
        date = str(int(date))
    else:
        date = date.strftime('%Y%m%d')
    location = row['Location']
    
    
    if not isinstance(location, str):
        try:
            datadir = gs.get_sessions(sources, mouseID=mouseID, start_date=date, end_date=date)
            anno.at[ir, 'Location'] = datadir[0]
        except:
            print('Could not find location for {} on {}'.format(mouseID, date))

df = pd.DataFrame(anno)
writer = pd.ExcelWriter(r"C:\Users\svc_ccg\ccb_onedrive\OneDrive - Allen Institute\VBN_video_annotations_Experiments.xlsx", engine='xlsxwriter')
df.to_excel(writer, sheet_name='Experiment', index=False)
writer.save()