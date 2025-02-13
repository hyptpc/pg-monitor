#!/bin/bash

api_key=$(<api-token)
grafana_host=192.168.1.242
port=3000
dashboard_uid=fdh0b69n4k0lca

dashboard_list=$(curl -s -H "Authorization: Bearer $api_key" "http://$grafana_host:$port/api/search?type=dash-db")

for uid in $(echo "$dashboard_list" | jq -r '.[].uid'); do
curl -H \
     "Authorization: Bearer $api_key" \
     -H "Content-Type: application/json" \
     http://$grafana_host:$port/api/dashboards/uid/$uid \
     -o dashboard_$uid.json
done
