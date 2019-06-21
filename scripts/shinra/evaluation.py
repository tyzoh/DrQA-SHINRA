#!/usr/bin/env python3
# Copyright 2018 Sansan, Inc. 
# Copyright 2019 Nihon Unisys, Ltd. 
#
# This source code is licensed under the MIT license.

from collections import Counter

import pandas as pd
pd.options.display.precision = 3
pd.options.display.unicode.east_asian_width = True

class WikiepediaEvaluation:
    """抽出した属性情報を評価する。
    使い方：
    from evaluation import WikiepediaEvaluation

    # 学習データの読み込み
    with open('../data/train-20180516T074039Z-001/company_train.json') as f:
        data = json.load(f)

    preds = SomeExtractor.extract(data)

    we = WikiepediaEvaluation(data)
    result = we.evaluate(preds)
    """

    def __init__(self, train_data, ignore_offset=False, debug=False):
        self.train_data = train_data
        self.ignore_offset = ignore_offset
        self.debug = debug

    def init_attribute_counts(self):
        first_entry = self.train_data['entry'][0]
        self.attribute_counts = dict(
            [(attr, Counter(true_positive=0, false_positive=0, false_negative=0, support=0))
             for attr in first_entry['Attributes_html'].keys()]
        )

    def evaluate(self, preds):
        """評価"""
        self.init_attribute_counts()
        for pred, test in zip(preds['entry'], self.train_data['entry']):
            
            page_id = test['page_id']
            for k in test['Attributes_html'].keys():
                #tp, fp, fn, support = self.count_tp_fp_fn(pred["Attributes"][k], test["Attributes_html"][k])
                try:
                    if self.debug: print('-'*3, test['title'], test['page_id'], k, '-'*3, )
                    tp, fp, fn, support = self.count_tp_fp_fn_offset(pred["Attributes"][k], test["Attributes_html"][k], self.ignore_offset, self.debug)
                except KeyError as e:
                    print('KeyError! page_id', e)
                    continue
                attribute_count = self.attribute_counts[k]
                attribute_count['true_positive'] += tp
                attribute_count['false_positive'] += fp
                attribute_count['false_negative'] += fn
                attribute_count['support'] += support
        
        result = pd.DataFrame(
            [(k, *self.evaluation(v)) for k, v in self.attribute_counts.items()],
            columns=["attribute", "precision", "recall", "f1-score", "support", "true_positive", "false_positive", "false_negative"]
        )
        return result

    @staticmethod
    def count_tp_fp_fn(pred, test):
        """True positive, False positive, False negativeの個数を計算する"""
        gold = list(set([t['text'] for t in test]))
        pred = list(set([list(d.keys())[0] for d in pred]))
        results = [(item in gold) for item in pred]

        # 抽出できたうえ,正解
        true_positive = results.count(True)
        # 抽出できたが、不正解
        false_positive = results.count(False)
        # 抽出したいが、抽出できなかった
        false_negative = len(test) - true_positive

        return true_positive, false_positive, false_negative, len(gold)

    @staticmethod
    def count_tp_fp_fn_offset(pred, test, ignore_offset=False, debug=False):
        target = [((e['start']['line_id'],e['start']['offset']),(e['end']['line_id'],e['end']['offset'])) for e in test]
        target_t = [e['text'] for e in test]
        if debug: print('target', target)
        if debug: print('target_t', target_t)
        
        pred_t = [e[0]['text'] for e in pred]
        pred = [((e[0]['start']['line_id'],e[0]['start']['offset']),(e[0]['end']['line_id'],e[0]['end']['offset'])) for e in pred]
        
        if debug: print('pred', pred)
        if debug: print('pred_t', pred_t)
        
        if ignore_offset:
            results = [(p_t in list(set(target_t))) for p_t in list(set(pred_t))]
        else:
            results = [(_p in target) for _p in pred]
        if debug: print('results', results)
        # 抽出できたうえ,正解
        true_positive = results.count(True)
        # 抽出できたが、不正解
        false_positive = results.count(False)
        # 抽出したいが、抽出できなかった
        false_negative = len(test) - true_positive

        return true_positive, false_positive, false_negative, len(test)

        
    @staticmethod
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
        
        return precision, recall, f_measure, c['support'], c['true_positive'], c['false_positive'], c['false_negative']
