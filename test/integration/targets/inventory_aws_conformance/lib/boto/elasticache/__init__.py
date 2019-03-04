class Connection(object):
    def __init__(self):
        pass

    def get_all_instances(*args, **kwargs):
        return []

    def describe_cache_clusters(*args, **kwargs):
        return {
            'DescribeCacheClustersResponse': {
                'DescribeCacheClustersResult': {
                    'Marker': None,
                    'CacheClusters': []
                }
            }
        }

    def describe_replication_groups(*args, **kwargs):
        return {
            'DescribeReplicationGroupsResponse': {
                'DescribeReplicationGroupsResult': {
                    'ReplicationGroups': []
                }
            }
        }

def connect_to_region(*args, **kwargs):
    return Connection()
