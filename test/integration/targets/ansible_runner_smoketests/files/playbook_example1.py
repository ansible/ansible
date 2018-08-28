#!/usr/bin/env python

import json
import os
import sys
import ansible_runner


PLAYBOOK = '''
- hosts: localhost
  gather_facts: False
  tasks:
    - set_fact:
        foo: bar
'''


output_dir = sys.argv[1]

invdir = os.path.join(output_dir, 'inventory')
if not os.path.isdir(invdir):
    os.makedirs(invdir)
with open(os.path.join(invdir, 'hosts'), 'w') as f:
    f.write('localhost\n')
pbfile = os.path.join(output_dir, 'test.yml')
with open(pbfile, 'w') as f:
    f.write(PLAYBOOK)

r = ansible_runner.run(private_data_dir=output_dir, playbook='test.yml')
'''
print("{}: {}".format(r.status, r.rc))
# successful: 0
for each_host_event in r.events:
    print(each_host_event['event'])
print("Final status:")
print(r.stats)
'''

data = {
    'rc': r.rc,
    'status': r.status,
    'events': [x['event'] for x in r.events],
    'stats': r.stats
}

print('#STARTJSON')
print(json.dumps(data))
