#!/bin/sh

top_dir=$(dirname $(readlink -f $0))

name=pg-scaler

session=`tmux ls | grep $name 2>/dev/null`
command=$top_dir/bin/scaler

if [ -z "$session" ]; then
    echo "create new session $name"
    tmux new-session -d -s $name "$command"
else
    echo "reattach session $name"
    tmux a -t $name
fi
