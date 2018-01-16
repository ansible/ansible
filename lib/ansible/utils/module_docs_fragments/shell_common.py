# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # common shelldocumentation fragment
    DOCUMENTATION = """
options:
  remote_temp:
    description:
      - Temporary directory to use on targets when executing tasks.
    default: '~/.ansible/tmp'
    env: [{name: ANSIBLE_REMOTE_TEMP}]
    ini:
      - section: defaults
        key: remote_tmp
    vars:
      - name: ansible_remote_tmp
  system_temps:
    description:
       - List of valid system temporary directories for Ansible to choose when it cannot use ``remote_temp``, normally due to permission issues.
    default: [ /var/tmp, /tmp ]
    type: list
    env: [{name: ANSIBLE_SYSTEM_TMPS}]
    ini:
      - section: defaults
        key: system_tmps
    vars:
      - name: ansible_system_tmps
  async_dir:
    description:
       - Directory in which ansible will keep async job inforamtion
    default: '~/.ansible_async'
    env: [{name: ANSIBLE_ASYNC_DIR}]
    ini:
      - section: defaults
        key: async_dir
    vars:
      - name: ansible_async_dir
  set_module_language:
    default: False
    description: Controls if we set locale for modules when executing on the target.
    env:
      - name: ANSIBLE_MODULE_SET_LOCALE
    ini:
      - section: defaults
        key: module_set_locale
    type: boolean
    vars:
      - name: ansible_module_set_locale
  module_language:
    description:
      - "If 'set_module_language' is true, this is the language language/locale setting to use for modules when they execute on the target."
      - "Defaults to match the controller's settings."
    default: "{{CONTROLLER_LANG}}"
    env:
      - name: ANSIBLE_MODULE_LANG
    ini:
      - section: defaults
        key: module_lang
    vars:
      - name: ansible_module_lang
  environment:
    type: dict
    default: {}
    description:
      - dictionary of environment variables and their values to use when executing commands.
  admin_users:
    type: list
    default: ['root', 'toor', 'admin']
    description:
      - list of users to be expected to have admin privileges, for BSD you might want to add 'toor' for windows 'Administrator'.
    env:
      - name: ANSIBLE_ADMIN_USERS
    ini:
      - section: defaults
        key: admin_users
    vars:
      - name: ansible_admin_users
  allow_world_readable_temp:
    type: boolean
    description:
        - This makes the temporary files created on the machine to be world readable and will issue a warning instead of failing the task.
        - It is useful when becoming an unprivileged user.
    ini:
      - section: defaults
        key: allow_world_readable_tmpfiles
    vars:
      - name: ansible_world_readable_tmpfiles
    version_added: "2.1"
"""
