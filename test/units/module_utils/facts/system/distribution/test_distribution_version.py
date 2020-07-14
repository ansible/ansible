# -*- coding: utf-8 -*-
# Copyright: (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import glob
import json
import os
import pytest
from itertools import product

from ansible.module_utils.six.moves import builtins

# the module we are actually testing (sort of)
from ansible.module_utils.facts.system.distribution import DistributionFactCollector

# to generate the testcase data, you can use the script gen_distribution_version_testcase.py in hacking/tests
TESTSETS = []

for datafile in glob.glob(os.path.join(os.path.dirname(__file__), 'fixtures/*.json')):
    with open(os.path.join(os.path.dirname(__file__), '%s' % datafile)) as f:
        TESTSETS.append(json.loads(f.read()))


@pytest.mark.parametrize("stdin, testcase", product([{}], TESTSETS), ids=lambda x: x.get('name'), indirect=['stdin'])
def test_distribution_version(am, mocker, testcase):
    """tests the distribution parsing code of the Facts class

    testsets have
    * a name (for output/debugging only)
    * input files that are faked
      * those should be complete and also include "irrelevant" files that might be mistaken as coming from other distributions
      * all files that are not listed here are assumed to not exist at all
    * the output of ansible.module_utils.distro.linux_distribution() [called platform.dist() for historical reasons]
    * results for the ansible variables distribution* and os_family

    """

    # prepare some mock functions to get the testdata in
    def mock_get_file_content(fname, default=None, strip=True):
        """give fake content if it exists, otherwise pretend the file is empty"""
        data = default
        if fname in testcase['input']:
            # for debugging
            print('faked %s for %s' % (fname, testcase['name']))
            data = testcase['input'][fname].strip()
        if strip and data is not None:
            data = data.strip()
        return data

    def mock_get_uname(am, flags):
        if '-v' in flags:
            return testcase.get('uname_v', None)
        elif '-r' in flags:
            return testcase.get('uname_r', None)
        else:
            return None

    def mock_file_exists(fname, allow_empty=False):
        if fname not in testcase['input']:
            return False

        if allow_empty:
            return True
        return bool(len(testcase['input'][fname]))

    def mock_platform_system():
        return testcase.get('platform.system', 'Linux')

    def mock_platform_release():
        return testcase.get('platform.release', '')

    def mock_platform_version():
        return testcase.get('platform.version', '')

    def mock_distro_name():
        return testcase['distro']['name']

    def mock_distro_id():
        return testcase['distro']['id']

    def mock_distro_version(best=False):
        if best:
            return testcase['distro']['version_best']
        return testcase['distro']['version']

    def mock_distro_codename():
        return testcase['distro']['codename']

    def mock_distro_os_release_info():
        return testcase['distro']['os_release_info']

    def mock_distro_lsb_release_info():
        return testcase['distro']['lsb_release_info']

    def mock_open(filename, mode='r'):
        if filename in testcase['input']:
            file_object = mocker.mock_open(read_data=testcase['input'][filename]).return_value
            file_object.__iter__.return_value = testcase['input'][filename].splitlines(True)
        else:
            file_object = real_open(filename, mode)
        return file_object

    def mock_os_path_is_file(filename):
        if filename in testcase['input']:
            return True
        return False

    mocker.patch('ansible.module_utils.facts.system.distribution.get_file_content', mock_get_file_content)
    mocker.patch('ansible.module_utils.facts.system.distribution.get_uname', mock_get_uname)
    mocker.patch('ansible.module_utils.facts.system.distribution._file_exists', mock_file_exists)
    mocker.patch('ansible.module_utils.distro.name', mock_distro_name)
    mocker.patch('ansible.module_utils.distro.id', mock_distro_id)
    mocker.patch('ansible.module_utils.distro.version', mock_distro_version)
    mocker.patch('ansible.module_utils.distro.codename', mock_distro_codename)
    mocker.patch(
        'ansible.module_utils.common.sys_info.distro.os_release_info',
        mock_distro_os_release_info)
    mocker.patch(
        'ansible.module_utils.common.sys_info.distro.lsb_release_info',
        mock_distro_lsb_release_info)
    mocker.patch('os.path.isfile', mock_os_path_is_file)
    mocker.patch('platform.system', mock_platform_system)
    mocker.patch('platform.release', mock_platform_release)
    mocker.patch('platform.version', mock_platform_version)

    real_open = builtins.open
    mocker.patch.object(builtins, 'open', new=mock_open)

    # run Facts()
    distro_collector = DistributionFactCollector()
    generated_facts = distro_collector.collect(am)

    # compare with the expected output

    # testcase['result'] has a list of variables and values it expects Facts() to set
    for key, val in testcase['result'].items():
        assert key in generated_facts
        msg = 'Comparing value of %s on %s, should: %s, is: %s' %\
            (key, testcase['name'], val, generated_facts[key])
        assert generated_facts[key] == val, msg
