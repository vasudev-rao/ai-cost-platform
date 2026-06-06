terraform {
  required_version = ">= 1.8"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    bucket = "ai-cost-platform-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" { region = var.aws_region }

module "vpc" {
  source             = "../../modules/vpc"
  name               = "${var.project}-${var.env}"
  cidr               = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets    = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

module "eks" {
  source          = "../../modules/eks"
  cluster_name    = "${var.project}-${var.env}"
  cluster_version = "1.30"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids
  node_groups = {
    general = { instance_types = ["m6i.xlarge"],  min = 2, max = 10, desired = 3 }
    gpu     = { instance_types = ["g5.12xlarge"], min = 0, max = 5,  desired = 0,
                labels = { workload = "gpu" }, taints = [{ key = "gpu", value = "true", effect = "NO_SCHEDULE" }] }
  }
}

module "rds" {
  source            = "../../modules/rds"
  identifier        = "${var.project}-${var.env}"
  engine_version    = "16.2"
  instance_class    = "db.r6g.xlarge"
  allocated_storage = 100
  vpc_id            = module.vpc.vpc_id
  subnet_ids        = module.vpc.private_subnet_ids
  db_name           = "ai_cost_platform"
}

module "s3" {
  source      = "../../modules/s3"
  bucket_name = "${var.project}-data-${var.env}"
  versioning  = true
  lifecycle_rules = [
    { id = "archive", prefix = "delta/bronze/", transition_days = 90, storage_class = "GLACIER" }
  ]
}

variable "project"    { default = "ai-cost-platform" }
variable "env"        { default = "prod" }
variable "aws_region" { default = "us-east-1" }
