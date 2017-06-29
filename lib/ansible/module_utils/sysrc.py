# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Mattias Lindvall
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


BOOL_MAP = {
    True: 'YES',
    False: 'NO',
}


def get_sysrc_value_bool(value):
    '''
    Translate a bool into a string compatbile with sysrc values.

    Args:
        value: A bool value to translate.
    Returns:
        A string, either 'YES' or 'NO'.
    '''

    return BOOL_MAP[value]


def sysrc_check_change_required(module, name, value, file=None):
    '''
    Check if given name and value differs from
    what is currently set in the system using sysrc.

    Args:
        module: An instance of AnsibleModule.
        name: Name of sysrc variable.
        value: Value of sysrc variable.
        file: Filename to read from.
    Returns:
        A bool indicating if change is required.
    '''

    args = [module.get_bin_path('sysrc', required=True)]

    if file is not None:
        args.extend(['-f', file])

    args.extend(['-c', '%s=%s' % (name, value)])

    rc, out, err = module.run_command(args)

    return rc != 0


def sysrc_set(module, name, value, file=None):
    '''
    Set given name and value in the system using sysrc.

    Args:
        module: An instance of AnsibleModule.
        name: Name of sysrc variable.
        value: Value of sysrc variable.
        file: Filename to write to.
    Returns:
        rc, out, err from a run_command call.
    '''

    args = [module.get_bin_path('sysrc', required=True)]

    if file is not None:
        args.extend(['-f', file])

    args.append('%s=%s' % (name, value))

    rc, out, err = module.run_command(args)

    if rc != 0:
        module.fail_json(msg=err)

    return rc, out, err


def sysrc_update(module, name, value, file=None):
    '''
    Check if given name and value differs
    from what is currently set in the system,
    and set value if they are different.

    Args:
        module: An instance of AnsibleModule.
        name: Name of sysrc variable.
        value: Value of sysrc variable.
        file: Filename to read and write from.
    Returns:
        A bool indicating if the value was changed.
    '''

    change_required = sysrc_check_change_required(module, name, value)

    changed = False

    if change_required:
        sysrc_set(module, name, value)
        changed = True

    return changed
