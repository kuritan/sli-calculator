locals {
  lambda_schedule_arns = {
    lambda-every-hour       = local.on_sli_monitoring ? aws_cloudwatch_event_rule.lambda-every-hour[0].arn : ""
    lambda-every-day        = local.on_sli_monitoring ? aws_cloudwatch_event_rule.lambda-every-day[0].arn : ""
  }
}

resource "aws_cloudwatch_event_rule" "lambda-every-hour" {
  count = local.on_sli_monitoring ? 1 : 0

  name                = "lambda-every-hour"
  description         = "Fires every hour"
  schedule_expression = "rate(1 hour)"
}

resource "aws_cloudwatch_event_rule" "lambda-every-day" {
  count = local.on_sli_monitoring ? 1 : 0

  name                = "lambda-every-day"
  description         = "Fires every day"
  schedule_expression = "rate(1 day)"
}
