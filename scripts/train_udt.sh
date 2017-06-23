#!/bin/bash

# NOTE: this script uses GNU parallel to distribute the job over all CPU
# cores, in case you have more cores than memory you might want to change
# this setting (which launches one job per core):
#N_CORES="+0"

N_CORES="8"

# Serial execution (does not require GNU parallel):
#N_CORES="1"

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
    LANGCODE=`echo $TRAIN | grep -Po '[a-z_]+-ud-train' | sed 's/-ud-train//'`
    MODEL="udt_$LANGCODE"
    if [ ! -e $MODEL ]; then
        if [ $N_CORES -eq 1 ]; then
            python3 build_udt.py --train "$TRAIN" $TAGGER_OPTIONS
        else
            sem -j"$N_CORES" --ungroup python3 build_udt.py \
                --train "$TRAIN" $TAGGER_OPTIONS
        fi
    fi
done

if [ $N_CORES -ne 1 ]; then
    sem --wait
fi


echo "Compiling finished, training..."

# Then, train all the models in parallel

for TRAIN in `ls $DATAPATH/$LANGS-ud-train.tab`; do
    DEV=`echo $TRAIN | sed 's/-train/-dev/'`
    LANGCODE=`echo $TRAIN | grep -Po '[a-z_]+-ud-train' | sed 's/-ud-train//'`
    MODEL="udt_$LANGCODE"
    if [ ! -e "$MODEL".bin ]; then
        if [ $N_CORES -eq 1 ]; then
            ./$MODEL train "$TRAIN" "$DEV" $MODEL.bin
        else
            sem -j"$N_CORES" --ungroup ./$MODEL train \
                "$TRAIN" "$DEV" "$MODEL".bin
        fi
    fi
done

if [ $N_CORES -ne 1 ]; then
    sem --wait
fi

echo "Training finished, evaluating..."

# Finally, perform the evaluations (quick)

for TRAIN in `ls $DATAPATH/$LANGS-ud-train.tab`; do
    DEV=`echo $TRAIN | sed 's/-train/-dev/'`
    TEST=`echo $TRAIN | sed 's/-train/-test/'`
    LANGCODE=`echo $TRAIN | grep -Po '[a-z_]+-ud-train' | sed 's/-ud-train//'`
    MODEL="udt_$LANGCODE"
    if [ -e $DEV ]; then
        echo $LANGCODE dev >>$OUTPUT
        ./$MODEL tag $DEV $MODEL.bin evaluate >/dev/null 2>>$OUTPUT
    fi
    if [ -e $TEST ]; then
        echo $LANGCODE test >>$OUTPUT
        ./$MODEL tag $TEST $MODEL.bin evaluate >/dev/null 2>>$OUTPUT
    fi
done

for TRAIN in `ls $DATAPATH/$LANGS-ud-train.tab`; do
    LANGCODE=`echo $TRAIN | grep -Po '[a-z_]+-ud-train' | sed 's/-ud-train//'`
    MODEL="udt_$LANGCODE"
    rm $MODEL.bin $MODEL.c $MODEL
done

