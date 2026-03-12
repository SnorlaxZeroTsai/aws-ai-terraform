#!/bin/bash
# Deployment script for AI Agent Platform (Stage 6)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"
DOCKER_DIR="$PROJECT_ROOT/docker"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed"
        exit 1
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed"
        exit 1
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi

    log_info "All prerequisites met"
}

build_docker_image() {
    log_info "Building Docker image..."

    cd "$DOCKER_DIR"

    # Build image
    docker build -t ai-agent-orchestrator:latest .

    log_info "Docker image built successfully"
}

push_to_ecr() {
    log_info "Pushing Docker image to ECR..."

    # Get AWS account ID and region
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=${AWS_REGION:-us-east-1}

    # Login to ECR
    log_info "Logging in to ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin \
        "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

    # Create repository if it doesn't exist
    REPO_NAME="ai-agent-orchestrator"
    REPO_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}"

    if ! aws ecr describe-repositories --repository-names "$REPO_NAME" --region "$AWS_REGION" &> /dev/null; then
        log_info "Creating ECR repository..."
        aws ecr create-repository --repository-name "$REPO_NAME" --region "$AWS_REGION"
    fi

    # Tag and push image
    log_info "Tagging and pushing image..."
    docker tag ai-agent-orchestrator:latest "$REPO_URL:latest"
    docker push "$REPO_URL:latest"

    log_info "Image pushed to ECR: $REPO_URL:latest"
}

deploy_infrastructure() {
    log_info "Deploying infrastructure with Terraform..."

    cd "$TERRAFORM_DIR"

    # Initialize Terraform
    log_info "Initializing Terraform..."
    terraform init

    # Validate configuration
    log_info "Validating Terraform configuration..."
    terraform validate

    # Plan deployment
    log_info "Planning Terraform deployment..."
    terraform plan -out=tfplan

    # Ask for confirmation
    read -p "Apply Terraform plan? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Apply changes
        log_info "Applying Terraform changes..."
        terraform apply tfplan

        # Get outputs
        log_info "Deployment outputs:"
        terraform output -json
    else
        log_warn "Deployment cancelled"
        exit 0
    fi
}

verify_deployment() {
    log_info "Verifying deployment..."

    cd "$TERRAFORM_DIR"

    # Get API endpoint
    API_ENDPOINT=$(terraform output -raw api_gateway_invoke_url)

    log_info "Testing health endpoint..."
    if curl -f -s "$API_ENDPOINT/health" | grep -q "healthy"; then
        log_info "Health check passed"
    else
        log_error "Health check failed"
        exit 1
    fi

    log_info "Deployment verification complete"
}

cleanup() {
    log_info "Cleaning up temporary files..."
    rm -f "$TERRAFORM_DIR/tfplan"
    log_info "Cleanup complete"
}

main() {
    log_info "Starting deployment of AI Agent Platform (Stage 6)"
    log_info "================================================"

    # Parse command line arguments
    SKIP_BUILD=false
    SKIP_PUSH=false
    SKIP_DEPLOY=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-push)
                SKIP_PUSH=true
                shift
                ;;
            --skip-deploy)
                SKIP_DEPLOY=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Execute deployment steps
    check_prerequisites

    if [ "$SKIP_BUILD" = false ]; then
        build_docker_image
    else
        log_info "Skipping Docker build"
    fi

    if [ "$SKIP_PUSH" = false ]; then
        push_to_ecr
    else
        log_info "Skipping ECR push"
    fi

    if [ "$SKIP_DEPLOY" = false ]; then
        deploy_infrastructure
        verify_deployment
    else
        log_info "Skipping infrastructure deployment"
    fi

    cleanup

    log_info "================================================"
    log_info "Deployment completed successfully!"
    log_info ""
    log_info "Next steps:"
    log_info "1. Test the API endpoints"
    log_info "2. Monitor CloudWatch dashboards"
    log_info "3. Check X-Ray traces for performance"
}

# Trap errors
trap 'log_error "Deployment failed at line $LINENO"' ERR

# Run main function
main "$@"
