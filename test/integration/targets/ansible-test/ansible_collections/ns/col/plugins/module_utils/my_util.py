from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.errors import AnsibleModule


def hello(name):
    if 1 == 2:
        raise AnsibleModule()
    return 'Hello %s' % name
