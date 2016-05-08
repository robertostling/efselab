#!/bin/bash

# Script to build, train and package a Swedish model
# This requires the (licensed) SUC data files to be present in suc-data/

python3 build_suc.py --python
time ./suc train suc-data/suc-blogs.tab suc-data/suc-dev.tab \
    swe-pipeline/suc.bin
python3 build_suc_ne.py --python
time ./suc_ne train suc-data/suc-blogs-ne-train.tab suc-data/suc-ne-dev.tab \
    swe-pipeline/suc-ne.bin
tar cvzf swe-pipeline.tar.gz swe-pipeline pysuc.c pysuc_ne.c --owner=0 --group=0

