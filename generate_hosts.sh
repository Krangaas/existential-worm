#!/bin/bash
touch host_list.txt
rocks list host | grep compute | cut -d" " -f1 | sed 's/.$//' | shuf | head -n $1 > host_list.txt
