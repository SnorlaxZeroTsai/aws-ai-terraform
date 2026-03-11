#!/bin/bash
set -euo pipefail

# Check for required dependencies
if ! command -v bc &> /dev/null; then
    echo "Error: 'bc' command is required but not installed."
    echo "Please install bc to run this script."
    echo "  - Ubuntu/Debian: sudo apt-get install bc"
    echo "  - macOS: brew install bc"
    echo "  - RHEL/CentOS: sudo yum install bc"
    exit 1
fi

echo "=================================="
echo "Stage 1: Cost Estimate"
echo "=================================="
echo ""

# Pricing (us-east-1, on-demand)
NAT_HOURLY=0.045
NAT_MONTHLY=$(echo "$NAT_HOURLY * 730" | bc)
EC2_HOURLY=0.0104
EC2_MONTHLY=$(echo "$EC2_HOURLY * 730" | bc)

echo "Assumptions:"
echo "- Region: us-east-1"
echo "- NAT Gateway: Always on"
echo "- EC2 t3.micro: 24/7 operation"
echo "- No data transfer included"
echo ""

echo "Resource Breakdown:"
printf "%-20s %10s %10s\n" "Resource" "Hourly" "Monthly"
printf "%-20s %10s %10s\n" "--------" "------" "-------"
printf "%-20s %10s %10s\n" "NAT Gateway" "\$$NAT_HOURLY" "\$$NAT_MONTHLY"
printf "%-20s %10s %10s\n" "EC2 t3.micro" "\$$EC2_HOURLY" "\$$EC2_MONTHLY"
echo ""

TOTAL=$(echo "$NAT_MONTHLY + $EC2_MONTHLY" | bc)
echo "Estimated Monthly Total: ~$${TOTAL}"
echo ""

echo "Cost Optimization Tips:"
echo "1. Stop EC2 when not in use"
echo "2. Use NAT instance for development (saves ~\$20/month)"
echo "3. Monitor with AWS Cost Explorer"
echo "4. Set up billing alerts"
echo ""

echo "Free Tier Eligibility:"
echo "- EC2: Yes (750 hours/month of t2/t3.micro)"
echo "- NAT Gateway: No (not covered)"
echo ""
