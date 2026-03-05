#!/bin/bash
# CVE Scanning Script for IBM ODM Decision MCP Server
# This script provides a convenient wrapper for running CVE scans using Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
RESULTS_DIR="${PROJECT_ROOT}/scan-results"

# Print colored message
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Print usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Run CVE security scans for the Python project using Docker.

OPTIONS:
    -h, --help          Show this help message
    -a, --all           Run all scanners (default)
    -p, --pip-audit     Run pip-audit only
    -s, --safety        Run Safety scan only
    -b, --bandit        Run Bandit SAST only
    -t, --trivy         Run Trivy scan only
    -c, --clean         Clean up scan results directory
    -v, --view          View existing scan results
    --no-cache          Build Docker image without cache

EXAMPLES:
    $0                  # Run all scanners
    $0 --pip-audit      # Run only pip-audit
    $0 --clean          # Clean up results directory
    $0 --view           # View existing results

EOF
}

# Clean up results directory
clean_results() {
    print_message "$YELLOW" "🧹 Cleaning up scan results..."
    if [ -d "$RESULTS_DIR" ]; then
        rm -rf "$RESULTS_DIR"
        print_message "$GREEN" "✅ Scan results directory cleaned"
    else
        print_message "$BLUE" "ℹ️  No scan results directory found"
    fi
}

# View existing results
view_results() {
    if [ ! -d "$RESULTS_DIR" ]; then
        print_message "$RED" "❌ No scan results found. Run a scan first."
        exit 1
    fi

    print_message "$BLUE" "📊 Scan Results Summary:"
    echo ""
    
    for report in "$RESULTS_DIR"/*.json; do
        if [ -f "$report" ]; then
            filename=$(basename "$report")
            size=$(du -h "$report" | cut -f1)
            print_message "$GREEN" "  📄 $filename ($size)"
            
            # Try to show summary if jq is available
            if command -v jq &> /dev/null; then
                case "$filename" in
                    pip-audit-report.json)
                        count=$(jq '. | length' "$report" 2>/dev/null || echo "N/A")
                        print_message "$YELLOW" "     Vulnerabilities found: $count"
                        ;;
                    trivy-report.json)
                        count=$(jq '.Results[].Vulnerabilities | length' "$report" 2>/dev/null || echo "N/A")
                        print_message "$YELLOW" "     Vulnerabilities found: $count"
                        ;;
                esac
            fi
            echo ""
        fi
    done
}

# Create results directory
mkdir -p "$RESULTS_DIR"

# Parse command line arguments
SCANNER="all"
BUILD_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -a|--all)
            SCANNER="all"
            shift
            ;;
        -p|--pip-audit)
            SCANNER="pip-audit"
            shift
            ;;
        -s|--safety)
            SCANNER="safety"
            shift
            ;;
        -b|--bandit)
            SCANNER="bandit"
            shift
            ;;
        -t|--trivy)
            SCANNER="trivy"
            shift
            ;;
        -c|--clean)
            clean_results
            exit 0
            ;;
        -v|--view)
            view_results
            exit 0
            ;;
        --no-cache)
            BUILD_ARGS="--no-cache"
            shift
            ;;
        *)
            print_message "$RED" "❌ Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_message "$RED" "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

print_message "$BLUE" "🔍 Starting CVE Security Scan..."
echo ""

# Build the Docker image
print_message "$YELLOW" "🏗️  Building CVE scanner Docker image..."
cd "${PROJECT_ROOT}"
if docker build $BUILD_ARGS -f scripts/cve/Dockerfile.cve-scan -t python-cve-scanner . > /dev/null 2>&1; then
    print_message "$GREEN" "✅ Docker image built successfully"
else
    print_message "$RED" "❌ Failed to build Docker image"
    exit 1
fi

echo ""

# Run the appropriate scanner
case $SCANNER in
    all)
        print_message "$BLUE" "🔍 Running all security scanners..."
        docker run --rm -v "${RESULTS_DIR}:/app/scan-results" python-cve-scanner
        ;;
    pip-audit)
        print_message "$BLUE" "🔍 Running pip-audit..."
        docker run --rm -v "${RESULTS_DIR}:/app/scan-results" python-cve-scanner \
            bash -c "uv tool run pip-audit --desc --format json --output /app/scan-results/pip-audit-report.json || true && uv tool run pip-audit --desc"
        ;;
    safety)
        print_message "$BLUE" "🔍 Running Safety scan..."
        docker run --rm -v "${RESULTS_DIR}:/app/scan-results" python-cve-scanner \
            bash -c "uv tool run safety scan --output json --save-as /app/scan-results/safety-report.json || true && uv tool run safety scan --detailed"
        ;;
    bandit)
        print_message "$BLUE" "🔍 Running Bandit SAST..."
        docker run --rm -v "${RESULTS_DIR}:/app/scan-results" python-cve-scanner \
            bash -c "uv tool run bandit -r src/ -f json -o /app/scan-results/bandit-report.json || true && uv tool run bandit -r src/"
        ;;
    trivy)
        print_message "$BLUE" "🔍 Running Trivy scan..."
        docker run --rm -v "${RESULTS_DIR}:/app/scan-results" python-cve-scanner \
            bash -c "trivy fs --severity CRITICAL,HIGH,MEDIUM --format json --output /app/scan-results/trivy-report.json . || true && trivy fs --severity CRITICAL,HIGH,MEDIUM ."
        ;;
esac

echo ""
print_message "$GREEN" "✅ CVE scan completed!"
print_message "$BLUE" "📁 Results saved to: $RESULTS_DIR"
echo ""
print_message "$YELLOW" "💡 Tip: Use '$0 --view' to see a summary of results"
print_message "$YELLOW" "💡 Tip: Use '$0 --clean' to remove old scan results"

# Made with Bob
