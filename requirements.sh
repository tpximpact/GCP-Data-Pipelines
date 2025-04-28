#!/bin/zsh

find . -mindepth 2 -type f -name "*.toml" | while read toml_file; do
  dir=$(dirname "$toml_file")
  cd "$dir" || exit
  echo "Exporting requirements.txt in $dir"
  uv sync
  uv pip compile pyproject.toml -o requirements.txt
  rm -R .venv
  cd - > /dev/null
done