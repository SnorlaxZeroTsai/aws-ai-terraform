# Get VPC and subnet information from Stage 1
data "aws_vpc" "main" {
  count = var.create_vpc_resources ? 0 : 1
  id    = var.vpc_id
}

data "aws_subnets" "private" {
  count = var.create_vpc_resources ? 0 : 1
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }

  tags = {
    Name = "*private*"
  }
}

# Create ECR Repository
resource "aws_ecr_repository" "orchestrator" {
  name                 = var.repository_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${var.platform_name}-ecr"
    }
  )
}

resource "aws_ecr_lifecycle_policy" "orchestrator" {
  repository = aws_ecr_repository.orchestrator.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Delete untagged images older than 1 day"
        selection = {
          tagStatus      = "untagged"
          countType      = "sinceImagePushed"
          countUnit      = "days"
          countNumber    = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# Create ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.platform_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${var.platform_name}-cluster"
    }
  )
}

# Create CloudWatch log group for ECS
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.platform_name}"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

# Create Security Group for ECS tasks
resource "aws_security_group" "ecs_tasks" {
  name_prefix = "${var.platform_name}-ecs-"
  description = "Security group for ECS tasks"
  vpc_id      = var.create_vpc_resources ? aws_vpc.main[0].id : var.vpc_id

  ingress {
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = var.load_balancer_security_groups
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${var.platform_name}-ecs-tasks"
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Create IAM role for ECS tasks
resource "aws_iam_role" "ecs_execution" {
  name = "${var.platform_name}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy_attachment" "ecs_xray" {
  count      = var.enable_xray ? 1 : 0
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# Create IAM role for ECS task
resource "aws_iam_role" "ecs_task" {
  name = "${var.platform_name}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Policy for ECS task to invoke Lambda functions
resource "aws_iam_role_policy" "ecs_task_invoke_lambda" {
  name = "${var.platform_name}-invoke-lambda"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = var.lambda_function_arns
      },
      {
        Effect = "Allow"
        Action = [
          "states:StartExecution"
        ]
        Resource = var.step_function_arns
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = var.dynamodb_table_arns
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = var.s3_bucket_arns
      }
    ]
  })
}

# Create ECS Task Definition
resource "aws_ecs_task_definition" "orchestrator" {
  family                   = "${var.platform_name}-orchestrator"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "orchestrator"
      image     = "${aws_ecr_repository.orchestrator.repository_url}:${var.image_tag}"
      cpu       = var.task_cpu
      memory    = var.task_memory
      essential = true

      portMappings = [
        {
          containerPort = var.container_port
          protocol      = "tcp"
        }
      ]

      environment = concat(
        [
          {
            name  = "PLATFORM_NAME"
            value = var.platform_name
          },
          {
            name  = "ENVIRONMENT"
            value = var.environment
          },
          {
            name  = "AWS_REGION"
            value = var.aws_region
          },
          {
            name  = "CONTAINER_PORT"
            value = tostring(var.container_port)
          }
        ],
        var.environment_variables
      )

      secrets = var.container_secrets

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "orchestrator"
          "awslogs-create-group"  = "true"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.container_port}/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      dockerLabels = {
        "com.amazonaws.ecs.task-architecture" = "linux/x86_64"
      }
    }
  ])

  tags = local.common_tags

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
}

# Create ECS Service
resource "aws_ecs_service" "main" {
  name            = "${var.platform_name}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.orchestrator.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.create_vpc_resources ? aws_subnet.private[*].id : var.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "orchestrator"
    container_port   = var.container_port
  }

  enable_execute_command = true

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 50
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }

  # Enable X-Ray tracing
  enable_ecs_managed_tags = true
  propagate_tags         = "SERVICE"

  tags = merge(
    local.common_tags,
    {
      Name = "${var.platform_name}-service"
    }
  )

  depends_on = [aws_iam_role_policy_attachment.ecs_execution]

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }
}

# Create Auto Scaling Target
resource "aws_appautoscaling_target" "ecs" {
  count           = var.enable_auto_scaling ? 1 : 0
  max_capacity    = var.max_capacity
  min_capacity    = var.min_capacity
  resource_id     = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.main.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  tags = local.common_tags
}

# Create Auto Scaling Policy
resource "aws_appautoscaling_policy" "ecs_cpu" {
  count              = var.enable_auto_scaling ? 1 : 0
  name               = "${var.platform_name}-cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ecs:Service:CPUUtilization:Average"
    }
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

resource "aws_appautoscaling_policy" "ecs_memory" {
  count              = var.enable_auto_scaling ? 1 : 0
  name               = "${var.platform_name}-memory-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ecs:Service:MemoryUtilization:Average"
    }
    target_value       = 80.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# CloudWatch Alarms for Auto Scaling
resource "aws_cloudwatch_metric_alarm" "ecs_cpu_high" {
  count              = var.enable_auto_scaling ? 1 : 0
  alarm_name          = "${var.platform_name}-cpu-high"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "70"
  alarm_description   = "This metric monitors ECS CPU utilization"
  alarm_actions       = var.enable_alarm_actions ? [aws_sns_topic.alarms[0].arn] : []

  dimensions = {
    ServiceName = aws_ecs_service.main.name
    ClusterName = aws_ecs_cluster.main.name
  }

  tags = local.common_tags
}

# Create SNS topic for alarms
resource "aws_sns_topic" "alarms" {
  count = var.enable_alarms ? 1 : 0
  name   = "${var.platform_name}-alarms"

  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "alarm_email" {
  count     = var.enable_alarms && var.alarm_email != null ? 1 : 0
  topic_arn = aws_sns_topic.alarms[0].arn
  protocol  = "email"
  endpoint  = var.alarm_email
}
