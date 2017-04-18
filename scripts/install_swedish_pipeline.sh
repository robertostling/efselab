#!/bin/sh

# Build lemmatizer
make

# Download and build models
if [ ! -e swe-pipeline-ud2.tar.gz ]; then
    wget http://mumin.ling.su.se/projects/efselab/swe-pipeline-ud2.tar.gz
    tar xvzf swe-pipeline-ud2.tar.gz
    python3 build_suc.py --skip-generate --python --n-train-fields 2
    python3 build_suc_ne.py --skip-generate --python --n-train-fields 4
fi

# Build and train the SUC-to-UD conversion model
python3 build_udt_suc_sv.py --python --beam-size 1 --n-train-fields 4
./udt_suc_sv train \
    data/sv-ud-train.tab data/sv-ud-dev.tab swe-pipeline/suc-ud.bin

