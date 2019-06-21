#!/usr/bin/env python3
# Copyright 2019, Nihon Unisys, Ltd.
#
# This source code is licensed under the BSD license. 

import time
import argparse
import logging
import json

import evaluation
import attr_list
import os, os.path
import numpy as np

logger = logging.getLogger()
logger.setLevel(logging.INFO)
fmt = logging.Formatter('%(asctime)s: [ %(message)s ]', '%m/%d/%Y %I:%M:%S %p')
console = logging.StreamHandler()
console.setFormatter(fmt)
logger.addHandler(console)

parser = argparse.ArgumentParser()
parser.add_argument('--predicate-json', type=str, default=None, 
                    help='Shinra predicted dataset')
parser.add_argument('--answer-json', type=str, default=None, 
                    help='Shinra answer dataset')
parser.add_argument('--splited', action='store_true',
                    help='use split json')
parser.add_argument('--min-score', type=float, default=0.1, 
                    help='threshold min score')
parser.add_argument('--ignore_offset', action='store_true',
                    help='ignore gold offset')
parser.add_argument('--debug', action='store_true',
                    help='print debug info')
                 
args = parser.parse_args()
t0 = time.time()

def regulation(shinra_dataset):
    pred_reg = {}
    pred_reg['entry'] = []
    
    for pred_qa in shinra_dataset['entry']:
        pred_reg['entry'].append(pred_qa)
        title =  pred_qa['title']
        ENE =  pred_qa['ENE']
        
        reg_att = dict()
        for k in pred_qa['Attributes'].keys():
            attr_k_qa = pred_qa['Attributes'][k]
            reg_att[k] = []
            anss_qa = [d[0]['text'] for d in attr_k_qa]
            scores_qa = [d[1] for d in attr_k_qa]
            answered = set()
            for i, qa_ans in enumerate(anss_qa):
                if len(qa_ans) == 0: continue
                score = scores_qa[i]

                if qa_ans.strip() in ['φ', '?', '？', '不明'] or qa_ans[0] == 'φ':
                    if score > 0.8: break
                    else: continue

                if len(reg_att[k]) > 0 and k in attr_list.top1keys[ENE]:
                    if score > 0.8:
                        reg_att[k].append(attr_k_qa[i])
                elif score > args.min_score:
                    reg_att[k].append(attr_k_qa[i])

        pred_reg['entry'][-1]['Attributes'] = reg_att
        
    return pred_reg

def evaluate(preds, logger=None):
    from evaluation import WikiepediaEvaluation
    # 学習データの読み込み
    with open(args.answer_json) as f:
        data = json.load(f)
    we = WikiepediaEvaluation(data, ignore_offset=args.ignore_offset, debug=args.debug)
    result = we.evaluate(preds)
    print(result[["attribute", "precision", "recall", "f1-score", "support"]])
    
    sum_support = np.sum(result['support'])
    sum_tp = np.sum(result['true_positive'])
    sum_fp = np.sum(result['false_positive'])
    sum_fn = np.sum(result['false_negative'])
    prec = sum_tp/(sum_tp+sum_fp)
    recall = sum_tp/(sum_tp+sum_fn)
    micro_f1 = 2*prec*recall/(prec+recall)
    print('\nmicro-precision:', f'{prec:.3f}', 'micro-recall:', f'{recall:.3f}', 'micro-f1:', f'{micro_f1:.3f}')
    
    print('macro-precision:', f'{result["precision"].mean():.3f}', 'macro-recall:', f'{result["recall"].mean():.3f}', 'macro-f1:', f'{result["f1-score"].mean():.3f}')

    
with open(args.predicate_json) as f:
    if args.splited:
        shinra_dataset = json.loads('{"entry": ['+''.join(f.readlines()).replace('\n', '')+']}')
    else:
        shinra_dataset = json.load(f)

pred_dataset = regulation(shinra_dataset)
if args.answer_json != None:
    evaluate(pred_dataset, logger)

basename = os.path.basename(args.predicate_json).replace('.json', '')+'_eval'
outfile = os.path.join(os.path.dirname(args.predicate_json), basename)

logger.info('Writing results to %s' % outfile)
out_lines = []
for p in pred_dataset['entry']:
    out_lines.append(json.dumps(p, ensure_ascii=False))

with open(outfile+'.json', 'w') as f:
    if not args.splited: f.write('{"entry": ['+'\n')
    f.write(',\n'.join(out_lines)+'\n')
    if not args.splited: f.write(']}'+'\n')

logger.info('Total time: %.2f' % (time.time() - t0))
