#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
CLI tool that analyses a Shippable run's test result and re-balances the test targets into new groups.

Before running this script you must run download.py like

./download.py https://app.shippable.com/github/<team>/<repo>/runs/<run_num> --test-results --job-number x --job-number y

Set the dir <team>/<repo>/<run_num> as the value of '-p/--test-path' for this script.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import argparse
import json
import operator
import os

try:
    import argcomplete
except ImportError:
    argcomplete = None


def main():
    """Main program body."""
    args = parse_args()
    rebalance(args)


def parse_args():
    """Parse and return args."""
    parser = argparse.ArgumentParser(description='Re-balance Shippable group(s) from a downloaded results directory.')

    parser.add_argument('group_count',
                        metavar='group_count',
                        help='The number of groups to re-balance the tests to.')

    parser.add_argument('-p', '--test-path',
                        dest='test_path',
                        required=True,
                        help='The directory where the downloaded Shippable job test results are.')

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    return args


def get_raw_test_targets(test_path):
    """Scans the test directory for all the test targets that was run and get's the max runtime for each target."""
    target_times = {}

    for job_id in os.listdir(test_path):
        json_path = os.path.join(test_path, job_id, 'test.json')
        if not os.path.isfile(json_path):
            continue

        with open(json_path, mode='rb') as fd:
            test_info = json.loads(fd.read().decode('utf-8'))

        for test in test_info:
            if not test.get('path', '').endswith('.json') or 'contents' not in test.keys():
                continue

            info = json.loads(test['contents'])

            for target_name, target_info in info.get('targets', {}).items():
                target_runtime = int(target_info.get('run_time_seconds', 0))

                # If that target already is found and has a higher runtime than the current one, ignore this entry.
                if target_times.get(target_name, 0) > target_runtime:
                    continue

                target_times[target_name] = target_runtime

    return dict([(k, v) for k, v in sorted(target_times.items(), key=lambda i: i[1], reverse=True)])


def print_test_runtime(target_times):
    """Prints a nice summary of a dict containing test target names and their runtime."""
    target_name_max_len = 0
    for target_name in target_times.keys():
        target_name_max_len = max(target_name_max_len, len(target_name))

    print("%s | Seconds |" % ("Target Name".ljust(target_name_max_len),))
    print("%s | ------- |" % ("-" * target_name_max_len,))
    for target_name, target_time in target_times.items():
        print("%s | %s |" % (target_name.ljust(target_name_max_len), str(target_time).ljust(7)))


def rebalance(args):
    """Prints a nice summary of a proposed rebalanced configuration based on the downloaded Shippable result."""
    test_path = os.path.expanduser(os.path.expandvars(args.test_path))
    target_times = get_raw_test_targets(test_path)

    group_info = dict([(i, {'targets': [], 'total_time': 0}) for i in range(1, int(args.group_count) + 1)])

    # Now add each test to the group with the lowest running time.
    for target_name, target_time in target_times.items():
        index, total_time = min(enumerate([g['total_time'] for g in group_info.values()]), key=operator.itemgetter(1))
        group_info[index + 1]['targets'].append(target_name)
        group_info[index + 1]['total_time'] = total_time + target_time

    # Finally print a summary of the proposed test split.
    for group_number, test_info in group_info.items():
        print("Group %d - Total Runtime (s): %d" % (group_number, test_info['total_time']))
        print_test_runtime({n: target_times[n] for n in test_info['targets']})
        print()


if __name__ == '__main__':
    main()
