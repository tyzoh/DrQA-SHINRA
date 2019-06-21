#!/bin/bash

mode=train
#label=answerspan
label=multipleanswer
target=Company

data_dir=./data
work_dir=${data_dir}/work/${mode}-${label}

model_dir=${data_dir}/drqa-models/${mode}-${label}
latest_model="`pwd`/`ls -lt ${model_dir}/*.mdl | head -n 1 | gawk '{print $9}'`"
model_ext="${latest_model##*/}"
model_fname="${model_ext%.*}"

embed_dir=${data_dir}/embeddings
embedding_file=cc.ja.300.vec
embedding_dim=300
batch_size=4
top_n=20
#min_score=" --min-score 0.01"
#debug=" --debug"
#otherparam=" --no-cuda"

python scripts/shinra/predict_shinra.py ${work_dir}/squad_${target}-test.json --model ${latest_model} --embedding-file ${embed_dir}/${embedding_file} --tokenizer "mecab" --batch-size ${batch_size} --out-dir ${model_dir} --top-n ${top_n}${otherparam}

python scripts/shinra/evaluate_shinra.py --predicate-json ${model_dir}/squad_${target}-test-${model_fname}.preds.json --answer-json ${data_dir}/work/${target}_dist_2018-test.json${min_score}${debug} > ${model_dir}/eval_${target}-test-${model_fname}.log
