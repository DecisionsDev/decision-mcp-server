#!/usr/bin/env bash
CURL_OPTS='-s -o /dev/null -w "%{http_code}\n" | grep -q "200"' server_discover.sh