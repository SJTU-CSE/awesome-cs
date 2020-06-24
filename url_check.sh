#!/bin/bash

set -e

echo "obtaining patch file..."

git diff origin/master:README.md HEAD:README.md | grep -E "^\+" | grep -Eo '(http|https)://[^)"]+' > .patch

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
done < .patch

echo "check successfully"
