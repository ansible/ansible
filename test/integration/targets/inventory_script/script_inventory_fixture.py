#!/usr/bin/env python

from __future__ import annotations

import argparse
import copy
import json
import os
import sys

inventory = dict(
    _meta=dict(hostvars=dict(localhost=dict(a_localhost_hostvar="avalue"), host1=dict(a_host1_hostvar="avalue"))),
    all=dict(children=["ungrouped", "group1", "empty_group"]),
    ungrouped=dict(hosts=["localhost"]),
    group1=dict(hosts=["host1"], vars=dict(a_group1_groupvar="avalue", group1_untrusted_var=dict(__ansible_unsafe="untrusted value"))),
    list_as_group=[],  # assigned to `hosts` in a new dict
    # this test case will be rewritten as a group with a host named `rewrite_as_host`, both vars will be untrusted
    rewrite_as_host=dict(avar="value", untrusted_var=dict(__ansible_unsafe="untrusted value")),
)

inventory_with_profile = copy.deepcopy(inventory)
inventory_with_profile['_meta']['profile'] = 'inventory_legacy'

normal_outputs = dict(
    # invalid
    invalid_utf8=b'i am invalid UTF-8 \xff\n',
    invalid_json="i am not JSON",
    invalid_type='"i am not a dict"',
    invalid_meta_type=dict(_meta='not a dict'),
    invalid_profile_type=dict(_meta=dict(profile=1)),
    invalid_profile_name=dict(_meta=dict(profile='invalid_profile')),
    invalid_inventory_profile_name=dict(_meta=dict(profile='inventory_invalid_profile')),
    invalid_json_for_profile=dict(dict(__ansible_vault=1)),
    invalid_meta_hostvars_type=dict(_meta=dict(hostvars=[])),
    invalid_meta_hostvars_type_for_host=dict(_meta=dict(hostvars=dict(myhost=[])), mygroup=dict(hosts=['myhost'])),
    invalid_group_vars_type=dict(_meta=dict(hostvars={}), mygroup=dict(vars=[])),
    invalid_group_type=dict(_meta=dict(hostvars={}), mygroup=None),
    no_meta_hostvars_host_nonzero_rc=dict(mygroup=dict(hosts=["myhost"])),  # trigger legacy "slow" path which invokes the script with --host for each host
    no_meta_hostvars_host_invalid_json=dict(mygroup=dict(hosts=["myhost"])),  # trigger legacy "slow" path which invokes the script with --host for each host
    # valid
    no_hosts=dict(_meta=dict(hostvars={})),
    no_profile=inventory,
    with_profile=inventory_with_profile,
    no_meta_hostvars=dict(mygroup=dict(hosts=["myhost"])),  # trigger legacy "slow" path which invokes the script with --host for each host
    no_meta_hostvars_empty_host_result=dict(mygroup=dict(hosts=["myhost"])),  # trigger legacy "slow" path which invokes the script with --host for each host
)

host_outputs = dict(
    # invalid/fail
    no_meta_hostvars_host_nonzero_rc=lambda: sys.exit(1),
    no_meta_hostvars_host_invalid_json=lambda: sys.exit(print("this is not JSON")),
    # valid
    no_meta_hostvars=dict(
        myhost=dict(avar="avalue", untrusted=dict(__ansible_unsafe="untrusted value")),
    ),
    no_meta_hostvars_empty_host_result=lambda: sys.exit(0),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--host')
    parser.add_argument('--list', action='store_true')

    args = parser.parse_args()
    host: str | None = args.host

    if os.environ.get("INVENTORY_EMIT_STDERR"):
        print('this is stderr', file=sys.stderr, end='')

    if host:
        outputs = host_outputs
    else:
        outputs = normal_outputs

    if not (output := outputs.get(os.environ.get('INVENTORY_TEST_MODE'))):
        print(f"The `INVENTORY_TEST_MODE` envvar should be one of: \n{os.linesep.join(outputs)}", file=sys.stderr)
        sys.exit(1)

    if callable(output):
        output()

    if host:
        output = output.get(host)

    if isinstance(output, bytes):
        sys.stdout.buffer.write(output)
    else:
        if not isinstance(output, str):
            output = json.dumps(output)

        print(output)


if __name__ == '__main__':
    main()
