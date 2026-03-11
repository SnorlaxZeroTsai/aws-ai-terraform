#!/usr/bin/env python3
"""
Quick validation script to check Stage 4 implementation
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: {filepath} (MISSING)")
        return False

def check_directory_structure():
    """Validate directory structure"""
    print("\n=== Checking Directory Structure ===")

    required_dirs = [
        "terraform",
        "terraform/modules/opensearch",
        "terraform/modules/lambda",
        "terraform/modules/s3",
        "terraform/modules/bedrock",
        "src/handlers",
        "src/services",
        "src/chunking",
        "src/prompts",
        "src/utils",
        "tests",
        "docs",
        "data/sample_documents"
    ]

    all_exist = True
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"✓ Directory: {dir_path}")
        else:
            print(f"✗ Directory: {dir_path} (MISSING)")
            all_exist = False

    return all_exist

def check_terraform_files():
    """Check Terraform files"""
    print("\n=== Checking Terraform Files ===")

    terraform_files = [
        ("terraform/main.tf", "Main Terraform configuration"),
        ("terraform/variables.tf", "Terraform variables"),
        ("terraform/outputs.tf", "Terraform outputs"),
        ("terraform/provider.tf", "Terraform provider"),
        ("terraform/terraform.tfvars.template", "Terraform variables template"),
        ("terraform/modules/opensearch/main.tf", "OpenSearch module"),
        ("terraform/modules/lambda/main.tf", "Lambda module"),
        ("terraform/modules/s3/main.tf", "S3 module"),
        ("terraform/modules/bedrock/main.tf", "Bedrock module"),
    ]

    all_exist = True
    for filepath, description in terraform_files:
        if not check_file_exists(filepath, description):
            all_exist = False

    return all_exist

def check_python_files():
    """Check Python source files"""
    print("\n=== Checking Python Source Files ===")

    python_files = [
        ("src/services/embedding_service.py", "Embedding service"),
        ("src/services/opensearch_service.py", "OpenSearch service"),
        ("src/services/rag_service.py", "RAG orchestration service"),
        ("src/chunking/strategies.py", "Chunking strategies"),
        ("src/chunking/evaluation.py", "Chunk evaluation"),
        ("src/prompts/rag_templates.py", "RAG prompt templates"),
        ("src/handlers/index_handler.py", "Index Lambda handler"),
        ("src/handlers/search_handler.py", "Search Lambda handler"),
        ("tests/chunking_test.py", "Chunking tests"),
        ("tests/rag_test.py", "RAG tests"),
    ]

    all_exist = True
    for filepath, description in python_files:
        if not check_file_exists(filepath, description):
            all_exist = False

    return all_exist

def check_documentation():
    """Check documentation files"""
    print("\n=== Checking Documentation ===")

    doc_files = [
        ("README.md", "Main README"),
        ("docs/design.md", "Design document"),
        ("docs/ARCHITECTURE.md", "Technical architecture"),
        ("requirements.txt", "Python dependencies"),
        (".gitignore", "Git ignore rules"),
    ]

    all_exist = True
    for filepath, description in doc_files:
        if not check_file_exists(filepath, description):
            all_exist = False

    return all_exist

def check_sample_data():
    """Check sample documents"""
    print("\n=== Checking Sample Data ===")

    sample_files = [
        ("data/sample_documents/machine_learning.txt", "ML sample document"),
        ("data/sample_documents/docker_basics.txt", "Docker sample document"),
        ("data/sample_documents/kubernetes_overview.txt", "Kubernetes sample document"),
    ]

    all_exist = True
    for filepath, description in sample_files:
        if not check_file_exists(filepath, description):
            all_exist = False

    return all_exist

def main():
    """Run all validation checks"""
    print("=" * 60)
    print("Stage 4: RAG Knowledge Base - Validation")
    print("=" * 60)

    results = {
        "directories": check_directory_structure(),
        "terraform": check_terraform_files(),
        "python": check_python_files(),
        "documentation": check_documentation(),
        "sample_data": check_sample_data(),
    }

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    all_passed = True
    for category, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{category.capitalize()}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ All validation checks passed!")
        print("\nNext steps:")
        print("1. Review terraform/terraform.tfvars.template and create terraform.tfvars")
        print("2. Run 'cd terraform && terraform init'")
        print("3. Run 'cd terraform && terraform plan'")
        print("4. Run 'cd terraform && terraform apply'")
        print("5. Test by uploading documents to S3")
        print("6. Query the API Gateway endpoint")
        return 0
    else:
        print("\n✗ Some validation checks failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
