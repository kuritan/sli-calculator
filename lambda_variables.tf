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