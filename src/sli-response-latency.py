import os
from modules.MonitorManager import MonitorManager

service_name_mackerel = os.environ.get('service_name_mackerel')
service_name_newrelic = os.environ.get('service_name_newrelic')
newrelic_account = os.environ.get('newrelic_account')


def lambda_handler(event, context):

    check_period_min = "60"
    percentiles = [99.9, 99.5, 99, 95, 50]
    map_list = map(str, percentiles)
    detail_numbers = "10"

    target_host_metrics_list = ('custom.sli.response.latency.millisecond.percentiles.50-percentile', 'custom.sli.response.latency.millisecond.percentiles.95-percentile', 'custom.sli.response.latency.millisecond.percentiles.99-percentile',
                                'custom.sli.response.latency.millisecond.percentiles.99_5-percentile', 'custom.sli.response.latency.millisecond.percentiles.99_9-percentile')
    monitor = MonitorManager()
    monitor.setNewRelic()
    monitor.setMackerel()

    result_query = "SELECT percentile(duration, %s) FROM Transaction SINCE %s MINUTES AGO WHERE appName = '%s'" % (','.join(map_list), check_period_min, service_name_newrelic)
    detail_query = "SELECT percentile(duration, 99.9) FROM Transaction FACET name SINCE %s MINUTES AGO WHERE appName = '%s' LIMIT %s" % (check_period_min, service_name_newrelic, detail_numbers)

    get_detail_req = monitor.getNewRelicInsightsQuery(newrelic_account, detail_query)
    for i in range(len(get_detail_req['facets'])):
        detail_host_metrics = ""
        details_name_raw = get_detail_req['facets'][i]["name"]
        # replace / to - (for mackerel specification)
        details_name = details_name_raw.replace("/", "-")
        detail_host_metrics = "custom.sli.response.latency.query.details.%s" % (details_name)
        # convert to millisecond
        details_result_raw = list(get_detail_req['facets'][i]["results"][0]["percentiles"].values())[0] * 1000
        # rounded up at the third decimal point
        details_result = f'{details_result_raw:.2f}'
        monitor.addMackerelServiceMetric(service_name_mackerel, detail_host_metrics, details_result)

    get_req = monitor.getNewRelicInsightsQuery(newrelic_account, result_query)
    percentiles = get_req['results'][0]['percentiles']
    for percentile, target_host_metrics in zip(percentiles.values(), target_host_metrics_list):
        # convert to millisecond
        payload_value_raw = percentile * 1000
        # rounded up at the third decimal point
        payload_value = f'{payload_value_raw:.2f}'
        print("post playload: " + payload_value)
        monitor.addMackerelServiceMetric(
                    service_name_mackerel, target_host_metrics, payload_value)

    monitor.sendMackerelServiceMetric()

    return 'end'
