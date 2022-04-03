#!/bin/bash

# TODO: instead of having the folders hard-coded here,
#     :    source this information from configuration

if [ -r ../.env ]; then
    source ../.env
else
    echo "Environment file missing on unreadable" >&2
    exit 1
fi

for dir in uploads datastore; do
    if [ ! -d ../$dir ]; then
        mkdir ../$dir
    fi
done
