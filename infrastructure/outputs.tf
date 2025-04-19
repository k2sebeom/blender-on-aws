output "instance_public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.blender_instance.public_ip
}

output "efs_id" {
  description = "ID of the EFS file system"
  value       = aws_efs_file_system.blender_efs.id
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}
