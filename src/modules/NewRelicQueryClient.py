#
# NewRelic InSights Query Client.
#

import os
import json
import urllib.request
import urllib.parse
import urllib.error


class NewRelicQueryClient:

    log = True

    # for insights-api
    api_query_protocol = "https"
    api_query_domain = "insights-api.newrelic.com"
    api_version = "/v1"
    api_path = "accounts"

    request_timeout = 10

    def __init__(self, query_key):
        self.__set_params()
        self.__set_url()
        self.__set_headers(query_key)

    def __log(self, log):
        if self.log:
            print(log)

    def __set_params(self):
        if os.environ.get('request_timeout'):
            self.request_timeout = int(os.environ['request_timeout'])

    def __set_url(self):
        self.query_url = "%s://%s%s/%s/" % (self.api_query_protocol,
                                            self.api_query_domain, self.api_version, self.api_path)

    def __set_headers(self, query_key):
        self.headers = {
            'Content-Type': 'application/json',
            'X-Query-Key': query_key,
        }

    def request(self, method, path, params, account):
        if account is None:
            print("Need account number.")
            return False
        else:
            print("Using " + account + " account")
            url = "%s%s" % (self.query_url, path)
        data = None

        if method == "GET":
            if params is not None:
                url += "?%s" % urllib.parse.urlencode(params)
        else:
            if not params:
                print("Not found POST data.")
                return
            data = json.dumps(params).encode()

        try:
            log = "NewRelic to [%s]" % path
            if data:
                log += " %s" % data
            self.__log(log)
            request = urllib.request.Request(url, data, self.headers)
            self.__log("Success connecting server (%s)." % url)
        except Exception as e:
            self.__log("Can't connect server (%s).\nERROR: %s" % (url, e))
            return False

        try:
            self.__log("Start  API request. timeout is %s" %
                       self.request_timeout)
            res = json.load(urllib.request.urlopen(
                request, timeout=self.request_timeout))
            self.__log("Finish API request.")
        except Exception as e:
            self.__log("Failed API request.\nERROR: %s" % e)
            return False

        if 'error' in res:
            self.__log("Error response (%s)" % (res['error']))
            return False

        return res


if __name__ == '__main__':
    client = NewRelicClient()
    print(client.request("GET", "hosts"))
