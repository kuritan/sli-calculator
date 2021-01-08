# Provider
provider "aws" {
  region  = "ap-northeast-1"
  version = ">= 2.57"
}

# Variables
variable "system_name" {
  default="terraform-lambda"
}

# Archive
data "archive_file" "layer_zip" {
  type        = "zip"
  source_dir  = "build/layer"
  output_path = "lambda/layer.zip"
}
data "archive_file" "function_zip" {
  type        = "zip"
  source_dir  = "build/function"
  output_path = "lambda/function.zip"
}

# Layer
resource "aws_lambda_layer_version" "lambda_layer" {
  count = local.on_sli_monitoring ? 1 : 0

  layer_name = var.system_name_lambda_layer
  filename   = data.archive_file.layer_zip.output_path
  source_code_hash = data.archive_file.layer_zip.output_base64sha256
}