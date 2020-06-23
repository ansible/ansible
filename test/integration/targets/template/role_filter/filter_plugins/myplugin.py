#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class FilterModule(object):
    def filters(self):
        return {'parse_ip': self.parse_ip}

    def parse_ip(self, ip):
        return ip
