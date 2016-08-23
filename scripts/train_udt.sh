#!/bin/bash

OUTPUT=$1
if [ -z "$OUTPUT" ]; then
    echo "Usage: train_udt.sh output-file"
    exit 1
fi

for TRAIN in `ls udt/*-train.tab`; do
    DEV=`echo $TRAIN | sed 's/-train/-dev/'`
    TEST=`echo $TRAIN | sed 's/-train/-test/'`
    LANGUAGE=`echo $TRAIN | grep -Po '[a-z_]+-ud-train' | sed 's/-ud-train//'`
    MODEL="udt_$LANGUAGE"
    #if [[ $TRAIN == *"sv-ud"* ]]; then
        echo "Evaluating $MODEL"
        python3 build_udt.py --train $TRAIN
        ./$MODEL train $TRAIN $DEV $MODEL.bin
        echo $LANGUAGE >>$OUTPUT
        ./$MODEL tag $TEST $MODEL.bin evaluate >/dev/null 2>>$OUTPUT
    #fi
done

