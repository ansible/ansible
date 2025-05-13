from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule


def main():
    m = AnsibleModule(argument_spec=dict(
        key_count=dict(default=100, type=int),
        depth=dict(default=5, type=int),
        as_facts=dict(default=False, type='bool')
    ))

    kc = m.params['key_count']
    depth = m.params['depth']
    as_facts = m.params['as_facts']

    rootdict = dict()
    thedict = rootdict

    for d in range(1, depth):
        for i in range(1, kc):
            thedict[f'key{i}'] = f'value{i}'
        newdict = dict()
        thedict[f'sub{d}'] = newdict
        thedict = newdict

    if as_facts:
        modout = dict(ansible_facts=rootdict)
    else:
        modout = dict(res=rootdict)

    m.exit_json(**modout)


if __name__ == '__main__':
    main()
