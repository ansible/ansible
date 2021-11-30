# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Say hello in Ukrainian."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec={
            'name': {'default': 'світ'},
        },
    )
    name = module.params['name']

    module.exit_json(
        msg='Greeting {name} completed.'.
        format(name=name.title()),
        greeting='Привіт, {name}!'.format(name=name),
    )


if __name__ == '__main__':
    main()
