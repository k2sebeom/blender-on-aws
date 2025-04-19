# Generate private key
resource "tls_private_key" "cert_private_key" {
  algorithm = "RSA"
}

# Generate self-signed certificate
resource "tls_self_signed_cert" "cert" {
  private_key_pem = tls_private_key.cert_private_key.private_key_pem

  subject {
    common_name  = "blender-alb.local"
    organization = "Blender ALB Self Signed"
  }

  validity_period_hours = 8760 # 1 year

  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "server_auth",
  ]
}

# Import the self-signed certificate to ACM
resource "aws_acm_certificate" "cert" {
  private_key      = tls_private_key.cert_private_key.private_key_pem
  certificate_body = tls_self_signed_cert.cert.cert_pem

  tags = {
    Name = "blender-alb-self-signed-cert"
  }

  lifecycle {
    create_before_destroy = true
  }
}
