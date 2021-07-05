#!/bin/bash

set -e

echo "checking URLs..."

unset failed
while IFS= read -r line
do
    if curl -fs "$line" > /dev/null ; then
        echo -e " \033[32;1m✅\033[0m $line \033[32;1msuccess\033[0m"
    else
        echo -e " \033[31;1m❌\033[0m $line \033[31;1mfailed\033[0m"
        failed=1
    fi
done

if [ -z ${failed+x} ]; then
    echo "check successfully"
else 
    echo "check failed"
    false   
fi
