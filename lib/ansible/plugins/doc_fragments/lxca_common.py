# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by
# Ansible still belong to the author of the module, and may assign their
# own license to the complete work.
#
# Copyright (C) 2017 Lenovo, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#


class ModuleDocFragment(object):
    # Standard Pylxca documentation fragment
    DOCUMENTATION = r'''
author:
  - Naval Patel (@navalkp)
  - Prashant Bhosale (@prabhosa)

options:
  login_user:
    description:
    - The username for use in HTTP basic authentication.
    type: str
    required: true

  login_password:
    description:
    - The password for use in HTTP basic authentication.
    type: str
    required: true

  auth_url:
    description:
    - lxca https full web address
    type: str
    required: true

requirements:
  - pylxca

notes:
  -  Additional detail about pylxca can be found at U(https://github.com/lenovo/pylxca)
  -  Playbooks using these modules can be found at U(https://github.com/lenovo/ansible.lenovo-lxca)
  -  Check mode is not supported.
'''
