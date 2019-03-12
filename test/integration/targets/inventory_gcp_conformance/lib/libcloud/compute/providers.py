import libcloud.compute.drivers.gce


def get_driver(*args, **kwargs):
    return libcloud.compute.drivers.gce.GCENodeDriver
