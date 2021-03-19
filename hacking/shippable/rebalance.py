#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
CLI tool that analyses a Shippable run's test result and re-balances the test targets into new groups.

Before running this script you must run download.py like:

    ./download.py https://app.shippable.com/github/<team>/<repo>/runs/<run_num> --test-results --job-number x --job-number y

Or to get all job results from a run:

    ./download.py https://app.shippable.com/github/<team>/<repo>/runs/<run_num> --test-results --all


Set the dir <team>/<repo>/<run_num> as the value of '-p/--test-path' for this script.
"""

import argparse
import json
import operator
import re
import argcomplete
import pathlib

parser = argparse.ArgumentParser(description='Re-balance CI group(s) from a downloaded results directory.')
parser.add_argument('group_count', help='The number of groups to re-balance the tests to.')
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                    help='Display more detailed info about files being read and edited.')
parser.add_argument('-p', '--test-results-path', dest='test_results_path', type=pathlib.Path, required=True,
                    help='The directory where the downloaded Shippable job test results are.')
parser.add_argument('-t', '--target-path', dest='target_path', type=pathlib.Path, required=False,
                    help='The directory where the test targets are located. If set the aliases will automatically '
                         'by rewritten with the new proposed group.')
argcomplete.autocomplete(parser)

def main():
    args = parser.parse_args()
    rebalance(args)

def get_raw_test_targets(args: argparse.Namespace, test_path:pathlib.Path):
    """Scans the test directory for all the test targets that was run and get's the max runtime for each target."""
    target_times = {}

    for job_id in test_path.iterdir():
        json_path = test_path/job_id/'test'/'testresults'/'data'

        # Some tests to do not have a data directory
        if not json_path.exists:
            continue

        json_file = json_path.glob('*integration-*.json')[0]
        if not json_file or not json_file.is_file():
            if args.verbose:
                print(f"The test json file '{json_file}' does not exist or is not a file, skipping test job run")
            continue

        with open(json_file, mode='rb') as fd:
            test_info = json.loads(fd.read().decode('utf-8'))

        targets = test_info.get('targets', {})

        for target_name, target_info in targets.items():
            target_runtime = int(target_info.get('run_time_seconds', 0))

            # If that target already is found and has a higher runtime than the current one, ignore this entry.
            if target_times.get(target_name, 0) > target_runtime:
                continue

            target_times[target_name] = target_runtime

    return dict(sorted(target_times.items(), key=lambda i: i[1], reverse=True))


def print_test_runtime(target_times):
    """Prints a nice summary of a dict containing test target names and their runtime."""
    target_name_max_len = 0
    for target_name in target_times.keys():
        target_name_max_len = max(target_name_max_len, len(target_name))

    print(f"{'Target Name'.ljust(target_name_max_len)} | Seconds |")
    print(f"{'-' * target_name_max_len} | ------- |")
    for target_name, target_time in target_times.items():
        print(f"{target_name.ljust(target_name_max_len)} | {str(target_time).ljust(7)} |")


def rebalance(args):
    """Prints a nice summary of a proposed rebalanced configuration based on the downloaded Shippable result."""
    test_path = args.test_results_path.expanduser()
    target_times = get_raw_test_targets(args, test_path)

    group_info = dict([(i, {'targets': [], 'total_time': 0}) for i in range(1, int(args.group_count) + 1)])

    # Now add each test to the group with the lowest running time.
    for target_name, target_time in target_times.items():
        index, total_time = min(enumerate([g['total_time'] for g in group_info.values()]), key=operator.itemgetter(1))
        group_info[index + 1]['targets'].append(target_name)
        group_info[index + 1]['total_time'] = total_time + target_time

    # Print a summary of the proposed test split.
    for group_number, test_info in group_info.items():
        print(f"Group {group_number} - Total Runtime (s): {test_info['total_time']}")
        print_test_runtime(dict([(n, target_times[n]) for n in test_info['targets']]))
        print()

    if args.target_path:
        target_path = args.target_path.expanduser()

        for test_root in ['test', 'tests']:  # ansible/ansible uses 'test' but collections use 'tests'.
            integration_root = target_path/test_root/'integration'/'targets'
            if integration_root.is_dir():
                if args.verbose:
                    print(f"Found test integration target dir at '{integration_root}'")
                break

        else:
            # Failed to find test integration target folder
            raise ValueError("Failed to find the test target folder on test/integration/targets or "
                             f"tests/integration/targets under '{target_path}'.")

        for group_number, test_info in group_info.items():
            for test_target in test_info['targets']:
                test_target_aliases = integration_root/test_target/'aliases'
                if not test_target_aliases.is_file():
                    if args.verbose:
                        print(f"Cannot find test target alias file at '{test_target_aliases}', skipping.")
                    continue

                with open(test_target_aliases, mode='r') as fd:
                    test_aliases = fd.readlines()

                changed = False
                for idx, line in enumerate(test_aliases):
                    group_match = re.match(r'shippable/(.*)/group(\d+)', line)
                    if group_match:
                        if int(group_match.group(2)) != group_number:
                            new_group = f"shippable/{group_match.group(1)}/group{group_number}\n"
                            if args.verbose:
                                print(f"Changing {test_target} group from '{group_match.group(0)}' to '{new_group.rstrip()}'")
                            test_aliases[idx] = new_group
                            changed = True
                            break
                else:
                    if args.verbose:
                        print(f"Test target {test_target} matches proposed group number, no changed required")

                if changed:
                    with open(test_target_aliases, mode='w') as fd:
                        fd.writelines(test_aliases)


if __name__ == '__main__':
    main()
