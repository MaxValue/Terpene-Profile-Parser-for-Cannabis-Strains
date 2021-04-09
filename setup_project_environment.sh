#!/usr/bin/env bash

dependencies=(
  # "python3.8-dev"\
  "python3.9-venv"\
  "python3-pip"\
)

for dependency in "${dependencies[@]}"; do
  if ! dpkg --search "$dependency" >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get --assume-yes install "${dependencies[@]}"
    break
  fi
done

python3.9 -m venv --clear venv
source venv/bin/activate
  pip install --upgrade pip
  pip install --upgrade wheel
  pip install --upgrade --requirement requirements.txt
deactivate
