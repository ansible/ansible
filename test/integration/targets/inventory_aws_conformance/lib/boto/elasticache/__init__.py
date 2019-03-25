class Connection(object):
    def __init__(self):
        pass

    def get_all_instances(self, *args, **kwargs):
        return []

    def describe_cache_clusters(self, *args, **kwargs):
        return {
            'DescribeCacheClustersResponse': {
                'DescribeCacheClustersResult': {
                    'Marker': None,
                    'CacheClusters': []
                }
            }
        }

    def describe_replication_groups(self, *args, **kwargs):
        return {
            'DescribeReplicationGroupsResponse': {
                'DescribeReplicationGroupsResult': {
                    'ReplicationGroups': []
                }
            }
        }


def connect_to_region(*args, **kwargs):
    return Connection()
