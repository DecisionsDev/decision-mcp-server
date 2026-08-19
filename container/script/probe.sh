#!/usr/bin/env bash
__dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

export CURL_OPTS="-s -o /dev/null -w %{http_code}"
RESPONSE_HTTP_CODE=$(${__dir}/server_discover.sh)

if [[ "${RESPONSE_HTTP_CODE}" == "200" ]]; then
    exit 0
else
    exit 1
fi