#!/bin/bash
sh create_word_embedding.sh;
cd calculate-quotes;
python create_words_vectors_chinese.py;

use SLURM here if you have it available!
for i in ../../work/folder*;
do python calculate_quotes.py $i ../../work/ chn;
done
# needs to be done twice
for i in ../../work/folder*;
do python calculate_quotes.py $i ../../work/ chn;
done

for i in ../../work/folder*;
do python process_lists.py $i chn;
done

cd ../merge-quotes;

python create_segment_dic.py;
cd ../;
pigz ../data/segments/*;

for i in ../../work/folder*;
do python merge_quotes.py $i;
done
