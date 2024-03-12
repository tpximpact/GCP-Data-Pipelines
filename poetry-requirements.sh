#!/bin/zsh

find . -not -path '*/\.*' -type f -name "*.toml" | while read toml_file; do
  dir=$(dirname "$toml_file")
  cd "$dir" || exit
  echo "Exporting requirements.txt in $dir"
  poetry lock --no-update
  poetry export --format=requirements.txt --output=requirements.txt --without-hashes
  sed -i '' -E 's/@[0-9a-f]{40}//g' requirements.txt
  cd - > /dev/null
done