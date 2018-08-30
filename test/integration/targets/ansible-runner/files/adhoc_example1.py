import json
import os
import sys
import ansible_runner

# the first positional arg should be where the artifacts live
output_dir = sys.argv[1]

# this calls a single module directly, aka "adhoc" mode
r = ansible_runner.run(
    private_data_dir=output_dir,
    host_pattern='localhost',
    module='shell',
    module_args='whoami'
)

data = {
    'rc': r.rc,
    'status': r.status,
    'events': [x['event'] for x in r.events],
    'stats': r.stats
}

# insert this header for the flask controller
print('#STARTJSON')
json.dump(data, sys.stdout)
