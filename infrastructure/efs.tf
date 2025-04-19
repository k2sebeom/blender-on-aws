# EFS File System
resource "aws_efs_file_system" "blender_efs" {
  creation_token = "blender-efs"
  
  tags = {
    Name = "blender-efs"
  }
}

# EFS Mount Targets
resource "aws_efs_mount_target" "blender_efs_mount" {
  count           = length(module.vpc.private_subnets)
  file_system_id  = aws_efs_file_system.blender_efs.id
  subnet_id       = module.vpc.private_subnets[count.index]
  security_groups = [aws_security_group.efs_sg.id]
}

# Security Group for EFS
resource "aws_security_group" "efs_sg" {
  name        = "efs-security-group"
  description = "Security group for EFS mount targets"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.blender_sg.id]
  }

  tags = {
    Name = "efs-security-group"
  }
}
