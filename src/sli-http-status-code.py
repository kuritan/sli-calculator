import os
from datetime import datetime, timedelta
from pytz import timezone
from modules.MonitorManager import MonitorManager

mackerel_api_key = os.environ.get('mackerel_api_key')
host_id = os.environ.get('mackerel_host_id')
service_name_mackerel = os.environ.get('service_name_mackerel')
lb_hosting_platform_name = os.environ.get('lb_hosting_platform_name')

def lambda_handler(event, context):

    mackerel_span_period = 72239
    basedate = datetime.now(timezone('Asia/Tokyo'))
    basedate_unix_time = basedate.timestamp()
    yesterday = basedate - timedelta(days=1)
    last_week = basedate - timedelta(days=7)
    last_month = basedate - timedelta(days=30)
    last_quarter = basedate - timedelta(days=90)
    last_year = basedate - timedelta(days=365)

    monitor = MonitorManager()
    monitor.setMackerel()
    metrics_name = ""
    status_code_list = ()

    if lb_hosting_platform_name.lower() == "idcf":
        metrics_name = "custom.ilb.haproxy.status.STATUS.total.total_STATUS"
        status_code_list = ('other', '1xx', '2xx', '3xx', '4xx', '5xx')
    elif lb_hosting_platform_name.lower() == "aws":
        metrics_name = "custom.aws.alb.http_code_target_count.http_code_target_STATUS_count"
        status_code_list = ('2xx', '3xx', '4xx', '5xx')
    else:
        raise Exception("No supported platform used.")

    check_period_from_list = [yesterday.timestamp(), last_week.timestamp(
    ), last_month.timestamp(), last_quarter.timestamp(), last_year.timestamp()]

    target_host_metrics_list = ('custom.sli.http.statuscode.daily-percentage',
                                'custom.sli.http.statuscode.weekly-percentage',
                                'custom.sli.http.statuscode.monthly-percentage',
                                'custom.sli.http.statuscode.quarterly-percentage',
                                'custom.sli.http.statuscode.yearly-percentage')

    # weekly, monthly, quarterly, yearly loop
    for target_host_metrics, check_period_from in zip(target_host_metrics_list, check_period_from_list):
        dict_payload = dict_payload_full = {}

        for status_code in status_code_list:
            res_metrics_value = [0]
            status_path = metrics_name.replace('STATUS', status_code)
            from_unix_time = check_period_from
            # mackerelの仕様で、72239秒を超えた期間をリクエストすると、データが丸めに返される
            # 回避策として、72239秒分のリクエストだけを送る
            while from_unix_time < basedate_unix_time:
                to_unix_time = from_unix_time + mackerel_span_period

                # get metrics
                get_req = monitor.getMackerelHostMetric(
                    host_id, status_path, str(from_unix_time), str(to_unix_time))
                custom_body_json = get_req['metrics']

                for custom_body in custom_body_json:
                    count = int(custom_body['value'])
                    # 値が最新値より髙いであれば、絶対値を取ってからリストに入れる
                    if count > res_metrics_value[-1]:
                        count_absolute = count - res_metrics_value[-1]
                        res_metrics_value.append(count_absolute)
                    # 値が最新値より低いであれば、ilb側リセットが発生とみなされ、値そのままリストに入れる
                    elif count < res_metrics_value[-1]:
                        res_metrics_value.append(count)
                    # 値が最新値と一致であれば、変更なしとみなされる
                    else:
                        res_metrics_value.append(0)

                from_unix_time = to_unix_time

            # status codeとmetrics期間中合計値とマッピングする辞書を作成
            dict_payload[status_code] = sum(res_metrics_value)
            dict_payload_full.update(dict_payload)
            
            # last loop only
            if list(dict_payload_full.keys())[-1] is not "5xx":
                pass
            else:
                payload_value_raw = 100 * (
                    1 - int(list(dict_payload_full.values())[-1]) / sum(dict_payload_full.values()))
                # 小数点以下2桁まで、第3位を四捨五入
                payload_value = f'{payload_value_raw:.2f}'
                print("post playload: " + payload_value)
                monitor.addMackerelServiceMetric(
                    service_name_mackerel, target_host_metrics, payload_value)

            continue
        monitor.sendMackerelServiceMetric()
    return 'end'
