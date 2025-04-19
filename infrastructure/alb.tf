# Security Group for ALB
resource "aws_security_group" "alb_sg" {
  name        = "blender-alb-security-group"
  description = "Security group for Application Load Balancer"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "blender-alb-security-group"
  }
}

# Application Load Balancer
resource "aws_lb" "blender_alb" {
  name               = "blender-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = module.vpc.public_subnets

  enable_deletion_protection = false

  tags = {
    Name = "blender-alb"
  }
}

# Target Group
resource "aws_lb_target_group" "blender_tg" {
  name     = "blender-target-group"
  port     = 8501
  protocol = "HTTP"
  vpc_id   = module.vpc.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval           = 30
    matcher            = "200"
    path              = "/"
    port              = "traffic-port"
    protocol          = "HTTP"
    timeout           = 5
    unhealthy_threshold = 2
  }
}

# Target Group Attachment
resource "aws_lb_target_group_attachment" "blender_tg_attachment" {
  target_group_arn = aws_lb_target_group.blender_tg.arn
  target_id        = aws_instance.blender_instance.id
  port             = 8501
}

# HTTPS Listener
resource "aws_lb_listener" "front_end" {
  load_balancer_arn = aws_lb.blender_alb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate.cert.arn

  default_action {
    type = "authenticate-cognito"

    authenticate_cognito {
      user_pool_arn       = aws_cognito_user_pool.blender_pool.arn
      user_pool_client_id = aws_cognito_user_pool_client.blender_client.id
      user_pool_domain    = aws_cognito_user_pool_domain.blender_domain.domain
    }

    order = 1
  }

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.blender_tg.arn
    order            = 2
  }
}

# HTTP Listener (Redirect to HTTPS)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.blender_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
      host        = "#{host}"
      path        = "/#{path}"
      query       = "#{query}"
    }
  }
}
