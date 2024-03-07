#!/bin/zsh

find . -not -path '*/\.*' -type f -name "*.toml" | while read toml_file; do
  dir=$(dirname "$toml_file")
  cd "$dir" || exit
#   echo "Exporting requirements.txt in $dir"
  poetry export --format=requirements.txt --output=requirements.txt --without-hashes
  cd - > /dev/null
done