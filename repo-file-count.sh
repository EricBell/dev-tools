#!/bin/bash

# Count the number of files (blobs) in a GitHub repository.
#
# The script uses the GitHub CLI (`gh`) to:
# 1) Look up the repository's default branch.
# 2) Fetch the full recursive tree for that branch.
# 3) Count only entries of type `blob`, which represent files.

if [ $# -eq 0 ]; then
  echo "Usage: $0 <owner/repo>"
  exit 1
fi

# Ask GitHub which branch is the repository's default branch.
DEFAULT_BRANCH=$(gh api repos/$1/$2 --jq '.default_branch')

# Fetch every item in that branch's tree and count the file entries.
gh api "repos/$1/$2/git/trees/$DEFAULT_BRANCH?recursive=1" | jq '[.tree[] | select(.type=="blob")] | length'
