#!/bin/bash

for file in *.py
do
 echo "$file"
 cat "$file" | grep AB_model_data
done
