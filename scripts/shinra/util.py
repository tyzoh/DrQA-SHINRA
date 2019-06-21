#!/usr/bin/env python3
# Copyright 2019, Nihon Unisys, Ltd.
#
# This source code is licensed under the BSD license. 

def init_wiki(db_path):
    from drqa import retriever

    db_class = retriever.get_class('sqlite')
    doc_db = db_class(**{'db_path': db_path})
    return doc_db

def make_split_data(data_set, split_nums=[0.99]):
    split_datasets = []
    start_idx = 0
    for split_num in split_nums:
        end_idx = int(split_num*len(data_set))
        split_datasets.append(data_set[start_idx:end_idx])
        start_idx = end_idx
    split_datasets.append(data_set[end_idx:])

    return split_datasets

def str2bool(v):
    return v.lower() in ('yes', 'true', 't', '1', 'y')
