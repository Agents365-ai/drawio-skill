resource "aws_api_gateway_rest_api" "api" {
  name = "orders-api"
}

resource "aws_lambda_function" "orders" {
  function_name = "orders-handler"
  role          = aws_iam_role.lambda.arn
  environment {
    variables = {
      TABLE  = aws_dynamodb_table.orders.name
      QUEUE  = aws_sqs_queue.jobs.url  # async work
      BUCKET = aws_s3_bucket.uploads.id
    }
  }
}

resource "aws_lambda_function" "worker" {
  function_name = "jobs-worker"
  role          = aws_iam_role.lambda.arn
  environment {
    variables = {
      TABLE = aws_dynamodb_table.orders.name
    }
  }
}

resource "aws_lambda_event_source_mapping" "worker_trigger" {
  event_source_arn = aws_sqs_queue.jobs.arn
  function_name    = aws_lambda_function.worker.arn
}

resource "aws_iam_role" "lambda" {
  name = "lambda-exec"
}

resource "aws_dynamodb_table" "orders" {
  name = "orders"
}

resource "aws_sqs_queue" "jobs" {
  name = "jobs"
}

resource "aws_s3_bucket" "uploads" {
  bucket = "orders-uploads"
}

resource "aws_cloudfront_distribution" "cdn" {
  origin {
    domain_name = aws_s3_bucket.uploads.bucket_regional_domain_name
  }
}

resource "aws_api_gateway_integration" "lambda_proxy" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  uri         = aws_lambda_function.orders.invoke_arn
}
