#!/usr/bin/env python
# boto3

from boto.mocks.instances import Boto3Instance


class Paginator(object):
    def __init__(self, datalist):
        self.datalist = datalist

    def paginate(self, *args, **kwargs):
        '''
        {'Filters': [{'Name': 'instance-state-name',
            'Values': ['running', 'pending', 'stopping', 'stopped']}]}
        '''
        filters = kwargs.get('Filters', [])
        if not (filters or any([True for f in filters if f['Name'] == 'instance-state-name'])):
            self.instance_states = ['running', 'pending', 'stopping', 'stopped']
        else:
            self.instance_states = [f['Values'] for f in filters if f['Name'] == 'instance-state-name'][0]
        return self

    def build_full_result(self):
        filtered_states = set([x.state['Name'] for x in self.datalist]).difference(set(self.instance_states))
        return {'Reservations': [{
            'Instances': [x.to_dict() for x in self.datalist if x.state['Name'] not in filtered_states],
            'OwnerId': '123456789012',
            'RequesterId': 'AIDAIS3MMFPO53D2T3WWE',
            'ReservationId': 'r-07889670a282de964'
        }]}


class Client(object):
    cloud = None
    region = None

    def __init__(self, *args, **kwargs):
        self.cloud = args[0]
        self.region = args[1]

    def get_paginator(self, method):
        if method == 'describe_instances':
            return Paginator(
                [Boto3Instance(instance_id='i-0678e70402c0b434c', owner_id='123456789012', region=self.region),
                 Boto3Instance(instance_id='i-16a83b42f01c082a1', owner_id='123456789012', region=self.region, stopped=True)]
            )


class Session(object):
    profile_name = None
    region = None

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def client(self, *args, **kwargs):
        return Client(*args, **kwargs)

    def get_config_variables(self, key):
        if hasattr(self, key):
            return getattr(self, key)

    def get_available_regions(self, *args):
        return ['us-east-1']

    def get_credentials(self, *args, **kwargs):
        raise Exception('not implemented')


def get_session(*args, **kwargs):
    return Session(*args, **kwargs)
