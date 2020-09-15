# -*- coding: utf-8 -*-

# Copyright: (c) 2019 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  hetzner_user:
    description: The username for the Robot webservice user.
    type: str
    required: yes
  hetzner_password:
    description: The password for the Robot webservice user.
    type: str
    required: yes
'''
