# Convert from the UD CoNLL-U format to the token/tab format used here.
# Usage example:
#   ./convert-ud-tab.sh universal-dependencies-1.2/UD_Finnish fi

SOURCE=$1
LANG=$2

grep -v '^#' $SOURCE/$LANG-ud-train.conllu | awk -v OFS="\t" -F"\t" '{print $3,$4}' | sed 's/^\t//' >$LANG-ud-train.tab
grep -v '^#' $SOURCE/$LANG-ud-dev.conllu | awk -v OFS="\t" -F"\t" '{print $3,$4}' | sed 's/^\t//' >$LANG-ud-dev.tab
grep -v '^#' $SOURCE/$LANG-ud-test.conllu | awk -v OFS="\t" -F"\t" '{print $3,$4}' | sed 's/^\t//' >$LANG-ud-test.tab
