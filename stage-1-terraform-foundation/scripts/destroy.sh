#!/bin/bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}========================================"
echo "WARNING: This will destroy ALL resources"
echo "========================================${NC}"
echo ""
echo -e "${YELLOW}Resources to be destroyed:${NC}"
cd ../terraform

# Check if terraform is initialized
if [ ! -d ".terraform" ]; then
    echo "Error: Terraform is not initialized."
    echo "Please run 'terraform init' first."
    exit 1
fi

# Check if terraform state exists
if ! terraform state list &> /dev/null; then
    echo "Error: No terraform state found."
    echo "Please ensure terraform is properly initialized and state exists."
    exit 1
fi

# Check if terraform plan succeeds
if ! terraform plan -destroy; then
    echo "Error: Terraform plan failed. Please review the errors above."
    exit 1
fi

echo ""
read -p "Are you sure you want to proceed? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
  echo "Aborted."
  exit 1
fi

echo ""
echo "Destroying resources..."
terraform destroy -auto-approve

echo ""
echo -e "${GREEN}✓ Resources destroyed${NC}"
echo ""
echo "Note: NAT Gateway and Elastic IP are fully released"
echo "Terraform state file has been updated"
