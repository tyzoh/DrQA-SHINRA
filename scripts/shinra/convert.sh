#!/bin/bash

mode=train
label=multipleanswer
target=Company

data_dir=./data
datasets_dir=${data_dir}/datasets
work_dir=${data_dir}/work
work_label_dir=${work_dir}/${mode}-${label}
mkdir ${work_dir}
mkdir ${work_label_dir}
multiple_answer=" --multiple-answer"

# Convert to shinra 2018 format
python scripts/shinra/shinra2019_to_2018.py ${datasets_dir}/annotation/${target}_dist.json ${work_dir}/${target}_dist_2018.json

# Convert to SQuAD format
python scripts/shinra/shinra_to_squad.py ${work_dir}/${target}_dist_2018.json ${work_label_dir}/squad_${target}.json ${multiple_answer}

# Preprocess SQuAD format data for DrQA
python scripts/shinra/preprocess.py ${work_label_dir} ${work_label_dir} --split squad_${target}-dev --tokenizer mecab${multiple_answer}
python scripts/shinra/preprocess.py ${work_label_dir} ${work_label_dir} --split squad_${target}-test --tokenizer mecab${multiple_answer}
python scripts/shinra/preprocess.py ${work_label_dir} ${work_label_dir} --split squad_${target}-train --tokenizer mecab${multiple_answer}