#!/usr/bin/env python3
# Copyright 2019, Nihon Unisys, Ltd.
#
# This source code is licensed under the BSD license.

import argparse
import json
import util
import re
from pathlib import Path

start_pattern = re.compile(r'^\s+<h1\s.+</h1>\s*')
end_pattern = re.compile(r'^.*<div class="printfooter">.*')
htmltag_pattern = re.compile(r'<sup .*?</sup>|<!--.*?-->|<[^>]+?>')
except_nextline_pattern = re.compile(r'^[^\n]*')

def replace_html_tag(html_data):
    is_content = False
    is_comment = False
    in_table_tag = False
    content = []
    for line in html_data.split('\n'):
        if not is_content and start_pattern.match(line):
            is_content = True
        if is_content and end_pattern.match(line):
            break
        if is_content and not is_comment and line.startswith('<!--') and not '-->' in line:
            is_comment = True

        if not is_content or is_comment:
            iterator = except_nextline_pattern.finditer(line)
            line = list(line)
            for match in iterator:
                line[match.start():match.end()] = [' ']*(match.end()-match.start())
            content.append(''.join(line)+'\n')
        else:
            iterator = htmltag_pattern.finditer(line)
            line = list(line)
            for match in iterator:
                if match.group().startswith('</th'):
                    in_table_tag = True
                if in_table_tag and match.group().startswith('<td '):
                    line[match.start():match.end()] = ['は', '、'] + [' ']*(match.end()-match.start()-2)
                    continue
                if in_table_tag and match.group().startswith('</td'):
                    line[match.start():match.end()] = ['。']+[' ']*(match.end()-match.start()-1)
                    in_table_tag = False
                    continue

                line[match.start():match.end()] = [' ']*(match.end()-match.start())

            content.append(''.join(line)+'\n')

        if is_comment and '-->' in line:
            is_comment = False

    return ''.join(content)

def process(dataset, filedir, multiple_answer=False, addtitle=True):

    data_size = len(dataset['entry'])
    squad_data = []

    for i, entry in enumerate(dataset['entry']):

        ENE = entry['ENE']
        title = entry['title']
        page_id = entry['page_id']
        attributes = entry['Attributes_html']

        print('-'*5, str(i) + '/' + str(data_size), str(page_id), title, '-'*5)

        with filedir.joinpath(str(page_id)+'.html').open() as f:
            html_content = f.read()

        content = replace_html_tag(html_content)

        if not multiple_answer:
            content = 'φ'+content[1:]

        q_idx = 0
        qas = []

        for k,v in attributes.items():
            if addtitle:
                q = title + 'の' + k + 'は？'
            else:
                q = k
            q_idx += 1
            q_id = str(page_id) + '_' + str(q_idx)
            answers = []
            found_answers = set()
            for ans in v:
                answers.append({"answer_start": ans['start'], "answer_end": ans['end'], "text": ans['text']})

            if not multiple_answer and len(answers) == 0:
                answers.append({"answer_start": 0, "text": 'φ'})
            qas.append({"answers": answers, "question": q, "id": q_id})

        squad_json = {"title": title, 'WikipediaID': page_id, "ENE":ENE, "paragraphs": [{"context": content, "qas": qas}]}
        squad_data.append(squad_json)
    return squad_data

def main():
    parser = argparse.ArgumentParser()
    parser.register('type', 'bool', util.str2bool)
    parser.add_argument('input', type=str)
    parser.add_argument('output', type=str)
    parser.add_argument('--category', type=str, default='',
                        help='category name')
    parser.add_argument('--html_dir', type=str, default='./data/JP-5/HTML/',
                        help='HTML data directory path')
    parser.add_argument('--multiple-answer', action='store_true',
                        help='convert for multiple answers model')
    parser.add_argument('--addtitle', type='bool', default=True,
                        help='add title to question string')
    parser.add_argument('--split_dev', type=float, default=0.85,
                        help='start point of dev data')
    parser.add_argument('--split_test', type=float, default=0.90,
                        help='start point of test data')

    args = parser.parse_args()

    if not args.category:
        p = Path(inputfile)
        args.category = p.stem.replace('_dist_2018','')

    squad_data_all = []
    squad_json_train = []
    squad_json_dev = []
    squad_json_test = []
    for inputfile in args.input.split(','):
        with open(inputfile) as f:
            shinra_dataset = json.load(f)
            filedir=Path(args.html_dir).joinpath(args.category)
            squad_data = process(shinra_dataset, filedir, multiple_answer=args.multiple_answer, addtitle=args.addtitle)

            squad_data_all.extend(squad_data)
            split_dataset = util.make_split_data(squad_data, split_nums=[args.split_dev, args.split_test])
            squad_json_train.extend(split_dataset[0])
            squad_json_dev.extend(split_dataset[1])
            squad_json_test.extend(split_dataset[2])

    with open(args.output, 'w') as f:
        f.write(json.dumps({"data": squad_data_all}, sort_keys=True, ensure_ascii=False)) #for formal run

    with open(args.output.replace('.json', '-train.json'), 'w') as f:
        f.write(json.dumps({"data": squad_json_train}, sort_keys=True, ensure_ascii=False))

    with open(args.output.replace('.json', '-dev.json'), 'w') as f:
        f.write(json.dumps({"data": squad_json_dev}, sort_keys=True, ensure_ascii=False))

    with open(args.output.replace('.json', '-test.json'), 'w') as f:
        f.write(json.dumps({"data": squad_json_test}, sort_keys=True, ensure_ascii=False))

main()
