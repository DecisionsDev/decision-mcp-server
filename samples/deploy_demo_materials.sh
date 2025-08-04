#!/bin/bash
set -euo pipefail

usage() {
  echo "Usage:"
  echo "  $0 basic <DC_API_URL> <DSR_URL> <BASIC_USER> <BASIC_PASSWORD>"
  echo "  $0 zen   <DC_API_URL> <DSR_URL> <USERNAME> <ZEN_API_KEY>"
  echo "  $0 oidc  <DC_API_URL> <DSR_URL> <CLIENT_ID> <CLIENT_SECRET> <OPENID_TOKEN_URL>"
  exit 1
}

# Check arguments
if [[ "$#" -lt 5 ]]; then usage; fi

AUTH_MODE="$1"
DC_API_URL="$2"
DSR_URL="$3"

case "$AUTH_MODE" in
  basic)
    if [[ "$#" -ne 5 ]]; then usage; fi
    BASIC_USER="$4"
    BASIC_PASSWORD="$5"
    AUTH_CREDENTIALS=(--user "${BASIC_USER}:${BASIC_PASSWORD}")
    ;;
  zen)
    if [[ "$#" -ne 5 ]]; then usage; fi
    USERNAME="$4"
    ZEN_API_KEY="$5"
    BASE64ENCODED_USERNAME_AND_APIKEY=$(echo -n "${USERNAME}:${ZEN_API_KEY}" | base64)
    AUTH_CREDENTIALS=(-H "Authorization: ZenApiKey ${BASE64ENCODED_USERNAME_AND_APIKEY}")
    ;;
  oidc)
    if [[ "$#" -ne 6 ]]; then usage; fi
    CLIENT_ID="$4"
    CLIENT_SECRET="$5"
    OPENID_TOKEN_URL="$6"
    ACCESS_TOKEN=$(curl -sk -X POST -H "Content-Type: application/x-www-form-urlencoded" \
      -d "client_id=${CLIENT_ID}&scope=openid&client_secret=${CLIENT_SECRET}&grant_type=client_credentials" \
      "${OPENID_TOKEN_URL}" | jq -r '.access_token')
    AUTH_CREDENTIALS=(-H "Authorization: Bearer ${ACCESS_TOKEN}")
    ;;
  *)
    echo "Invalid authentication mode: $AUTH_MODE"
    usage
    ;;
esac

# ----------------------------------
# Function to import, deploy, and execute a Decision Service
# ----------------------------------
import_and_deploy_decision_service() {
  local DS_NAME="$1"
  local DEPLOYMENT_NAME_URLENCODED="$2"
  local DS_FILENAME="$3"
  local DEPLOYMENT_NAME="Decision Service Execution"

  local DS_NAME_URLENCODED="${DS_NAME// /%20}"

  echo "🔽 Downloading archive for '${DS_NAME}'..."
#  curl -sL -o "${DS_FILENAME}" "https://github.com/DecisionsDev/odm-for-dev-getting-started/blob/master/${DS_FILENAME_URLENCODED}?raw=1"

  echo "📤 Importing '${DS_NAME}' into Decision Center..."
  curl -sk -X POST "${AUTH_CREDENTIALS[@]}" \
    -H "accept: application/json" \
    -H "Content-Type: multipart/form-data" \
    --form "file=@${DS_FILENAME};type=application/zip" \
    "${DC_API_URL}/v1/decisionservices/import"

  echo "🔍 Retrieving service ID..."
  local GET_DECISIONSERVICE_RESULT=$(curl -sk -X GET "${AUTH_CREDENTIALS[@]}" -H "accept: application/json" \
    "${DC_API_URL}/v1/decisionservices?q=name%3A${DS_NAME_URLENCODED}")
  local DECISIONSERVICEID=$(echo "${GET_DECISIONSERVICE_RESULT}" | jq -r '.elements[0].id')

  echo "🔍 Retrieving deployment config ID..."
  local GET_DEPLOYMENT_RESULT=$(curl -sk -X GET "${AUTH_CREDENTIALS[@]}" -H "accept: application/json" \
    "${DC_API_URL}/v1/decisionservices/${DECISIONSERVICEID}/deployments?q=name%3A${DEPLOYMENT_NAME_URLENCODED}")
  local DEPLOYMENTCONFIGURATIONID=$(echo "${GET_DEPLOYMENT_RESULT}" | jq -r '.elements[0].id')

  echo "🚀 Deploying '${DS_NAME}'..."
  curl -sk -X POST "${AUTH_CREDENTIALS[@]}" -H "accept: application/json" \
    "${DC_API_URL}/v1/deployments/${DEPLOYMENTCONFIGURATIONID}/deploy" | jq
}

# ----------------------------------
# Call function for multiple services
# ----------------------------------

# You can repeat the line below for other decision services
import_and_deploy_decision_service "targeted_advertising" "deployment" "advertising_project.zip"
import_and_deploy_decision_service "hr_decision_service" "deployment" "vacation_project.zip" 