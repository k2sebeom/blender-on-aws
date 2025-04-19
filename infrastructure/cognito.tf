# Cognito User Pool
resource "aws_cognito_user_pool" "blender_pool" {
  name = "blender-user-pool"

  username_attributes = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_symbols   = true
  }

  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  schema {
    attribute_data_type = "String"
    name               = "email"
    required           = true
    mutable           = true

    string_attribute_constraints {
      min_length = 7
      max_length = 256
    }
  }
}

# Cognito User Pool Client
resource "aws_cognito_user_pool_client" "blender_client" {
  name = "blender-client"

  user_pool_id = aws_cognito_user_pool.blender_pool.id

  generate_secret = true
  
  callback_urls = ["https://${aws_lb.blender_alb.dns_name}/oauth2/idpresponse"]
  logout_urls   = ["https://${aws_lb.blender_alb.dns_name}"]

  allowed_oauth_flows = ["code"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_scopes = [
    "email",
    "openid",
  ]
  supported_identity_providers = ["COGNITO"]
}

# Cognito Domain
resource "aws_cognito_user_pool_domain" "blender_domain" {
  domain       = "blender-auth-${data.aws_caller_identity.current.account_id}"
  user_pool_id = aws_cognito_user_pool.blender_pool.id
}
