resource "aws_api_gateway_resource" "unlock_s3_bucket" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  parent_id   = aws_api_gateway_rest_api.root_access_api.root_resource_id
  path_part   = "unlock-s3-bucket"
}

resource "aws_api_gateway_resource" "unlock_s3_bucket_account" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  parent_id   = aws_api_gateway_resource.unlock_s3_bucket.id
  path_part   = "{account_number}"
}

resource "aws_api_gateway_resource" "unlock_s3_bucket_bucket" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  parent_id   = aws_api_gateway_resource.unlock_s3_bucket_account.id
  path_part   = "{bucket_name}"
}

resource "aws_api_gateway_method" "unlock_s3_bucket_post" {
  rest_api_id      = aws_api_gateway_rest_api.root_access_api.id
  resource_id      = aws_api_gateway_resource.unlock_s3_bucket_bucket.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
  request_parameters = {
    "method.request.path.account_number" = true
    "method.request.path.bucket_name"    = true
  }
}

resource "aws_api_gateway_method" "unlock_s3_bucket_get" {
  rest_api_id      = aws_api_gateway_rest_api.root_access_api.id
  resource_id      = aws_api_gateway_resource.unlock_s3_bucket_bucket.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
  request_parameters = {
    "method.request.path.account_number" = true
    "method.request.path.bucket_name"    = true
  }
}

resource "aws_api_gateway_method" "unlock_s3_bucket_options" {
  rest_api_id   = aws_api_gateway_rest_api.root_access_api.id
  resource_id   = aws_api_gateway_resource.unlock_s3_bucket_bucket.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "unlock_s3_bucket" {
  rest_api_id             = aws_api_gateway_rest_api.root_access_api.id
  resource_id             = aws_api_gateway_resource.unlock_s3_bucket_bucket.id
  http_method             = aws_api_gateway_method.unlock_s3_bucket_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.unlock_s3_bucket_lambda.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration" "unlock_s3_bucket_get" {
  rest_api_id             = aws_api_gateway_rest_api.root_access_api.id
  resource_id             = aws_api_gateway_resource.unlock_s3_bucket_bucket.id
  http_method             = aws_api_gateway_method.unlock_s3_bucket_get.http_method
  integration_http_method = "POST" # Lambda proxy integration always uses POST
  type                    = "AWS_PROXY"
  uri                     = module.unlock_s3_bucket_lambda.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration" "unlock_s3_bucket_options" {
  rest_api_id             = aws_api_gateway_rest_api.root_access_api.id
  resource_id             = aws_api_gateway_resource.unlock_s3_bucket_bucket.id
  http_method             = aws_api_gateway_method.unlock_s3_bucket_options.http_method
  type                    = "MOCK"
  integration_http_method = "OPTIONS"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "unlock_s3_bucket_options" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  resource_id = aws_api_gateway_resource.unlock_s3_bucket_bucket.id
  http_method = aws_api_gateway_method.unlock_s3_bucket_options.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Headers" = true
  }
}

resource "aws_api_gateway_integration_response" "unlock_s3_bucket_options" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  resource_id = aws_api_gateway_resource.unlock_s3_bucket_bucket.id
  http_method = aws_api_gateway_method.unlock_s3_bucket_options.http_method
  status_code = aws_api_gateway_method_response.unlock_s3_bucket_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
  }

  response_templates = {
    "application/json" = ""
  }
  depends_on = [aws_api_gateway_integration.unlock_s3_bucket_options]
}