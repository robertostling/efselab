#!/bin/bash

# Path to where the supplementary data from the CoNLL2017 shared task is
# unpacked: https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-1990
CONLLPATH=/home/robert/local/udpipe/udpipe-ud-2.0

TRAIN_FILES=`ls /home/corpora/ud/ud-treebanks-v2.0/*/*-ud-train.conllu`

UDPIPE="../../local/udpipe/src/udpipe"

mkdir -p udv2_udpipe_models

for TRAIN_FILE in $TRAIN_FILES; do
    DEV_FILE=`echo $TRAIN_FILE | sed 's/ud-train.conllu/ud-dev.conllu/'`
    LANGCODE=`basename $TRAIN_FILE | sed 's/-ud-train.conllu//'`
    MODEL_FILE=udv2_udpipe_models/"$LANGCODE".model
    OPTIONS=`grep '^'$LANGCODE' ' $CONLLPATH/params_tagger | cut -d ' ' -f 2`
    if [ -z $OPTIONS ]; then
        echo "No options available for $LANGCODE"
    fi
    VECTORS="$CONLLPATH/ud-2.0-baselinemodel-train-embeddings/$LANGCODE"'.skip.forms.50.vectors'
    if [ ! -e $DEV_FILE ]; then
        echo "Development data not available: $DEV_FILE"
    fi
    if [ ! -e $VECTORS ]; then
        echo Word vectors not available: $VECTORS
    else
        OPTIONS="$OPTIONS"';embedding_form_file='"$VECTORS"
    fi
    CMD="$UDPIPE --tokenizer=none --tagger='$OPTIONS' --parser=none \
        --train $MODEL_FILE --heldout=$DEV_FILE $TRAIN_FILE"
    echo $CMD
    sem -j 16 $CMD
done

sem --wait

