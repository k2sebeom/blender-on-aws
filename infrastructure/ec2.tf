# Security Group for EC2
resource "aws_security_group" "blender_sg" {
  name        = "blender-security-group"
  description = "Security group for Blender application"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
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
    Name = "blender-security-group"
  }
}

# EC2 Instance
resource "aws_instance" "blender_instance" {
  ami           = var.instance_ami
  instance_type = var.instance_type
  subnet_id     = module.vpc.public_subnets[0]

  vpc_security_group_ids = [aws_security_group.blender_sg.id]

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  tags = {
    Name = "blender-instance"
  }

  # Script to mount EFS
  user_data = templatefile("${path.module}/user_data.tpl", {
    efs_id             = aws_efs_file_system.blender_efs.id
    additional_user_data = var.user_data
  })
}
