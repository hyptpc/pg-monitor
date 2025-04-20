#!/bin/sh

# /usr/pgsql-16/bin/psql -U postgres -d e73 -f create-table-hoge.sql

psql -d e72 -f sql/create-table-dhcp.sql
