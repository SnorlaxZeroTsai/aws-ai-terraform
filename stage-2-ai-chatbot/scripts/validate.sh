#!/bin/bash
# Validation script for Stage 2 AI Chatbot Service

set -e

echo "========================================="
echo "Stage 2: AI Chatbot Service Validation"
echo "========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "terraform/main.tf" ]; then
    echo "Error: Please run this script from the stage-2-ai-chatbot directory"
    exit 1
fi

echo "1. Checking file structure..."
required_files=(
    "terraform/main.tf"
    "terraform/variables.tf"
    "terraform/outputs.tf"
    "terraform/provider.tf"
    "terraform/modules/lambda/main.tf"
    "terraform/modules/api_gateway/main.tf"
    "terraform/modules/secrets_manager/main.tf"
    "terraform/modules/cloudwatch/main.tf"
    "src/handlers/chat.py"
    "src/services/llm_service.py"
    "src/prompts/chat_templates.py"
    "src/utils/response.py"
    "tests/api_tests.py"
    "README.md"
    "docs/design.md"
    "docs/ARCHITECTURE.md"
    "requirements.txt"
    ".gitignore"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "❌ Missing files:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    exit 1
else
    echo "✅ All required files present"
fi

echo ""
echo "2. Checking Python syntax..."
if command -v python3 &> /dev/null; then
    python_files=(
        "src/handlers/chat.py"
        "src/services/llm_service.py"
        "src/prompts/chat_templates.py"
        "src/utils/response.py"
        "tests/api_tests.py"
    )

    for file in "${python_files[@]}"; do
        if python3 -m py_compile "$file" 2>/dev/null; then
            echo "✅ $file - syntax OK"
        else
            echo "❌ $file - syntax error"
            exit 1
        fi
    done
else
    echo "⚠️  Python3 not found, skipping syntax check"
fi

echo ""
echo "3. Checking Terraform format (if available)..."
if command -v terraform &> /dev/null; then
    cd terraform
    if terraform fmt -check -recursive &> /dev/null; then
        echo "✅ Terraform files are formatted correctly"
    else
        echo "⚠️  Terraform files need formatting. Run: terraform fmt -recursive"
    fi
    cd ..
else
    echo "⚠️  Terraform not found, skipping format check"
fi

echo ""
echo "4. Checking for sensitive data in git..."
if [ -d ".git" ]; then
    if grep -r "SECRET\|PASSWORD\|API_KEY" --include="*.tf" --include="*.py" . 2>/dev/null | grep -v "SECRET_ARN\|secret_name\|# Example" | grep -q .; then
        echo "⚠️  Warning: Possible hardcoded secrets detected"
        echo "   Please ensure all secrets are in terraform.tfvars (not committed)"
    else
        echo "✅ No hardcoded secrets detected"
    fi
else
    echo "⚠️  Not a git repository, skipping secret check"
fi

echo ""
echo "5. Validating file structure..."
total_files=$(find . -type f \( -name "*.tf" -o -name "*.py" -o -name "*.md" \) | wc -l)
echo "   Total Terraform files: $(find . -name "*.tf" | wc -l)"
echo "   Total Python files: $(find . -name "*.py" | wc -l)"
echo "   Total Markdown files: $(find . -name "*.md" | wc -l)"
echo "   Total project files: $total_files"

echo ""
echo "========================================="
echo "Validation Summary"
echo "========================================="
echo "✅ Stage 2 structure is complete!"
echo ""
echo "Next steps:"
echo "1. cd terraform"
echo "2. cp terraform.tfvars.template terraform.tfvars"
echo "3. Edit terraform.tfvars with your configuration"
echo "4. terraform init"
echo "5. terraform plan"
echo "6. terraform apply"
echo ""
echo "For testing:"
echo "1. pip install -r ../requirements.txt"
echo "2. export CHAT_API_ENDPOINT=\$(terraform output chat_endpoint_url)"
echo "3. pytest ../tests/api_tests.py"
echo ""
