#!/bin/bash

mode=train
#label=answerspan
label=multipleanswer
target=Company

data_dir=./data
work_dir=${data_dir}/work/${mode}-${label}

model_dir=${data_dir}/drqa-models/${mode}-${label}
mkdir ${data_dir}/drqa-models
mkdir ${model_dir}

python scripts/reader/train.py \
    --embed-dir ${data_dir}/embeddings \
    --embedding-file cc.ja.300.vec \
    --embedding-dim 300 \
    --model-dir ${model_dir} \
    --data-dir ${work_dir} \
    --train-file squad_${target}-train-processed-mecab.txt \
    --dev-file squad_${target}-dev-processed-mecab.txt \
    --dev-json squad_${target}-dev.json \
    --valid-metric f1 \
    --batch-size 4 \
    --test-batch-size 4 \
    --num-epochs 30 \
    --multiple-answer True \
    --shinra-eval True

