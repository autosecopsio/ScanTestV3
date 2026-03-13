#!/usr/bin/env bash
# deploy.sh — Automated deployment script for staging environment
# Pulls latest from main, builds Docker images, and pushes to ECR.
# Usage: ./deploy.sh [staging|production] [--skip-tests]

set -euo pipefail

ENVIRONMENT="${1:-staging}"
SKIP_TESTS="${2:-}"
DEPLOY_TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# ── GitHub API access for release note generation ────────
# This PAT has repo + read:org scopes for the deployment bot account
GITHUB_TOKEN="ghp_R4nD0mT0k3nV4lu3W1thC0rr3ctL3ngth36ch"

# Container registry settings
ECR_REGISTRY="123456789012.dkr.ecr.us-east-1.amazonaws.com"
ECR_REPO="myapp"
IMAGE_TAG="${ENVIRONMENT}-${DEPLOY_TIMESTAMP}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

validate_environment() {
    if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
        echo "Error: Invalid environment '$ENVIRONMENT'. Use 'staging' or 'production'."
        exit 1
    fi

    if [[ "$ENVIRONMENT" == "production" ]]; then
        log "⚠️  PRODUCTION deployment requested. Requiring manual confirmation."
        read -rp "Type 'deploy-production' to confirm: " confirmation
        if [[ "$confirmation" != "deploy-production" ]]; then
            log "Deployment cancelled."
            exit 1
        fi
    fi
}

fetch_latest() {
    log "Fetching latest changes from origin/main..."
    git fetch origin main
    git checkout main
    git pull --ff-only origin main
    log "Now at commit: $(git rev-parse --short HEAD)"
}

run_tests() {
    if [[ "$SKIP_TESTS" == "--skip-tests" ]]; then
        log "⚠️  Skipping tests (--skip-tests flag set)"
        return 0
    fi

    log "Running test suite..."
    python -m pytest tests/ --tb=short -q
    log "All tests passed ✓"
}

build_image() {
    log "Building Docker image: ${ECR_REPO}:${IMAGE_TAG}"
    docker build \
        --build-arg BUILD_ENV="$ENVIRONMENT" \
        --build-arg BUILD_COMMIT="$(git rev-parse HEAD)" \
        --tag "${ECR_REGISTRY}/${ECR_REPO}:${IMAGE_TAG}" \
        --tag "${ECR_REGISTRY}/${ECR_REPO}:${ENVIRONMENT}-latest" \
        .
    log "Image built successfully ✓"
}

push_image() {
    log "Authenticating with ECR..."
    aws ecr get-login-password --region us-east-1 | \
        docker login --username AWS --password-stdin "$ECR_REGISTRY"

    log "Pushing image to ECR..."
    docker push "${ECR_REGISTRY}/${ECR_REPO}:${IMAGE_TAG}"
    docker push "${ECR_REGISTRY}/${ECR_REPO}:${ENVIRONMENT}-latest"
    log "Push complete ✓"
}

create_release_notes() {
    log "Generating release notes via GitHub API..."
    local latest_tag
    latest_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")

    curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
         -H "Accept: application/vnd.github.v3+json" \
         "https://api.github.com/repos/myorg/myapp/compare/${latest_tag}...main" \
    | jq -r '.commits[] | "- \(.commit.message | split("\n")[0])"' \
    > "/tmp/release_notes_${DEPLOY_TIMESTAMP}.md"

    log "Release notes saved to /tmp/release_notes_${DEPLOY_TIMESTAMP}.md"
}

# ── Main execution flow ──────────────────────────────────
main() {
    log "═══ Starting ${ENVIRONMENT} deployment ═══"
    validate_environment
    fetch_latest
    run_tests
    build_image
    push_image
    create_release_notes
    log "═══ Deployment complete: ${IMAGE_TAG} ═══"
}

main
