#!/bin/bash

echo $PWD/$3;
for item in $(find $PWD/$3 -type f -not -path '*/\.*' -exec basename {} \;| grep .sql )
do  
    echo $item; 
    $EXAPLUS -x -c $1:$2 -u sys -p exasol -f $PWD/$3/$item;
done;

