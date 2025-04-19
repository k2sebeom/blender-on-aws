variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "instance_ami" {
  description = "AMI ID for the EC2 instance"
  type        = string
}

variable "instance_type" {
  description = "Instance type for the EC2 instance"
  type        = string
  default     = "t3.micro"
}

variable "github_repo" {
  description = "Github repo for blender-on-aws project"
  type        = string
  default = "https://github.com/k2sebeom/blender-on-aws.git"
}
