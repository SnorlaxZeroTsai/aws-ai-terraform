#!/bin/bash
set -euxo pipefail

# Update system
yum update -y || apt-get update -y

# Install AWS CLI (for testing)
if command -v yum &> /dev/null; then
  yum install -y aws-cli
else
  apt-get install -y awscli
fi

# Create a simple test file
echo "Terraform Foundation Test Instance" > /tmp/test.txt
echo "Timestamp: $(date)" >> /tmp/test.txt

# Install a simple web server for testing
if command -v yum &> /dev/null; then
  yum install -y python3
else
  apt-get install -y python3
fi

echo "<h1>Stage 1: Terraform Foundation</h1>" > /tmp/index.html
echo "<p>This is a test instance deployed via Terraform</p>" >> /tmp/index.html
echo "<p>Private IP: $(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)</p>" >> /tmp/index.html

# Start simple Python HTTP server
cd /tmp
nohup python3 -m http.server 80 > /dev/null 2>&1 &
