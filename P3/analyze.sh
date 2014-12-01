#!/bin/bash

for DATA_SET in "books" "robust-class" "robust-community";
do
   for METHOD in "cluster" "rm" "ql" "lda" "qlda" "combined";
   do
      ~/galago-3.6/galago-3.6-bin/bin/galago eval --judgments=../qrels/${DATA_SET}.qrels --runs+output/${DATA_SET}-${METHOD} --details=true --metrics+map --metrics+ndcg20 --metrics+P10 | grep "^output" >> results
      echo $DATA_SET $METHOD
   done
done


