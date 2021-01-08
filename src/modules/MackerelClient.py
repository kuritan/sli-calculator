#
# Mackerel API Client.
#

import os
import json
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse

class MackerelClient:

    log = True

    api_protocol = "https"
    api_domain   = "api.mackerelio.com"
    api_path     = "/api"
    api_version  = "v0"

    request_timeout = 10

    def __init__(self, api_key):
        self.__set_params()
        self.__set_url()
        self.__set_headers(api_key)

    def __log(self, log):
        if self.log: print(log)

    def __set_params(self):
        if os.environ.get('request_timeout'):
            self.request_timeout = int(os.environ['request_timeout'])

    def __set_url(self):
        self.url = "%s://%s%s/%s/" % (self.api_protocol, self.api_domain, self.api_path, self.api_version)

    def __set_headers(self, api_key):
        self.headers = {
            'Content-Type': 'application/json',
            'X-Api-Key'   : api_key,
        }

    def request(self, method, path, params=None):
        url  = "%s%s" % (self.url, path)
        data = None

        if method == "GET":
            if params is not None: url += "?%s" % urllib.parse.urlencode(params)
        else:
            if not params:
                print("Not found POST data.")
                return
            data = json.dumps(params).encode()

        try:
            log = "mackerel to [%s]" % path
            if data: log += " %s" % data
            self.__log(log)
            request = urllib.request.Request(url, data, self.headers)
            self.__log("Success connecting server (%s)." % url)
        except Exception as e:
            self.__log("Can't connect server (%s).\nERROR: %s" % (url, e))
            return False

        try:
            self.__log("Start  API request. timeout is %s" % self.request_timeout)
            res = json.loads(urllib.request.urlopen(request, timeout=self.request_timeout).read())
            self.__log("Finish API request.")
        except Exception as e:
            self.__log("Failed API request.\nERROR: %s" % e)
            return False

        if 'error' in res:
            self.__log("Error response (%s)" % (res['error']))
            return False

        return res

if __name__ == '__main__':
    client = MackerelClient()
    print(client.request("GET", "hosts"))

