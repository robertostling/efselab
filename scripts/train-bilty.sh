#!/bin/bash

# Script to train models for https://github.com/bplank/bilstm-aux
#
# First, convert the UD treebank with scripts/udt2tab.py:
#
#   mkdir udv2
#   python3 scripts/udt2tab.py ud-treebanks-v2.0 udv2
#
# Modify the necessary paths in this scrips.
#
# Then run this script without arguments:
#
#   scripts/train-bilty.sh 

export LD_PRELOAD=/opt/intel/mkl/lib/intel64/libmkl_core.so:/opt/intel/mkl/lib/intel64/libmkl_sequential.so

#TRAIN_FILES=`ls udv2/*-ud-train.tab`
TRAIN_FILES=`ls udv2/en-ud-train.tab udv2/fi-ud-train.tab udv2/ru_syntagrus-ud-train.tab`

BILTY="python3 ../../local/bilstm-aux/src/bilty.py"

mkdir -p udv2_bilty_models

for TRAIN_FILE in $TRAIN_FILES; do
    DEV_FILE=`echo $TRAIN_FILE | sed 's/ud-train.tab/ud-dev.tab/'`
    MODEL_FILE=udv2_bilty_models/`basename $TRAIN_FILE | sed 's/-ud-train.tab//'`
    CMD="$BILTY  --dynet-seed 1512141834 --dynet-mem 1500 \
        --train $TRAIN_FILE --dev $DEV_FILE \
        --in_dim 64 --c_in_dim 100 --trainer sgd --iters 20 --sigma 0.2 \
        --save $MODEL_FILE \
        --h_layers 3 --pred_layer 3"
    echo $CMD
    sem -j 12 $CMD >"$MODEL_FILE".out 2>"$MODEL_FILE".err
done

sem --wait

