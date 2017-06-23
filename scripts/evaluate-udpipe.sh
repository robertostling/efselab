#!/bin/bash

OUTPUT="$1"

if [ -z $OUTPUT ]; then
    echo "Usage: $0 target-file.txt"
    exit 1
fi

UDPIPE=../../local/udpipe/src/udpipe

for DEVFILE in `ls /home/corpora/ud/ud-treebanks-v2.0/*/*-ud-dev.conllu`; do
    LANGCODE=`basename $DEVFILE | sed 's/-ud-dev.conllu//'`
    ACCURACY=`$UDPIPE --accuracy --tag \
        udv2_udpipe_models/"$LANGCODE".model $DEVFILE \
        | grep -Po 'upostag: (\d+\.\d+)' | sed 's/upostag: //'`
    echo $LANGCODE $ACCURACY
    echo $LANGCODE $ACCURACY >>$OUTPUT
done

