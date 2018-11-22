import re


def get_bgp_as(config):
    match = re.search('^router bgp (\d+)', config, re.M)
    if match:
        return int(match.group(1))
