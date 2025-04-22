output "efs_id" {
  description = "ID of the EFS file system"
  value       = aws_efs_file_system.blender_efs.id
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.blender_alb.dns_name
}
