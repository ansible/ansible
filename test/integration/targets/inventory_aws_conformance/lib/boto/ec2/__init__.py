# boto2

from boto.mocks.instances import BotoInstance


class Region(object):
    name = None
    def __init__(self, name):
        self.name = name


class Connection(object):
    region = None
    instances = None

    def __init__(self, **kwargs):
        self.instances = [
            BotoInstance(id=100, region=kwargs['region'])
        ]
        if 'region' in kwargs:
            self.region = kwargs['region']
            for x in self.instances:
                x.region = self.region

    def get_all_instances(self, *args, **kwargs):
        return self.instances

    def describe_cache_clusters(*args, **kwargs):
        return {}

    def get_all_tags(*args, **kwargs):
        return []


def connect_to_region(*args, **kwargs):
    return Connection(region=args[0])


def regions():
    return [Region('us-east-1')]
