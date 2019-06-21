#!/usr/bin/env python3
# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
# Copyright 2019 Nihon Unisys, Ltd. 
# 
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
"""Tokenizer for Japanese that is backed by MeCab"""

import copy
import json
import re
import unicodedata

from .tokenizer import Tokens, Tokenizer
from . import DEFAULTS
import MeCab

tagger = MeCab.Tagger('-F %m\\t%H\\n')
info = tagger.dictionary_info()
print(info.charset)

comma_pattern = re.compile(r'([^\d])[,]|[,]([^\d])')
hyphen_pattern = re.compile(r'([^\dA-z])[\-‐−]|[\-‐−]([^\dA-z])')

class MecabTokens(Tokens):
    LINE_OFFSETS = 6

    def untokenize(self):
        """Returns the original text (with whitespace reinserted)."""
        return ''.join([t[self.TEXT_WS] for t in self.data])#.strip()

    def line_offsets(self):
        """Returns a list of [start, end) character offsets of each token."""
        return [t[self.LINE_OFFSETS] for t in self.data]

class MecabTokenizer(Tokenizer):
  
  def __init__(self, **kwargs):
    """
    Args:
      annotators: set that can include pos, lemma, and ner.
      classpath: Path to the corenlp directory of jars
      mem: Java heap memory
    """
    #self.classpath = (kwargs.get('classpath') or
    #          DEFAULTS['corenlp_classpath'])
    self.annotators = copy.deepcopy(kwargs.get('annotators', set()))
    self.mem = kwargs.get('mem', '2g')
    #self._launch()
    self.annotators = copy.deepcopy(kwargs.get('annotators', set()))
    nlp_kwargs = {'parser': False}
    if not any([p in self.annotators for p in ['lemma', 'pos', 'ner']]):
      nlp_kwargs['tagger'] = False
    if 'ner' not in self.annotators:
      nlp_kwargs['entity'] = False


  @staticmethod
  def normalize(line):
    #line = unicodedata.normalize('NFKC', line)
    #line = line.replace(' ','　')
    return line

  def tokenize(self, text):
    org_text = text
    text = text.rstrip()
    #text = self.normalize(text)
    tagger.parse('')

    data = []
    idx_s =0
    lines = org_text.split('\n')
    current_line = 0
    current_line_begin_offset = 0
    for token in tagger.parse(text).splitlines()[:-1]:
      elems = token.split("\t")
      if len(elems) < 2: continue
      surface = elems[0]

      start_ws = text.find(surface, idx_s)
      end = start_ws+len(surface)
      end_ws = end
      if end_ws < len(text) and text[end_ws] == ' ':
        end_ws += 1
      idx_s = end_ws
      features = elems[1].split(',') 
      
      while current_line < len(lines) and (current_line_begin_offset + len(lines[current_line]) < start_ws):
        current_line_begin_offset +=  len(lines[current_line]) + 1
        current_line += 1
      line_id = current_line
      line_offset = start_ws - current_line_begin_offset
      
      if surface == 'φ':
        ent_type = 'φ'
      else:
        ent_type = '*'
      
      if features[6] == '*' or features[6] == surface:
        l = org_text[start_ws: end]
      else:
        l = features[6]
        
      data.append((
        org_text[start_ws: end],
        org_text[start_ws: end_ws],
        (start_ws, end), 
        features[0]+'_'+features[1]+'_'+features[2],
        l,
        ent_type,
        (line_id, line_offset)
      ))

    return MecabTokens(data, self.annotators, opts={'non_ent': ''})
