playbook = [
    {
        'hosts': 'localhost',
        'gather_facts': 'no',
        'tasks': [
            {
                'name': 'test item being present in the output',
                'debug': 'var=item',
                'loop': [1, 2, 3]
            },
        ],
    },
]
