#!/bin/sh

if [ ! -d suc-data ]; then
    echo "ERROR: no directory suc-data"
    echo "Make sure you have the (licensed) SUC data package, and that you"
    echo "execute this script from the efselab root directory, not scripts/"
    exit 1
fi

EVALDIR="ner-eval"

if [ -d $EVALDIR ]; then
    echo "Directory $EVALDIR already exists, will not overwrite!"
    exit 1
fi

EVALSCRIPT="perl 3rdparty/conlleval.perl"

mkdir $EVALDIR
cut -f 1 suc-data/suc-ne-test.tab | sed 's/ /_/g' >$EVALDIR/test-raw.tab
cut -f 1 suc-data/suc-ne-dev.tab | sed 's/ /_/g' >$EVALDIR/dev-raw.tab
python3 swe-pipeline.py --skip-tokenization --tagged --tokenized \
    --lemmatized --ner \
    --output $EVALDIR $EVALDIR/test-raw.tab $EVALDIR/dev-raw.tab
paste $EVALDIR/test-raw.tab suc-data/suc-ne-test.tab $EVALDIR/test-raw.ne | \
    cut --output-delimiter=" " -f 1,5,7 >$EVALDIR/results-test.tab
paste $EVALDIR/dev-raw.tab suc-data/suc-ne-dev.tab $EVALDIR/dev-raw.ne | \
    cut --output-delimiter=" " -f 1,5,7 >$EVALDIR/results-dev.tab

echo "DEVELOPMENT SET"
$EVALSCRIPT <$EVALDIR/results-dev.tab
echo "------------------------------------------------------------------------"

echo "TEST SET"
$EVALSCRIPT <$EVALDIR/results-test.tab
echo "------------------------------------------------------------------------"

