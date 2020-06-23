#!/bin/bash

set -e

pull_number=$(jq --raw-output .pull_request.number "$GITHUB_EVENT_PATH")

echo "running on pull request #$pull_number"

echo "fetching patch file..."

curl -sfL https://github.com/SJTU-CSE/awesome-cs/pull/$pull_number.patch | grep -E "^\+" | grep -Eo '(http|https)://[^)"]+' > .patch

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

echo "checking successfully"
