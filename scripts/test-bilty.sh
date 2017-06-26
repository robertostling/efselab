#!/bin/bash

# Script to evaluate models for https://github.com/bplank/bilstm-aux
#
# See train-bilty.sh for details.

OUTPUT="$1"

if [ -z "$OUTPUT" ]; then
    echo "Usage: $0 result.txt"
    exit 1
fi

export LD_PRELOAD=/opt/intel/mkl/lib/intel64/libmkl_core.so:/opt/intel/mkl/lib/intel64/libmkl_sequential.so

TEST_FILES=`ls udv2/*-ud-test.tab`

BILTY="python3 ../../local/bilstm-aux/src/bilty.py"

mkdir -p udv2_bilty_models

for TEST_FILE in $TEST_FILES; do
    LANGCODE=`basename $TEST_FILE | sed 's/-ud-test.tab//'`
    MODEL_FILE=udv2_bilty_models/"$LANGCODE".model
    if [ -e $MODEL_FILE ]; then
        CMD="$BILTY  --dynet-seed 1512141834 --dynet-mem 1500 \
            --test $TEST_FILE \
            --model $MODEL_FILE \
            --pred_layer 3"
        echo $CMD
        ACC=`$CMD 2>&1 | grep 'Task0 test accuracy on 1 items' | \
            sed 's/Task0 test accuracy on 1 items: //'`
        echo $LANGCODE $ACC >>$OUTPUT
    fi
done

