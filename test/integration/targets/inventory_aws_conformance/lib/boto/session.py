#!/usr/bin/env python
# boto3

'''
try:
    from mocks.instances import Boto3Instance
except ModuleNotFoundError:
    from boto.mocks.instances import Boto3Instance
'''
from boto.mocks.instances import Boto3Instance


class Paginator(object):
    def __init__(self, datalist):
        self.datalist = datalist
    def paginate(self, *args, **kwargs):
        '''
        {'Filters': [{'Name': 'instance-state-name',
            'Values': ['running', 'pending', 'stopping', 'stopped']}]}
        '''
        return self

    def build_full_result(self):
        return {'Reservations': [{'Instances': [x.to_dict() for x in self.datalist]}]}


class Client(object):
    cloud = None
    region = None
    def __init__(self, *args, **kwargs):
        self.cloud = args[0]
        self.region = args[1]

    def get_paginator(self, method):
        if method == 'describe_instances':
            return Paginator([Boto3Instance(id=100, region=self.region)])


class Session(object):
    profile_name = None
    region = None

    def __init__(self, *args, **kwargs):
        for k,v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
        #self.client = Client(*args, **kwargs)

    def client(self, *args, **kwargs):
        return Client(*args, **kwargs)

    def get_config_variables(self, key):
        if hasattr(self, key):
            return getattr(self, key)        

    def get_available_regions(self, *args):
        # args[0] == 'ec2'
        return ['us-east-1']
        
    def get_credentials(self, *args, **kwargs):
        raise Exception('not implemented')


def get_session(*args, **kwargs):
    return Session(*args, **kwargs)
