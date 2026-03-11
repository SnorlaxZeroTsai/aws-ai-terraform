# S3 Module for Tool Definitions

resource "aws_s3_bucket" "tool_definitions" {
  bucket = var.bucket_name

  tags = var.tags
}

resource "aws_s3_bucket_versioning" "tool_definitions" {
  bucket = aws_s3_bucket.tool_definitions.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tool_definitions" {
  bucket = aws_s3_bucket.tool_definitions.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tool_definitions" {
  bucket = aws_s3_bucket.tool_definitions.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Sample tool definition
resource "aws_s3_object" "sample_tool" {
  bucket = aws_s3_bucket.tool_definitions.id
  key    = "tools/search_tool.json"
  content = jsonencode({
    name        = "web_search"
    description = "Search the web for current information"
    parameters = {
      type = "object"
      properties = {
        query = {
          type        = "string"
          description = "Search query"
        }
      }
      required = ["query"]
    }
  })

  tags = var.tags
}
