# Step Functions Module for Agent Workflow

data "aws_iam_policy_document" "step_functions_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# IAM Role for Step Functions
resource "aws_iam_role" "step_functions_role" {
  name               = "${var.project_name}-stepfunctions-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.step_functions_assume_role.json

  tags = var.tags
}

# IAM Policy for Lambda invocation
resource "aws_iam_role_policy" "step_functions_lambda" {
  name = "${var.project_name}-lambda-invocation-${var.environment}"
  role = aws_iam_role.step_functions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          var.agent_core_lambda_arn,
          var.tool_executor_arn,
          var.reasoning_engine_arn
        ]
      }
    ]
  })
}

# Step Functions State Machine
resource "aws_sfn_state_machine" "agent_workflow" {
  name     = "${var.project_name}-agent-workflow-${var.environment}"
  role_arn = aws_iam_role.step_functions_role.arn

  definition = jsonencode({
    Comment = "Autonomous Agent ReAct Workflow"
    StartAt = "InitializeAgent"
    Version = "1.0"

    States = {
      InitializeAgent = {
        Type = "Task"
        Resource = var.agent_core_lambda_arn
        Next = "Reason"
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            ResultPath = "$.error"
            Next = "HandleError"
          }
        ]
        Retry = [
          {
            ErrorEquals = ["States.TaskFailed"]
            IntervalSeconds = 2
            MaxAttempts = 3
            BackoffRate = 2.0
          }
        ]
      }

      Reason = {
        Type = "Task"
        Resource = var.reasoning_engine_arn
        Next = "CheckIteration"
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            ResultPath = "$.error"
            Next = "HandleError"
          }
        ]
      }

      CheckIteration = {
        Type = "Choice"
        Choices = [
          {
            Variable = "$.iteration"
            NumericLessThan = var.max_iterations
            Next = "DecideAction"
          }
        ]
        Default = "Finalize"
      }

      DecideAction = {
        Type = "Choice"
        Choices = [
          {
            Variable = "$.action.type"
            StringEquals = "tool"
            Next = "ExecuteTool"
          },
          {
            Variable = "$.action.type"
            StringEquals = "respond"
            Next = "Finalize"
          }
        ]
        Default = "Reason"
      }

      ExecuteTool = {
        Type = "Task"
        Resource = var.tool_executor_arn
        Next = "StoreMemory"
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            ResultPath = "$.error"
            Next = "HandleError"
          }
        ]
        Retry = [
          {
            ErrorEquals = ["States.TaskFailed"]
            IntervalSeconds = 1
            MaxAttempts = 2
            BackoffRate = 2.0
          }
        ]
      }

      StoreMemory = {
        Type = "Task"
        Resource = var.agent_core_lambda_arn
        Next = "Reason"
        Parameters = {
          "action.$" = "$"
          "operation" = "store_memory"
        }
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            ResultPath = "$.error"
            Next = "HandleError"
          }
        ]
      }

      Finalize = {
        Type = "Task"
        Resource = var.agent_core_lambda_arn
        End = true
        Parameters = {
          "action.$" = "$"
          "operation" = "finalize"
        }
      }

      HandleError = {
        Type = "Task"
        Resource = var.agent_core_lambda_arn
        End = true
        Parameters = {
          "action.$" = "$"
          "operation" = "handle_error"
        }
      }
    }
  })

  tags = var.tags
}

# CloudWatch Log Group for Step Functions
resource "aws_cloudwatch_log_group" "step_functions_logs" {
  name              = "/aws/vendedlogs/states/${var.project_name}-agent-workflow-${var.environment}"
  retention_in_days = 7

  tags = var.tags
}
