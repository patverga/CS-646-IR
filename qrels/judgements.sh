#!/bin/bash

QREL=$1
QUERIES=$2
INDEX=$3
OUTPUT=$4
RESULTS=${QUERIES}.results
GALAGO=~/galago-3.6/galago-3.6-bin/bin/galago

# run the queries we want to evalute
echo "Running Queries..."
$GALAGO batch-search --index=$INDEX --corpus=${INDEX}/corpus/ $QUERIES >> $RESULTS

# need to add a 0 column for galago for some reason
echo "Adding column to qrel"
awk '{print $1" 0 "$2" "$3}' $QREL > ${QREL}.galago

# evaluate
echo "Evaluating..."
$GALAGO eval --judgments=${QREL}.galago --runs+${RESULTS} --details=true --metrics+map --metrics+ndcg20 --metrics+P10 > $OUTPUT


