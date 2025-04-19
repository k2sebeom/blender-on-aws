# Blender on AWS

A streamlined solution for running Blender rendering workloads on AWS infrastructure. This project provides both the infrastructure setup using Terraform and a Streamlit-based interface for managing Blender rendering jobs.

## Overview

This project enables:
- Automated AWS infrastructure provisioning for Blender workloads
- EFS-backed storage for persistent data
- Streamlit interface for job management
- Automated Blender installation and configuration

## Infrastructure Components

The project uses Terraform to provision the following AWS resources:

- **VPC Configuration**
  - Custom VPC with public and private subnets
  - NAT Gateway for private subnet internet access
  - DNS support enabled

- **EC2 Instance**
  - Runs in a private subnet
  - Configured with SSM for secure access
  - Automatically installs Blender and required dependencies
  - Security group allowing Streamlit port (8501)

- **EFS Storage**
  - Persistent storage for Blender files and renders
  - Automatically mounted to EC2 instance
  - Secured with dedicated security group

- **IAM Configuration**
  - EC2 instance role with SSM capabilities
  - Secure access management

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform installed (version >= 1.2.0)
3. Python environment management tool (uv recommended)

## Setup and Usage

1. **Infrastructure Deployment**

```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

2. **Running the Application**

The application can be started using:

```bash
uv run ./run.sh
```

This will launch the Streamlit interface where you can manage your Blender rendering jobs.

## Project Structure

```
.
├── infrastructure/          # Terraform configuration files
│   ├── ec2.tf             # EC2 instance and security group configuration
│   ├── efs.tf             # EFS storage configuration
│   ├── iam.tf             # IAM roles and policies
│   ├── vpc.tf             # VPC network configuration
│   └── ...
├── src/                    # Application source code
│   ├── config/            # Configuration management
│   ├── models/            # Data models
│   ├── services/          # Core services (Blender, FFmpeg, etc.)
│   └── utils/             # Utility functions
├── scripts/               # Helper scripts
└── run.sh                 # Application startup script
```

## Configuration

The application can be configured through `config.yaml`. Ensure this file is properly set up before running the application.
