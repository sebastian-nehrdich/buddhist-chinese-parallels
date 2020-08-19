#!/bin/bash
# NOTE: YOu have to run ..//code/create_word_embedding.sh for the evaluation to work properly!
cd code;
python evaluate_vectors.py;
python evaluate_translation.py;
