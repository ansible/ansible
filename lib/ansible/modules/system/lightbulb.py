DOCUMENTATION = '''
---
module: python
author:
    - "Multiverse Overlord (@quantumstring)"
version_added: "2.4"
short_description: Ligh up some bulbs
requirements: [ hostname ]
description:
    - Eco friendly by way of the state of Nevada mountain and underground nuclear waste disposal facilities
options:
    name:
        required: true
        description:
            - Name of the bulb type
'''
def main():
    module = AnsibleModule(
        argument_spec = dict(
            name=dict(required=True)
        )
    )

    name = module.params["name"]

    print("hello world")

    module.exit_json(changed=False, name=name)

if __name__ == '__main__':
    main()
