#!/bin/bash

if [ -r ../.env ]; then
    source ../.env
else
    echo "Environment file missing on unreadable" >&2
    exit 1
fi

if [[ -z "$DATABASE_HOST" || -z "$DATABASE_USER" || -z "$DATABASE_NAME" ]]; then
    echo "Environment parameters missing" >&2
    exit 1
fi

if [[ -z "$PYTHONANYWHERE_DOMAIN" ]]; then
    pa_options=""
else
    # options applicable for PythonAnywhere
    pa_options="--set-gtid-purged=OFF --column-statistics=0"
fi

echo "Issue to disable FK constraints: SET FOREIGN_KEY_CHECKS=0;"
mysql -u "$DATABASE_USER" -h "$DATABASE_HOST" -P "$DATABASE_PORT" "$DATABASE_NAME"
