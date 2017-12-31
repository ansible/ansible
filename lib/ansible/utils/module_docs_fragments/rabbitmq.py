# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright: (c) 2017, Ansible Project


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
      version_added: "2.5"
"""
