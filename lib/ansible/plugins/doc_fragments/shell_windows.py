# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Windows shell documentation fragment
    # FIXME: set_module_language don't belong here but must be set so they don't fail when someone
    #  get_option('set_module_language') on this plugin
    DOCUMENTATION = """
options:
  async_dir:
    description:
    - Directory in which ansible will keep async job information.
    - Before Ansible 2.8, this was set to C(remote_tmp + "\\.ansible_async").
    default: '%USERPROFILE%\\.ansible_async'
    ini:
    - section: powershell
      key: async_dir
    vars:
    - name: ansible_async_dir
    version_added: '2.8'
  remote_tmp:
    description:
    - Temporary directory to use on targets when copying files to the host.
    default: '%TEMP%'
    ini:
    - section: powershell
      key: remote_tmp
    vars:
    - name: ansible_remote_tmp
  set_module_language:
    description:
    - Controls if we set the locale for moduels when executing on the
      target.
    - Windows only supports C(no) as an option.
    type: bool
    default: 'no'
    choices:
    - 'no'
  environment:
    description:
    - Dictionary of environment variables and their values to use when
      executing commands.
    type: dict
    default: {}
"""
