#!/bin/bash

set -e

pull_number=$(jq --raw-output .pull_request.number "$GITHUB_EVENT_PATH")

echo "Running on Pull Request #$pull_number"
