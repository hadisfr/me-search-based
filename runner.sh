#!/usr/bin/env bash

if [[ $# -ne 2 ]]; then
    echo -e "usage:\t$0 <ga|sa> #_of_iterations"
    exit 2
fi


if [[ $1 == "ga" ]]; then
    RNUNNE="./ga.py"
    PREF="ga"
elif [[ $1 == "sa" ]]; then
    RNUNNE="./sa.py"
    PREF="sa"
else
    echo -e "usage:\t$0 <ga|sa> #_of_iterations"
    exit 2
fi

N=$2

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
