#!/bin/bash

cd "$(dirname "$0")"

name=alert-receiver
script=alert-receiver.py

if tmux has-session -t "$name" 2>/dev/null; then
  tmux attach-session -t "$name"
else
  tmux new-session -s "$name" "python $script"
fi
