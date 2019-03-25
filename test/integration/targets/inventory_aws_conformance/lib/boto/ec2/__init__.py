# boto2

from boto.mocks.instances import BotoInstance, Reservation


class Region(object):
    name = None

    def __init__(self, name):
        self.name = name


class Connection(object):
    region = None
    instances = None

    def __init__(self, **kwargs):
        self.reservations = [Reservation(
            owner_id='123456789012',
            instance_ids=['i-0678e70402c0b434c', 'i-16a83b42f01c082a1'],
            region=kwargs['region']
        )]

    def get_all_instances(self, *args, **kwargs):
        return self.reservations

    def describe_cache_clusters(self, *args, **kwargs):
        return {}

    def get_all_tags(self, *args, **kwargs):
        tags = []
        resid = kwargs['filters']['resource-id'][0]
        for instance in self.reservations[0].instances:
            if instance.id == resid:
                tags = instance._tags[:]
                break
        return tags


def connect_to_region(*args, **kwargs):
    return Connection(region=args[0])


def regions():
    return [Region('us-east-1')]
