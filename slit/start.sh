#!/bin/sh

top_dir=$(dirname $(readlink -f $0))

name=pg-slit

session=`tmux ls | grep $name 2>/dev/null`
command="while true; do python3 $top_dir/slit.py; sleep 2; done"

if [ -z "$session" ]; then
    echo "create new session $name"
    tmux new-session -d -s $name "$command"
else
    echo "reattach session $name"
    tmux a -t $name
fi
