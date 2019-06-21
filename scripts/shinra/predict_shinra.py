#!/usr/bin/env python3
# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
# Copyright 2019, Nihon Unisys, Ltd.
# 
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
"""A script to make and save model predictions on an input dataset."""

import os
import time
import torch
import argparse
import logging
import json

from tqdm import tqdm
from drqa.reader import Predictor

from collections import defaultdict
from collections import OrderedDict

import attr_list
import util

logger = logging.getLogger()
logger.setLevel(logging.INFO)
fmt = logging.Formatter('%(asctime)s: [ %(message)s ]', '%m/%d/%Y %I:%M:%S %p')
console = logging.StreamHandler()
console.setFormatter(fmt)
logger.addHandler(console)

parser = argparse.ArgumentParser()
parser.register('type', 'bool', util.str2bool)
parser.add_argument('dataset', type=str, default=None,
                    help='Shinra ENE dataset to evaluate on')
parser.add_argument('--dbpath', type=str, default=None,
                    help='Path to DB to use')
parser.add_argument('--infobox-db', type=str, default=None,
                    help='Path to DB to use')
parser.add_argument('--model', type=str, default=None,
                    help='Path to model to use')
parser.add_argument('--embedding-file', type=str, default=None,
                    help=('Expand dictionary to use all pretrained '
                          'embeddings in this file.'))
parser.add_argument('--out-dir', type=str, default='/tmp',
                    help=('Directory to write prediction file to '
                          '(<dataset>-<model>.preds)'))
parser.add_argument('--tokenizer', type=str, default=None,
                    help=("String option specifying tokenizer type to use "
                          "(e.g. 'corenlp')"))
parser.add_argument('--num-workers', type=int, default=None,
                    help='Number of CPU processes (for tokenizing, etc)')
parser.add_argument('--no-cuda', action='store_true',
                    help='Use CPU only')
parser.add_argument('--gpu', type=int, default=-1,
                    help='Specify GPU device id to use')
parser.add_argument('--batch-size', type=int, default=128,
                    help='Example batching size')
parser.add_argument('--top-n', type=int, default=1,
                    help='Store top N predicted spans per example')
parser.add_argument('--official', action='store_true',
                    help='Only store single top span instead of top N list')
parser.add_argument('--addtitle', type='bool', default=True,
                      help='add title to question string')
parser.add_argument('--multiple-answer', type='bool', default=False,
                      help='Use multiple answer model')
args = parser.parse_args()
t0 = time.time()

args.cuda = not args.no_cuda and torch.cuda.is_available()
if args.cuda:
    torch.cuda.set_device(args.gpu)
    logger.info('CUDA enabled (GPU %d)' % args.gpu)
else:
    logger.info('Running on CPU only.')

predictor = Predictor(
    model=args.model,
    tokenizer=args.tokenizer,
    embedding_file=args.embedding_file,
    num_workers=args.num_workers,
)
if args.cuda:
    predictor.cuda()


# ------------------------------------------------------------------------------
# Read in dataset and make predictions.
# ------------------------------------------------------------------------------

wiki_content_db = None
if args.dbpath:
    wiki_content_db = util.init_wiki(args.dbpath)
wiki_infobox_db = None
if args.infobox_db:
    wiki_infobox_db = util.init_wiki(args.infobox_db)

examples = []
questions = []
answer_attr = OrderedDict()
wiki_ids = []

with open(args.dataset) as f:
    data = json.load(f)['data']
    for article in data:
        ENE = article['ENE']
        wiki_id = article['WikipediaID']
        title = article['title']
        attrs = attr_list.attrs[ENE]
        answer_attr[wiki_id] = {'ENE':ENE, 'title':title,'WikipediaID':wiki_id,'Attributes':defaultdict(list)}
        for paragraph in article['paragraphs']:
            context = paragraph['context']
            #if len(context) > 50000:
            #    context = context[:50000]
            for attr in attrs:
                questions.append(attr)
                wiki_ids.append(wiki_id)
                if args.addtitle:
                    q = title+'の'+attr+'は？'
                else:
                    q = attr
                examples.append((context, q))

for i in tqdm(range(0, len(examples), args.batch_size)):
    predictions = predictor.predict_batch(
        examples[i:i + args.batch_size], top_n=args.top_n)
    for j in range(len(predictions)):
        #answer_attr[wiki_ids[i+j]]['Attributes'][examples[i+j][1]].append(predictions[j][0][0])
        answer_attr[wiki_ids[i+j]]['Attributes'][questions[i+j]] = [(p[0], float(p[1])) for p in predictions[j]]

model = os.path.splitext(os.path.basename(args.model or 'default'))[0]
basename = os.path.splitext(os.path.basename(args.dataset))[0]
outfile = os.path.join(args.out_dir, basename + '-' + model + '.preds.json')
logger.info('Writing results to %s' % outfile)
with open(outfile, 'w') as out_f:
    out_f.write('{"entry":[' + '\n')
    out_f.write(',\n'.join([json.dumps(v, ensure_ascii=False) for v in answer_attr.values()]) + '\n')
    out_f.write(']}' + '\n')

logger.info('Total time: %.2f' % (time.time() - t0))
