resource "aws_api_gateway_resource" "delete_root_login_profile" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  parent_id   = aws_api_gateway_rest_api.root_access_api.root_resource_id
  path_part   = "delete-root-login-profile"
}

resource "aws_api_gateway_resource" "delete_root_login_profile_account" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  parent_id   = aws_api_gateway_resource.delete_root_login_profile.id
  path_part   = "{account_number}"
}

resource "aws_api_gateway_method" "delete_root_login_profile_post" {
  rest_api_id      = aws_api_gateway_rest_api.root_access_api.id
  resource_id      = aws_api_gateway_resource.delete_root_login_profile_account.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
  request_parameters = {
    "method.request.path.account_number" = true
  }
}

resource "aws_api_gateway_method" "delete_root_login_profile_options" {
  rest_api_id   = aws_api_gateway_rest_api.root_access_api.id
  resource_id   = aws_api_gateway_resource.delete_root_login_profile_account.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "delete_root_login_profile" {
  rest_api_id             = aws_api_gateway_rest_api.root_access_api.id
  resource_id             = aws_api_gateway_resource.delete_root_login_profile_account.id
  http_method             = aws_api_gateway_method.delete_root_login_profile_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.delete_root_login_profile_lambda.lambda_function_invoke_arn
}

# --


resource "aws_api_gateway_integration" "delete_root_login_profile_options" {
  rest_api_id             = aws_api_gateway_rest_api.root_access_api.id
  resource_id             = aws_api_gateway_resource.delete_root_login_profile_account.id
  http_method             = aws_api_gateway_method.delete_root_login_profile_options.http_method
  type                    = "MOCK"
  integration_http_method = "OPTIONS"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "delete_root_login_profile_options" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  resource_id = aws_api_gateway_resource.delete_root_login_profile_account.id
  http_method = aws_api_gateway_method.delete_root_login_profile_options.http_method
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

resource "aws_api_gateway_integration_response" "delete_root_login_profile_options" {
  rest_api_id = aws_api_gateway_rest_api.root_access_api.id
  resource_id = aws_api_gateway_resource.delete_root_login_profile_account.id
  http_method = aws_api_gateway_method.delete_root_login_profile_options.http_method
  status_code = aws_api_gateway_method_response.delete_root_login_profile_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
  }

  response_templates = {
    "application/json" = ""
  }
  depends_on = [aws_api_gateway_integration.delete_root_login_profile_options]
}