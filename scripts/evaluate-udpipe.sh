#!/bin/bash

OUTPUT="$1"
PART="$2"

if [ -z "$OUTPUT" -o -z "$PART" ]; then
    echo "Usage: $0 target-file.txt test|dev"
    exit 1
fi

UDPIPE=../../local/udpipe/src/udpipe

if [ "$PART" == "dev" ]; then
    for DEVFILE in `ls /home/corpora/ud/ud-treebanks-v2.0/*/*-ud-dev.conllu`; do
        LANGCODE=`basename $DEVFILE | sed 's/-ud-dev.conllu//'`
        ACCURACY=`$UDPIPE --accuracy --tag \
            udv2_udpipe_models/"$LANGCODE".model $DEVFILE \
            | grep -Po 'upostag: (\d+\.\d+)' | sed 's/upostag: //'`
        echo $LANGCODE $ACCURACY
        echo $LANGCODE $ACCURACY >>$OUTPUT
    done
elif [ "$PART" == "test" ]; then
    for TESTFILE in `ls /home/corpora/ud/ud-treebanks-v2.0/*/*-ud-test.conllu`; do
        LANGCODE=`basename $TESTFILE | sed 's/-ud-test.conllu//'`
        ACCURACY=`$UDPIPE --accuracy --tag \
            udv2_udpipe_models/"$LANGCODE".model $TESTFILE \
            | grep -Po 'upostag: (\d+\.\d+)' | sed 's/upostag: //'`
        echo $LANGCODE $ACCURACY
        echo $LANGCODE $ACCURACY >>$OUTPUT
    done
    echo "FIXME: remove exit here!"
    exit 0
    for TESTFILE in `ls /home/corpora/ud/ud-test-v2.0-conll2017/gold/conll17-ud-test-2017-05-09/*.conllu`; do
        LANGCODE=`basename $TESTFILE | sed 's/.conllu//'`
        ACCURACY=`$UDPIPE --accuracy --tag \
            udv2_udpipe_models/"$LANGCODE".model $TESTFILE \
            | grep -Po 'upostag: (\d+\.\d+)' | sed 's/upostag: //'`
        echo $LANGCODE $ACCURACY
        echo $LANGCODE $ACCURACY >>$OUTPUT
    done
fi

