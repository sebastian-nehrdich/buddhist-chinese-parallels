cd ../data/tsv;
cat *tsv >> all.txt;
perl -i -pe "s/.*\t(.*)/\1/g;" all.txt;
fasttext skipgram -dim 100 -input all.txt -output ../chinese;
rm all.txt;

