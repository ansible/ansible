from __future__ import annotations


import re
import json


def parse_json(value):
    return json.dumps(json.loads(re.sub('^.*\n#STARTJSON\n', '', value, flags=re.DOTALL)), indent=4, sort_keys=True)


class FilterModule(object):
    def filters(self):
        return {
            'parse_json': parse_json,
        }
