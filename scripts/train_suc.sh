#!/bin/bash

# Script to build, train and package a Swedish model
# This requires the (licensed) SUC data files to be present in suc-data/

python3 build_suc.py --python
time ./suc train suc-data/suc-blogs.tab suc-data/suc-dev.tab \
    swe-pipeline/suc.bin
tar cvzf swe-pipeline.tar.gz swe-pipeline pysuc.c --owner=0 --group=0

