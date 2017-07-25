#
# Copyright (c) 2017 Ansible Project
#
# This file is part of Ansible
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


class ModuleDocFragment(object):

    # Documentation fragment for EXTRA CTL PATHS
    EXTRA_CTL_PATHS = """
options:
  extra_ctl_paths:
      description:
        - List of alternative paths to look for rabbitmqctl in
        - Only needed when running RabbitMQ as user other than root / rabbitmq
      required: false
      default: ()
      version_added: "2.4"
"""
