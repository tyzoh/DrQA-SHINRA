#!/usr/bin/env python3
# Copyright 2019, Nihon Unisys, Ltd.
#
# This source code is licensed under the BSD license. 

import argparse
import json
import collections
from collections import defaultdict
import attr_list

all_attributes = collections.OrderedDict()

def process(dataset_2019):
    ENE = dataset_2019['ENE']
    title = dataset_2019['title']
    page_id = dataset_2019['page_id']
    if not page_id in all_attributes:
        all_attributes[page_id] = collections.OrderedDict()
        all_attributes[page_id]['ENE'] = ENE
        all_attributes[page_id]['title'] = title
        all_attributes[page_id]['page_id'] = page_id
        all_attributes[page_id]['Attributes_html'] = {att:[] for att in attr_list.attrs[ENE]}
        all_attributes[page_id]['Attributes_text'] = {att:[] for att in attr_list.attrs[ENE]}
    
    attribute = dataset_2019['attribute']
    html_offset = dataset_2019['html_offset']
    text_offset = dataset_2019['text_offset']
    all_attributes[page_id]['Attributes_html'][attribute].append(html_offset)
    all_attributes[page_id]['Attributes_text'][attribute].append(text_offset)
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str)
    parser.add_argument('output', type=str)
    parser.add_argument('--split_test', type=float, default=0.90,
                        help='start point of test data')

    args = parser.parse_args()

    with open(args.input) as f:
        for line in f:
            dataset_2019 = json.loads(line)
            process(dataset_2019)
    
    with open(args.output, 'w') as f:
        f.write('{"entry":[\n')
        json_str = []
        for attr in all_attributes.values():
            json_str.append(json.dumps(attr, ensure_ascii=False))
        f.write(',\n'.join(json_str))
        f.write('\n]}\n')
    
    import util
    split_dataset = util.make_split_data(list(all_attributes.values()), split_nums=[args.split_test])
    with open(args.output.replace('.json', '-test.json'), 'w') as f:
        f.write('{"entry":[\n')
        json_str = []
        for attr in split_dataset[1]:
            json_str.append(json.dumps(attr, ensure_ascii=False))
        f.write(',\n'.join(json_str))
        f.write('\n]}\n')
    
main()
