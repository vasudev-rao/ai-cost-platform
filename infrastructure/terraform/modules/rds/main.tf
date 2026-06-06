variable "identifier"        {}
variable "engine_version"    { default = "16.2" }
variable "instance_class"    { default = "db.r6g.large" }
variable "allocated_storage" { default = 50 }
variable "vpc_id"            {}
variable "subnet_ids"        { type = list(string) }
variable "db_name"           { default = "ai_cost_platform" }

resource "aws_db_subnet_group" "main" {
  name       = "${var.identifier}-subnet-group"
  subnet_ids = var.subnet_ids
}

resource "aws_security_group" "rds" {
  name   = "${var.identifier}-rds-sg"
  vpc_id = var.vpc_id
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }
}

resource "aws_db_instance" "main" {
  identifier              = var.identifier
  engine                  = "postgres"
  engine_version          = var.engine_version
  instance_class          = var.instance_class
  allocated_storage       = var.allocated_storage
  max_allocated_storage   = var.allocated_storage * 4
  storage_encrypted       = true
  db_name                 = var.db_name
  username                = "postgres"
  password                = random_password.db.result
  db_subnet_group_name    = aws_db_subnet_group.main.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  multi_az                = true
  backup_retention_period = 7
  deletion_protection     = true
  skip_final_snapshot     = false
  final_snapshot_identifier = "${var.identifier}-final"
  parameter_group_name    = aws_db_parameter_group.main.name
}

resource "aws_db_parameter_group" "main" {
  name   = "${var.identifier}-pg16"
  family = "postgres16"
  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }
}

resource "random_password" "db" {
  length  = 32
  special = false
}

output "endpoint" { value = aws_db_instance.main.endpoint }
output "password"  {
  value     = random_password.db.result
  sensitive = true
}
