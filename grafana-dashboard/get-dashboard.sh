#!/bin/bash

api_key=$(<api-token)
grafana_host=192.168.1.242
port=3000
dashboard_uid=fdh0b69n4k0lca

dashboard_list=$(curl -s -H "Authorization: Bearer $api_key" "http://$grafana_host:$port/api/search?type=dash-db")

for uid in $(echo "$dashboard_list" | jq -r '.[].uid'); do
    dashboard_json=$(curl -s -H "Authorization: Bearer $api_key" \
                          -H "Content-Type: application/json" \
                          "http://$grafana_host:$port/api/dashboards/uid/$uid")
    dashboard_title=$(echo "$dashboard_json" | jq -r '.dashboard.title')
    safe_title=$(echo "$dashboard_title" | tr -cd '[:alnum:]-_')
    output_file="${safe_title}.json"
    echo "$dashboard_json" > "$output_file"
    echo "Saved dashboard UID: $uid as $output_file"
done
