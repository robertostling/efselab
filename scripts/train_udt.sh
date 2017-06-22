#!/bin/bash

# NOTE: this script uses GNU parallel to distribute the job over all CPU
# cores, in case you have more cores than memory you might want to change
# this setting (which launches one job per core):
N_CORES="+0"

TAGGER_OPTIONS="--beam-size 4"

OUTPUT=$1
if [ -z "$OUTPUT" ]; then
    echo "Usage: scripts/train_udt.sh output-file"
    exit 1
fi

# Expression for which languages should be included in the evaluation:
LANGS='*'

# Path of .tab files
DATAPATH=udv2

# First compile all the models

for TRAIN in `ls $DATAPATH/$LANGS-ud-train.tab`; do
    sem -j"$N_CORES" python3 build_udt.py --train "$TRAIN" $TAGGER_OPTIONS
done

sem --wait

echo "Compiling finished, training..."

# Then, train all the models in parallel

for TRAIN in `ls $DATAPATH/$LANGS-ud-train.tab`; do
    DEV=`echo $TRAIN | sed 's/-train/-dev/'`
    TEST=`echo $TRAIN | sed 's/-train/-test/'`
    LANGUAGE=`echo $TRAIN | grep -Po '[a-z_]+-ud-train' | sed 's/-ud-train//'`
    MODEL="udt_$LANGUAGE"
    sem -j"$N_CORES" ./$MODEL train "$TRAIN" "$DEV" $MODEL.bin
done

sem --wait

echo "Training finished, evaluating..."

# Finally, perform the evaluations (quick)

for TRAIN in `ls $DATAPATH/$LANGS-ud-train.tab`; do
    DEV=`echo $TRAIN | sed 's/-train/-dev/'`
    TEST=`echo $TRAIN | sed 's/-train/-test/'`
    LANGUAGE=`echo $TRAIN | grep -Po '[a-z_]+-ud-train' | sed 's/-ud-train//'`
    MODEL="udt_$LANGUAGE"
    if [ -e $DEV ]; then
        echo $LANGUAGE dev >>$OUTPUT
        ./$MODEL tag $DEV $MODEL.bin evaluate >/dev/null 2>>$OUTPUT
    fi
    if [ -e $TEST ]; then
        echo $LANGUAGE test >>$OUTPUT
        ./$MODEL tag $TEST $MODEL.bin evaluate >/dev/null 2>>$OUTPUT
    fi
done

for TRAIN in `ls $DATAPATH/$LANGS-ud-train.tab`; do
    LANGUAGE=`echo $TRAIN | grep -Po '[a-z_]+-ud-train' | sed 's/-ud-train//'`
    MODEL="udt_$LANGUAGE"
    rm $MODEL.bin $MODEL.c $MODEL
done

