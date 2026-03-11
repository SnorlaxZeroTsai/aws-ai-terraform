# S3 Module for Document Storage
module "s3" {
  source = "./modules/s3"

  bucket_name       = "stage3-documents-${var.environment}"
  enable_versioning = true
  tags = {
    Purpose = "document-upload"
  }
}

# DynamoDB Module for Document Metadata
module "dynamodb" {
  source = "./modules/dynamodb"

  table_name = "stage3-document-metadata-${var.environment}"
  tags = {
    Purpose = "document-metadata"
  }
}

# SNS/SQS Module for Async Processing
module "sns_sqs" {
  source = "./modules/sns_sqs"

  enabled           = var.enable_async_processing
  queue_name        = "stage3-document-processing-${var.environment}"
  topic_name        = "stage3-document-notifications-${var.environment}"
  notification_email = var.notification_email

  tags = {
    Purpose = "async-processing"
  }
}

# Lambda Module for Document Processing
module "lambda" {
  source = "./modules/lambda"

  upload_function_name = "stage3-upload-handler-${var.environment}"
  analysis_function_name = "stage3-analysis-handler-${var.environment}"

  s3_bucket_arn     = module.s3.bucket_arn
  s3_bucket_name    = module.s3.bucket_name
  dynamodb_table_arn = module.dynamodb.table_arn
  dynamodb_table_name = module.dynamodb.table_name
  sqs_queue_arn     = module.sns_sqs.queue_arn
  sqs_queue_url     = module.sns_sqs.queue_url
  sns_topic_arn     = module.sns_sqs.topic_arn

  textract_features = var.textract_features

  tags = {
    Purpose = "document-processing"
  }

  depends_on = [module.s3, module.dynamodb, module.sns_sqs]
}
