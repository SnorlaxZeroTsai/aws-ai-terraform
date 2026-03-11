#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================"
echo "Stage 1: Connectivity Tests"
echo "================================"
echo ""

# Get outputs from Terraform
cd ../terraform

echo -e "${YELLOW}Getting Terraform outputs...${NC}"
PUBLIC_IP=$(terraform output -raw ec2_public_ip 2>/dev/null || echo "")
VPC_ID=$(terraform output -raw vpc_id 2>/dev/null || echo "")

if [ -z "$PUBLIC_IP" ]; then
  echo -e "${RED}✗ Failed to get outputs. Run 'terraform apply' first.${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Outputs retrieved${NC}"
echo "  Public IP: $PUBLIC_IP"
echo "  VPC ID: $VPC_ID"
echo ""

# Test 1: Ping
echo -e "${YELLOW}Test 1: Ping (ICMP)${NC}"
if ping -c 3 -W 2 "$PUBLIC_IP" > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Ping successful${NC}"
else
  echo -e "${RED}✗ Ping failed (may be blocked by security group)${NC}"
fi
echo ""

# Test 2: HTTP
echo -e "${YELLOW}Test 2: HTTP Access${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$PUBLIC_IP" --max-time 5 || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
  echo -e "${GREEN}✓ HTTP successful (200)${NC}"
  curl -s "http://$PUBLIC_IP" | head -3
else
  echo -e "${RED}✗ HTTP failed (code: $HTTP_CODE)${NC}"
fi
echo ""

# Test 3: SSH (if key provided)
echo -e "${YELLOW}Test 3: SSH Access${NC}"
if timeout 3 bash -c "cat < /dev/null > /dev/tcp/$PUBLIC_IP/22" 2>/dev/null; then
  echo -e "${GREEN}✓ SSH port is open${NC}"
else
  echo -e "${YELLOW}⚠ SSH port check timed out (may be open but slow)${NC}"
fi
echo ""

# Summary
echo "================================"
echo -e "${GREEN}Connectivity Tests Complete${NC}"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Test SSH access: ssh -i <key.pem> ec2-user@$PUBLIC_IP"
echo "2. Test Session Manager: aws ssm start-session --target <instance-id>"
echo "3. When done, run: terraform destroy"
