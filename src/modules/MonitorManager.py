#
# Environment variable
#   - mackerel_api_key   : required for sending metric data to mackerel
#   - newrelic_api_key   : required for sending metric data to newrelic
#   - newrelic_query_key : required for getting data from newrelic-insights-api
#
from datetime import datetime

import os
import re
import json
import urllib.request
import urllib.error
import urllib.parse
import calendar

from modules.MackerelClient import MackerelClient
from modules.NewRelicQueryClient import NewRelicQueryClient


class MonitorManager:

    def __init__(self):
        self.epoch_time = self.getEpochTime()
        self.__setMackerel()
        self.__setNewRelic()

    def __setMackerel(self):
        self.mackerel = {}
        self.mackerel['client'] = None
        self.mackerel['host_metrics'] = []
        self.mackerel['service_metrics'] = {}
        self.mackerel['api_key'] = os.environ.get("mackerel_api_key")

    def __setNewRelic(self):
        self.newrelic = {}
        self.newrelic['client'] = None
        self.newrelic['api_key'] = os.environ.get("newrelic_api_key")
        self.newrelic['query_key'] = os.environ.get("newrelic_query_key")

    #####
    #
    # Mackerel
    #

    def setMackerel(self):
        if self.mackerel['api_key'] is None:
            return False
        if self.mackerel['client']:
            return True
        self.mackerel['client'] = MackerelClient(self.mackerel['api_key'])
        return True

    #
    # Host
    #

    # keys of filters: service, role, name, status
    def getMackerelHosts(self, filters=None):
        return self.mackerel['client'].request("GET", "hosts", filters)

    def createMackerelHost(self, name, service, role):
        path = "hosts"
        data = {
            "name": name,
            "meta": {},
            "roleFullnames": ["%s:%s" % (service, role)],
        }
        res = self.mackerel['client'].request("POST", path, data)
        return res["id"] if res else False

    def getMackerelHostMetric(self, host_id, name, from_time, to_time):
        path = "hosts/%s/metrics?name=%s&from=%s&to=%s" % (
            host_id, name, from_time, to_time)
        return self.mackerel['client'].request("GET", path)

    def addMackerelHostMetric(self, host_id, name, value):
        metrics = {"hostId": host_id, "name": name,
                   "value": float(value), "time": self.epoch_time}
        self.mackerel['host_metrics'].append(metrics)

    def sendMackerelHostMetric(self):
        path = "tsdb"
        self.mackerel['client'].request(
            "POST", path, self.mackerel['host_metrics'])
        self.mackerel['host_metrics'] = []

    #
    # Service
    #
    def addMackerelServiceMetric(self, service, name, value):
        metrics = {"name": name, "value": float(
            value), "time": self.epoch_time}
        if service not in self.mackerel['service_metrics']:
            self.mackerel['service_metrics'][service] = []

        self.mackerel['service_metrics'][service].append(metrics)

    def sendMackerelServiceMetric(self):
        for service, metrics in list(self.mackerel['service_metrics'].items()):
            path = "services/%s/tsdb" % service
            self.mackerel['client'].request("POST", path, metrics)
            self.mackerel['service_metrics'][service] = []

    #
    # Graph
    #
    def makeMackerelGraphDefinitions(self, graphs):
        path = "graph-defs/create"
        self.mackerel['client'].request("POST", path, graphs)


    #####
    #
    # NewRelic
    #

    def setNewRelic(self):
        if self.setNewRelicAPI() or self.setNewRelicQuery():
            return True
        return False

    def setNewRelicAPI(self):
        if self.newrelic['api_key'] is None:
            return False
        if self.newrelic['client']:
            return True
        self.newrelic['client'] = NewRelicAPIClient(self.newrelic['api_key'])
        return True

    def setNewRelicQuery(self):
        if self.newrelic['query_key'] is None:
            return False
        if self.newrelic['client']:
            return True
        self.newrelic['client'] = NewRelicQueryClient(
            self.newrelic['query_key'])
        return True

    #
    # newrelic insights
    #

    def getNewRelicInsightsQuery(self, account, query):
        path = "%s/query" % (account)
        params = {"nrql": query}
        return self.newrelic['client'].request("GET", path, params, account)
