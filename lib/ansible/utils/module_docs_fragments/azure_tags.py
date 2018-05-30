# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
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
#


class ModuleDocFragment(object):

    # Azure doc fragment
    DOCUMENTATION = '''
options:
    tags:
        description:
            - >
              Dictionary of string:string pairs to assign as metadata to the object.
              Metadata tags on the object will be updated with any provided values. To remove tags set append_tags option to false.
    append_tags:
        description:
            - Use to control if tags field is canonical or just appends to existing tags.
              When canonical, any tags not found in the tags parameter will be removed from the object's metadata.
        type: bool
        default: 'yes'
    '''
