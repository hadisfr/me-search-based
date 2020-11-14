#!/usr/bin/env bash

RNUNNE="./ga.py"
PREF="ga"

# RNUNNE="./sa.py"
# PREF="sa"

N=10

# set -o xtrace

echo "run $RNUNNE and write in $PREF"

[ -d $PREF ] && rm --interactive=once -r $PREF
[ -d $PREF ] && exit 1
mkdir $PREF

for i in $(seq $N); do
    echo ""
    echo -e "\e[96mrun $i\e[0m"
    echo -e "\e[36m======\e[0m"
    time $RNUNNE $PREF/$i;
done
