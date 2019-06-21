# DrQA-SHINRA

Wikipediaに書かれている世界知識を計算機が扱えるような形に変換することを目的とした森羅プロジェクトの森羅2018タスクで用いた手法の実装です．森羅2018タスクは，人名，企業名，市区町村名，空港名，化合物名の5カテゴリのWikipediaページから，定義された属性の値を抽出するタスクです．本手法では，[DrQA](<https://github.com/facebookresearch/DrQA>)のDocument Readerをベースとして用い，属性名を質問，属性値を回答とする機械読解により属性値の抽出を行いました．

[森羅2019のデータ](http://liat-aip.sakura.ne.jp/森羅/森羅wikipedia構造化プロジェクト2019/森羅2019データ配布/)を森羅2018形式に変換し，一部のデータで動作確認をしました．

## 使用方法

### データのダウンロード:

データセットは， [森羅2019データ配布](http://liat-aip.sakura.ne.jp/森羅/森羅wikipedia構造化プロジェクト2019/森羅2019データ配布/)からダウンロードして，以下のように配置してください．単語ベクトルは[fastText website](https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.ja.300.vec.gz)からダウンロードできます．

※森羅2018タスクで使用した単語ベクトルは，日本語Wikipedia全文をMeCabで空白区切りにしたファイルから[fastText](<https://github.com/facebookresearch/fastText>)を用いて作成したものです．

```
DrQA-SHINRA
|____ data                     
|       |____ datasets              # 森羅2019のサイトからダウンロードするデータセット
|       |   |____ annotation
|       |   |       |____ Company_dist.json
|       |   |         ...
|       |   |____ HTML
|       |           |____ Company
|       |           |       |____xxxxx.html
|       |             ...
|       |____ drqa-models           # train.shがモデルファイルを出力するディレクトリ
|       |____ embeddings        
|       |   |____ cc.ja.300.vec     # fastTextのサイトからダウンロードする単語ベクトル 
|       |____ work                  # convert.shが前処理後のファイルを出力するディレクトリ
|____ drqa                          # メインソースコード
|____ scripts                       
        |____ shinra                # 森羅データセット用のスクリプト
```

### 前処理：

```
sh scripts/shinra/convert.sh
```

3. ```scripts/shinra/shinra2019_to_2018.py```

   森羅2018のフォーマットと似た形式に変換し，```[target]_dist_2018.json```ファイルを作成します．このとき評価用の解答データも```[target]_dist_2018-test.json```という名前で作成します。

4. ```scripts/shinra/shinra_to_squad.py```

   3で出力したファイルをSQuAD形式に変換します．Infoboxを自然文に置き換える処理と，HTMLタグをスペースに置換する処理を行います．```--addtitle True```(デフォルト)とすると，質問が"成田国際空港(Wikipediaタイトル)の所在地(属性名)は？"という文に変換されます．

5. ```scripts/shinra/preprocess.py```

   DrQA Document Readerの前処理を実行します．MeCabの単語の切れ目と解答のOffsetが合わない場合，Assertion Errorが出力され，その解答は学習データに設定されません．

### 学習：

```
sh scripts/shinra/train.sh
```

DrQA Document Readerの学習を実行します．```--multiple-answer True```とすると，複数回答対応版が動きます．```--shinra-eval True```とすると，森羅タスク用のValidationが実行されます．

### 予測と評価：

```
sh scripts/shinra/predict.sh
```

1. ```scripts/shinra/predict_shinra.py```

   学習したモデルを用いた予測を実行します．予測結果は```squad_${target}-test-${model_fname}.preds.json```というファイルに出力されます．

2. ```scripts/shinra/evaluate_shinra.py```

   1が出力した予測結果を整形して```squad_${target}-test-${model_fname}.pred_eval.json```に出力し，評価結果を```eval_${target}-test-${model_fname}.log```に出力します．



学習時のValidationに使用する```scripts/reader/validate_shinra.py```および，評価結果の算出に使用する```scripts/shinra/evaluation.py```は，[Sansan株式会社提供のスクリプト](<https://gist.github.com/kanjirz50/616b3a1c069dc4b0a4d9357457f6a105>)をベースにしています．



## 評価結果:

データセットを train (85%), dev (5%), test (10%)に分割し，学習にはtrain，モデル選択にdev，評価にtestを使用した結果を以下に記載します．

GPU搭載マシン(4 コア / 8 T / 3.60GHz, 64GB メモリ, NVIDIA GeForce GTX 1080 Ti 11GB)を使用しました． (時間短縮のため，train.pyのtrainデータに対するバリデーションのコードをコメントアウトして実行)

#### 企業名 (HTML):

* 学習時間：約24時間 (学習サンプル数 = 29925, モデル選択サンプル数 = 1785)
* embedding_file=cc.ja.300.vec
* num-epochs=30 (best epoch = 22)
* multiple_answer=True
* batch_size=4
* top_n=20

```
                     attribute  precision  recall  f1-score  support
0                     正式名称      0.552   0.399     0.463      386
1                     ふりがな      0.911   0.879     0.895       58
2                         別名      0.734   0.095     0.168      610
3                         種類      0.974   0.916     0.944       83
4                     本拠地国      0.933   0.916     0.925      107
5                       本拠地      0.844   0.750     0.794      188
6                       設立年      0.850   0.613     0.713      194
7                         業界      0.931   0.817     0.870       82
8                     事業内容      0.466   0.395     0.428      471
9                     取扱商品      0.476   0.238     0.317      937
10                      代表者      0.851   0.843     0.847      102
11                      資本金      0.910   0.859     0.884       71
12            資本金データの年      0.938   0.556     0.698       27
13            従業員数（単体）      0.889   0.960     0.923       50
14  従業員数（単体）データの年      1.000   1.000     1.000       33
15            従業員数（連結）      0.923   0.857     0.889       14
16  従業員数（連結）データの年      0.857   1.000     0.923       12
17              売上高（単体）      0.800   0.933     0.862       30
18            売上高データの年      0.818   0.964     0.885       28
19              売上高（連結）      0.933   0.824     0.875       17
20    売上高（連結）データの年      0.812   0.867     0.839       15
21                    主要株主      0.709   0.442     0.545      552
22            子会社・合弁会社      0.442   0.169     0.244      635
23            業界内地位・規模      0.185   0.135     0.156       37
24          買収・合併した会社      0.389   0.280     0.326      175
25                        起源      0.188   0.136     0.158       22
26                  過去の社名      0.471   0.285     0.355      200
27                      創業国      0.000   0.000     0.000        3
28                      創業地      0.667   0.370     0.476       27
29                      創業者      0.585   0.522     0.552       46
30                創業時の事業      0.100   0.045     0.063       22
31              社名使用開始年      0.610   0.427     0.503      117
32      コーポレートスローガン      0.600   0.250     0.353       12
33                      商品名      0.472   0.138     0.214     1786
34                      解散年      0.143   0.500     0.222        2

micro-precision: 0.611 micro-recall: 0.325 micro-f1: 0.424
macro-precision: 0.656 macro-recall: 0.554 macro-f1: 0.580
```

#### 空港名 (HTML):

* 学習時間：約5時間 (学習サンプル数 = 12750, モデル選択サンプル数 = 750)
* embedding_file=cc.ja.300.vec
* num-epochs=30 (best epoch = 28)
* multiple_answer=True
* batch_size=4
* top_n=20

```
                   attribute  precision  recall  f1-score  support
0                   ふりがな      1.000   0.907     0.951       54
1         IATA（空港コード）      0.955   0.984     0.969       64
2         ICAO（空港コード）      0.985   1.000     0.992       64
3                       別名      0.760   0.671     0.713      207
4                 名前の謂れ      0.643   0.600     0.621       15
5   名称由来人物の地位職業名      0.222   0.182     0.200       11
6                         国      0.952   0.825     0.884      120
7               年間利用客数      0.730   0.844     0.783       32
8     年間利用者数データの年      0.742   0.767     0.754       30
9               年間発着回数      0.792   0.950     0.864       20
10    年間発着回数データの年      0.889   0.762     0.821       21
11                座標・経度      0.971   1.000     0.985      198
12                座標・緯度      0.981   0.994     0.987      158
13                    所在地      0.657   0.730     0.692      163
14                      旧称      0.367   0.257     0.303       70
15                      標高      0.990   0.990     0.990      103
16                    母都市      0.938   0.714     0.811       21
17                  滑走路数      0.600   0.600     0.600       10
18              滑走路の長さ      0.906   0.828     0.865      116
19                    総面積      0.500   0.556     0.526        9
20                  近隣空港      0.107   0.059     0.076       51
21                    運営者      0.921   0.773     0.841       75
22                  運用時間      0.458   0.524     0.489       21
23                    開港年      0.700   0.318     0.438       44

micro-precision: 0.834 micro-recall: 0.782 micro-f1: 0.807
macro-precision: 0.740 macro-recall: 0.701 macro-f1: 0.715
```

#### 化合物名 (HTML):

* 学習時間：約2時間半 (学習サンプル数 = 7620, モデル選択サンプル数 = 450)
* embedding_file=cc.ja.300.vec
* num-epochs=30 (best epoch = 29)
* multiple_answer=True
* batch_size=4
* top_n=20

```
     attribute  precision  recall  f1-score  support
0         読み      0.955   0.913     0.933       23
1         別称      0.668   0.538     0.596      333
2         用途      0.337   0.369     0.352      241
3         種類      0.529   0.628     0.574       86
4       商標名      0.250   0.034     0.061       29
5         特性      0.177   0.218     0.196      289
6       原材料      0.419   0.153     0.224       85
7     製造方法      0.061   0.042     0.050       71
8   生成化合物      0.000   0.000     0.000       24
9      CAS番号      0.967   1.000     0.983       58
10      化学式      0.814   0.716     0.761      116
11        密度      0.783   0.878     0.828       41
12        融点      0.816   0.765     0.790       81
13        沸点      0.922   0.839     0.879       56
14      示性式      1.000   1.000     1.000        7

micro-precision: 0.496 micro-recall: 0.465 micro-f1: 0.480
macro-precision: 0.580 macro-recall: 0.540 macro-f1: 0.548
```

### 参考文献:

[1] [Reading Wikipedia to Answer Open-Domain Questions](https://arxiv.org/abs/1704.00051)

[2] <https://github.com/facebookresearch/DrQA>

[3] [SHINRA: Structuring Wikipedia by Collaborative Contribution](<https://openreview.net/pdf?id=HygfXWqTpm>)

[4] [機械読解によるWikipediaからの情報抽出](<https://www.anlp.jp/proceedings/annual_meeting/2019/pdf_dir/P1-34.pdf>)

## インストール

DrQA-SHINRA は，Linux/OSX と Python 3.5以上，[PyTorch](http://pytorch.org/) version 1.0で動作します. その他の必要なソフトウェアはrequirements.txtに記載されています. CUDA は処理速度のために推奨されますが，必須ではありません．

以下のコマンドを実行し，リポジトリをクローン後，インスト―ルしてください．

```bash
git clone https://github.com/tyzoh/DrQA-SHINRA.git
cd DrQA-SHINRA; pip install -r requirements.txt; python setup.py develop
```

requirements.txt に記載されている以外の，MeCab等のインストールは必要に応じて個別に行ってください．

## License

DrQA-SHINRA は[DrQA](https://github.com/facebookresearch/DrQA)のBSDライセンスを継承しています. ただし， [Sansan株式会社提供のスクリプト](<https://gist.github.com/kanjirz50/616b3a1c069dc4b0a4d9357457f6a105>)をベースとした以下のスクリプトはMITライセンスで提供されます．

* scripts/reader/validate_shinra.py
* scripts/shinra/evaluation.py