#!/usr/bin/env bash

python modified_gensim/setup.py clean_ext
python modified_gensim/setup.py build_ext --inplace
while [ true ] ; do
	read -s -N 1 -t 1 key
	if [[ $key == $'\x0a' ]] ; then
		exit ;
	fi
done