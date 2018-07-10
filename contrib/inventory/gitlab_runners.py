#!/usr/bin/env python

# (c) 2017, Stefan Heitmueller <stefan.heitmueller@gmx.com>
#
# This file is part of Ansible,
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Installation
# ------------
#
# ! Your Runners description needs to match the hostname of the runner !
#
# - copy this file to /etc/ansible and make it executable (chmod +x)
# - pip install python-gitlab
# - modify /etc/ansible/gitlab_runner.ini to your needs
#
# Usage:
# All runners are in "runners" hostgroup:
#   ansible -i /etc/ansible/gitlab_runner.py runners -m ping
# You'll also get hostgroups for your Gitlab tags:
#   ansible -i /etc/ansible/gitlab_runner.py my_gitlab_tagged_runners -m ping
#

import ConfigParser
import os
import json
import re
import gitlab


class GitlabRunnersInventory(object):

    def __init__(self):
        """ Main execution path """

        self.read_settings()

        # initiate gitlab api connection
        self.gl = gitlab.Gitlab.from_config('ansible', os.path.dirname(os.path.realpath(__file__)) + '/gitlab_runners.ini')

        # build json output for ansible containing hostgroup "runners"
        self.data = {"runners": []}

        # get runners (with filter, if set in ini file)
        try:
            self.runners = self.gl.runners.all(scope=self.runners_filter)
        except:
            self.runners = self.gl.runners.all()

        for self.runner in self.runners:
            try:
                self.runner_hostname = re.sub(self.runners_regex, '', self.gl.runners.get(self.runner.id).description)
            except:
                self.runner_hostname = self.gl.runners.get(self.runner.id).description

            self.runner_tag_list = self.gl.runners.get(self.runner.id).tag_list

            # add hostgroup for each tag
            for self.tag in self.runner_tag_list:
                if self.tag not in self.data:
                    self.data.update({self.tag: []})
                # append to hostgroup "tag_list"
                if self.runner_hostname not in self.data[self.tag]:
                    self.data[self.tag].append(self.runner_hostname)

            # append to hostgroup "runners"
            if self.runner_hostname not in self.data["runners"]:
                self.data["runners"].append(self.runner_hostname)

        # finally print json
        print(json.dumps(self.data, indent=4))

    def read_settings(self):
        """ Reads the settings from the gitlab_runners.ini file """

        config = ConfigParser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/gitlab_runners.ini')

        if config.has_option('ansible', 'host_regex'):
            self.runners_regex = config.get('ansible', 'host_regex')
        if config.has_option('ansible', 'host_filter'):
            self.runners_filter = config.get('ansible', 'host_filter')


if __name__ == "__main__":
    GitlabRunnersInventory()
