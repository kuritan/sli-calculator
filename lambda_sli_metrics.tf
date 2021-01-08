#
# For SLI monitoring
#
locals {
    sli_monitoring_enabled = true
    on_sli_monitoring      = local.sli_monitoring_enabled ? true : false

    # lambda runtime
    lambda_runtime = "python3.6"

    # IDCF or AWS
    lb_hosting_platform_name = ""

    # LBのHTTP status
    sli_http_status_host_id = ""
    lambda_sli-http-status-code = [
      {
        "name" = "sli-http-status-code"
        "rule" = "lambda-every-day"
      }
    ]

    # mackerel account's information
    mackerel_api_key = ""

    # newrelic account's information
    newrelic_account = ""
    newrelic_query_key = ""
    lambda_sli-response-latency = [
      {
        "name" = "sli-response-latency"
        "rule" = "lambda-every-hour"
      },
    ]
}

#
# http status code
#
resource "aws_lambda_function" "sli-http-status-code" {
  count = local.on_sli_monitoring ? 1 : 0

  function_name     = local.lambda_sli-http-status-code[count.index]["name"]
  handler           = "${local.lambda_sli-http-status-code[count.index]["name"]}.lambda_handler"
  filename          = "${data.archive_file.function_zip.output_path}"

  layers = ["${aws_lambda_layer_version.lambda_layer.arn}"]

  memory_size = 3008
  timeout     = 600

  runtime = local.lambda_runtime
  role    = "${aws_iam_role.lambda_iam_role.arn}"
  source_code_hash = "${data.archive_file.function_zip.output_base64sha256}"

  environment {
    variables = {
      mackerel_api_key = local.mackerel_api_key
      mackerel_host_id = local.sli_http_status_host_id
      lb_hosting_platform_name = local.lb_hosting_platform_name
    }
  }
}

resource "aws_cloudwatch_event_target" "sli-http-status-code" {
  count = local.on_sli_monitoring ? 1 : 0

  target_id = local.lambda_sli-http-status-code[count.index]["name"]
  arn       = element(aws_lambda_function.sli-http-status-code.*.arn, count.index)
  rule      = local.lambda_sli-http-status-code[count.index]["rule"]
}

resource "aws_lambda_permission" "sli-http-status-code" {
  count = local.on_sli_monitoring ? 1 : 0

  statement_id = "AllowExecutionFromCloudWatch"
  action       = "lambda:InvokeFunction"
  principal    = "events.amazonaws.com"

  function_name = element(aws_lambda_function.sli-http-status-code.*.function_name, count.index)
  source_arn    = local.lambda_schedule_arns[local.lambda_sli-http-status-code[count.index]["rule"]]
}

resource "aws_cloudwatch_log_group" "sli-http-status-code" {
  count = local.on_sli_monitoring ? 1 : 0

  name              = format("%s%s", local.lambda_log_group_prefix, local.lambda_sli-http-status-code[count.index]["name"])
  retention_in_days = 7
}

#
# response latency
#
resource "aws_lambda_function" "sli-response-latency" {
  count = local.on_sli_monitoring ? 1 : 0

  function_name     = local.lambda_sli-response-latency[count.index]["name"]
  handler           = "${local.lambda_sli-response-latency[count.index]["name"]}.lambda_handler"
  filename          = "${data.archive_file.function_zip.output_path}"

  layers = ["${aws_lambda_layer_version.lambda_layer.arn}"]

  memory_size = 128
  timeout     = 30

  runtime = local.lambda_runtime
  role    = "${aws_iam_role.lambda_iam_role.arn}"
  source_code_hash = "${data.archive_file.function_zip.output_base64sha256}"

  environment {
    variables = {
      mackerel_api_key = local.mackerel_api_key
      newrelic_query_key = local.newrelic_query_key
      newrelic_account = local.newrelic_account
    }
  }
}

resource "aws_cloudwatch_event_target" "sli-response-latency" {
  count = local.on_sli_monitoring ? 1 : 0

  target_id = local.lambda_sli-response-latency[count.index]["name"]
  arn       = element(aws_lambda_function.sli-response-latency.*.arn, count.index)
  rule      = local.lambda_sli-response-latency[count.index]["rule"]
}

resource "aws_lambda_permission" "sli-response-latency" {
  count = local.on_sli_monitoring ? 1 : 0

  statement_id = "AllowExecutionFromCloudWatch"
  action       = "lambda:InvokeFunction"
  principal    = "events.amazonaws.com"

  function_name = element(aws_lambda_function.sli-response-latency.*.function_name, count.index)
  source_arn    = local.lambda_schedule_arns[local.lambda_sli-response-latency[count.index]["rule"]]
}

resource "aws_cloudwatch_log_group" "sli-response-latency" {
  count = local.on_sli_monitoring ? 1 : 0

  name              = format("%s%s", local.lambda_log_group_prefix, local.lambda_sli-response-latency[count.index]["name"])
  retention_in_days = 7
}


# Role
resource "aws_iam_role" "lambda_iam_role" {
  count = local.on_sli_monitoring ? 1 : 0

  name = var.system_name_iam_role

  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
POLICY
}

# Policy
resource "aws_iam_role_policy" "lambda_access_policy" {
  count = local.on_sli_monitoring ? 1 : 0
  
  name   = var.system_name_lambda_access_policy
  role   = aws_iam_role.lambda_iam_role.id
  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:CreateLogGroup",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
POLICY
}