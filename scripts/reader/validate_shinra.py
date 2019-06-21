#!/usr/bin/env python3
# Copyright 2018 Sansan, Inc. 
# Copyright 2019 Nihon Unisys, Ltd. 
#
# This source code is licensed under the MIT license.
"""Validation script for SHINRA dataset"""

import logging
from collections import Counter
from drqa.reader import utils

logger = logging.getLogger()

def validate(args, data_loader, model, global_stats, mode):
    """Run validation for SHINRA dataset."""
    eval_time = utils.Timer()
    attribute_count = Counter(true_positive=0, false_positive=0, false_negative=0, support=0)
    
    # Run through examples
    examples = 0
    for ex in data_loader:
        batch_size = ex[0].size(0)
        pred_s, pred_e, _ = model.predict(ex, top_n=20)
        
        if args.multiple_answer:
            target_s, target_e = ex[-4:-2]
        else:
            target_s, target_e = ex[-3:-1]

        for i in range(batch_size):
            tp, fp, fn, support = count_tp_fp_fn(zip(pred_s[i], pred_e[i]), zip(target_s[i], target_e[i]))
            attribute_count['true_positive'] += tp
            attribute_count['false_positive'] += fp
            attribute_count['false_negative'] += fn
            attribute_count['support'] += support
                
        examples += batch_size
    
    precision, recall, f_measure, support = evaluation(attribute_count)
    
    logger.info('dev valid shinra: Epoch = %d | precision = %.2f | recall = %.2f | ' %
                (global_stats['epoch'], precision * 100, recall * 100) +
                'F1 = %.2f | examples = %d | support = %d |valid time = %.2f (s)' %
                (f_measure * 100, examples, support, eval_time.time()))

    return {'precision': precision * 100, 'recall': recall * 100, 'f1': f_measure * 100, 'support': support}

def count_tp_fp_fn(pred, test):
    test = [(t_s, t_e) for t_s, t_e in test]
    pred = [(p_s, p_e) for p_s, p_e in pred]
    
    results = [(p in test) for p in pred]
    
    # 抽出できたうえ,正解
    true_positive = results.count(True)
    # 抽出できたが、不正解
    false_positive = results.count(False)
    # 抽出したいが、抽出できなかった
    false_negative = len(test) - true_positive

    return true_positive, false_positive, false_negative, len(test)
        
def evaluation(c):
    """計上したTrue positiveなどから、適合率、再現率、F値をDataframe化する"""
    # ToDO: 0のときどうするか
    if c['true_positive'] == 0 and c['false_positive'] == 0 and c['false_negative'] == 0:
        return

    if c['true_positive'] == 0 and c['false_positive'] == 0:
        precision = 0
    else:
        precision = c['true_positive'] / (c['true_positive'] + c['false_positive'])

    recall = c['true_positive'] / (c['true_positive'] + c['false_negative'])

    if precision == 0 and recall == 0:
        f_measure = 0
    else:
        f_measure = (2 * recall * precision) / (recall + precision)

    return precision, recall, f_measure, c['support']
    
