#!/usr/bin/env python3
# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
# Copyright 2019, Nihon Unisys, Ltd.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
"""Preprocess the SQuAD dataset for training."""

import argparse
import os
import sys
import json
import time

from multiprocessing import Pool
from multiprocessing.util import Finalize
from functools import partial
from drqa import tokenizers

# ------------------------------------------------------------------------------
# Tokenize + annotate.
# ------------------------------------------------------------------------------

TOK = None


def init(tokenizer_class, options):
    global TOK
    TOK = tokenizer_class(**options)
    Finalize(TOK, TOK.shutdown, exitpriority=100)


def tokenize(text):
    """Call the global process tokenizer on the input text."""
    global TOK
    tokens = TOK.tokenize(text)
    output = {
        'words': tokens.words(),
        'offsets': tokens.offsets(),
        'pos': tokens.pos(),
        'lemma': tokens.lemmas(),
        'ner': tokens.entities(),
        'line_offsets': tokens.line_offsets(),
    }
    return output


# ------------------------------------------------------------------------------
# Process dataset examples
# ------------------------------------------------------------------------------


def load_dataset(path):
    """Load json file and store fields separately."""
    with open(path) as f:
        data = json.load(f)['data']
    output = {'qids': [], 'questions': [], 'answers': [],
              'contexts': [], 'qid2cid': [], 'page_id': []}
    for article in data:
        for paragraph in article['paragraphs']:
            output['contexts'].append(paragraph['context'])
            output['page_id'].append(article['WikipediaID'])
            for qa in paragraph['qas']:
                output['qids'].append(qa['id'])
                output['questions'].append(qa['question'])
                output['qid2cid'].append(len(output['contexts']) - 1)
                if 'answers' in qa:
                    output['answers'].append(qa['answers'])
    return output

def find_answer(offset_line_id, answer_start, answer_end):
    """Match token offsets with the char begin/end offsets of the answer."""
    start = [i for i, tok in enumerate(offset_line_id) if tok == (answer_start['line_id'], answer_start['offset'])]
    end = [i for i, tok in enumerate(offset_line_id) if tok[0] == answer_end['line_id'] and tok[1] >= answer_start['offset'] and tok[1] < answer_end['offset']]
    
    try:
        assert(len(start) == 1)
        assert(len(end) >= 1)
    except:
        print('find_answer AssertionError start:', answer_start, start)
        print('find_answer AssertionError end:', answer_end, end)
    if len(start) == 1 and len(end) >= 1:
        return start[0], end[-1]

def set_answer_to_offsets(offsets, answers):
	answer_offsets = [0] * len(offsets)
	for ans in answers:
		answer_offsets[ans[0]:ans[1]+1] = [1] * (ans[1]-ans[0]+1)
	return answer_offsets
  
def process_dataset(data, tokenizer, workers=None):
    """Iterate processing (tokenize, parse, etc) dataset multithreaded."""
    tokenizer_class = tokenizers.get_class(tokenizer)
    make_pool = partial(Pool, workers, initializer=init)
    workers = make_pool(initargs=(tokenizer_class, {'annotators': {'lemma'}}))
    q_tokens = workers.map(tokenize, data['questions'])
    workers.close()
    workers.join()

    workers = make_pool(
        initargs=(tokenizer_class, {'annotators': {'lemma', 'pos', 'ner'}})
    )
    c_tokens = workers.map(tokenize, data['contexts'])
    
    #offsets_lineid = dict()
    #for i, cnt in enumerate(data['contexts']):
    #    offsets_lineid[data['page_id'][i]] = line_id_to_offset(cnt, c_tokens[i]['offsets'])
    
    workers.close()
    workers.join()

    for idx in range(len(data['qids'])):
        question = q_tokens[idx]['words']
        qlemma = q_tokens[idx]['lemma']
        document = c_tokens[data['qid2cid'][idx]]['words']
        offsets = c_tokens[data['qid2cid'][idx]]['offsets']
        line_offsets = c_tokens[data['qid2cid'][idx]]['line_offsets']
        lemma = c_tokens[data['qid2cid'][idx]]['lemma']
        pos = c_tokens[data['qid2cid'][idx]]['pos']
        ner = c_tokens[data['qid2cid'][idx]]['ner']
        ans_tokens = []
        if len(data['answers']) > 0:
            for ans in data['answers'][idx]:
                found = find_answer(line_offsets,
                                    ans['answer_start'],
                                    ans['answer_end'])
                if found:
                    ans_tokens.append(found)
        if args.multiple_answer:
            answer_offsets = set_answer_to_offsets(offsets,ans_tokens)
            yield {
                'id': data['qids'][idx],
                'question': question,
                'document': document,
                'offsets': offsets,
                'answers': ans_tokens,
                'answer_offsets': answer_offsets,
                'qlemma': qlemma,
                'lemma': lemma,
                'pos': pos,
                'ner': ner,
            }
        else:
            yield {
                'id': data['qids'][idx],
                'question': question,
                'document': document,
                'offsets': offsets,
                'answers': ans_tokens,
                'qlemma': qlemma,
                'lemma': lemma,
                'pos': pos,
                'ner': ner,
            }


# -----------------------------------------------------------------------------
# Commandline options
# -----------------------------------------------------------------------------


parser = argparse.ArgumentParser()
parser.add_argument('data_dir', type=str, help='Path to SQuAD data directory')
parser.add_argument('out_dir', type=str, help='Path to output file dir')
parser.add_argument('--split', type=str, help='Filename for train/dev split',
                    default='SQuAD-v1.1-train')
parser.add_argument('--workers', type=int, default=None)
parser.add_argument('--tokenizer', type=str, default='corenlp')
parser.add_argument('--multiple-answer', action='store_true', help='Use multiple answer model')
args = parser.parse_args()

t0 = time.time()

in_file = os.path.join(args.data_dir, args.split + '.json')
print('Loading dataset %s' % in_file, file=sys.stderr)
dataset = load_dataset(in_file)

out_file = os.path.join(
    args.out_dir, '%s-processed-%s.txt' % (args.split, args.tokenizer)
)
print('Will write to file %s' % out_file, file=sys.stderr)
with open(out_file, 'w') as f:
    for ex in process_dataset(dataset, args.tokenizer, args.workers):
        f.write(json.dumps(ex, ensure_ascii=False) + '\n')
print('Total time: %.4f (s)' % (time.time() - t0))
