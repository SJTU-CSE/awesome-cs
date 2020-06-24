#!/bin/bash

set -e

echo "checking URLs..."

while IFS= read -r line
do
    echo "  checking $line"
    if curl -fs "$line" > /dev/null ; then
        echo "  ... success"
    else
        echo "  ... failed"
        false
    fi
done

echo "check successfully"
