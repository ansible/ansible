from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback, return_values
from ansible.module_utils.network_common import to_list, EntityCollection
from ansible.module_utils.connection import Connection, exec_command

_DEVICE_CONFIGS = {}
_CONNECTION = None

enos_provider_spec = {
    'host': dict(),
    'port': dict(type='int'),
    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    'authorize': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTHORIZE']), type='bool'),
    'auth_pass': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTH_PASS']), no_log=True),
    'timeout': dict(type='int'),
    'context': dict(),
    'passwords': dict()
}

enos_argument_spec = {
    'provider': dict(type='dict', options=enos_provider_spec),
}

enos_top_spec = {
    'host': dict(removed_in_version=2.9),
    'port': dict(removed_in_version=2.9, type='int'),
    'username': dict(removed_in_version=2.9),
    'password': dict(removed_in_version=2.9, no_log=True),
    'ssh_keyfile': dict(removed_in_version=2.9, type='path'),
    'authorize': dict(type='bool'),
    'auth_pass': dict(removed_in_version=2.9, no_log=True),
    'timeout': dict(removed_in_version=2.9, type='int'),
    'context': dict(),
    'passwords': dict()
}

enos_argument_spec.update(enos_top_spec)

command_spec = {
    'command': dict(key=True),
    'prompt': dict(),
    'answer': dict()
}


def get_provider_argspec():
    return enos_provider_spec


def check_args(module):
    pass


def get_connection(module):
    global _CONNECTION
    if _CONNECTION:
        return _CONNECTION
    _CONNECTION = Connection(module)

    context = module.params['context']

    if context:
        if context == 'system':
            command = 'changeto system'
        else:
            command = 'changeto context %s' % context
        _CONNECTION.get(command)

    return _CONNECTION


def get_config(module, flags=None):
    flags = [] if flags is None else flags

    passwords = module.params['passwords']
    if passwords:
        cmd = 'more system:running-config'
    else:
        cmd = 'show running-config '
        cmd += ' '.join(flags)
        cmd = cmd.strip()

    try:
        return _DEVICE_CONFIGS[cmd]
    except KeyError:
        conn = get_connection(module)
        out = conn.get(cmd)
        cfg = to_text(out, errors='surrogate_then_replace').strip()
        _DEVICE_CONFIGS[cmd] = cfg
        return cfg


def to_commands(module, commands):
    assert isinstance(commands, list), 'argument must be of type <list>'

    transform = EntityCollection(module, command_spec)
    commands = transform(commands)

    for index, item in enumerate(commands):
        if module.check_mode and not item['command'].startswith('show'):
            module.warn('only show commands are supported when using check '
                        'mode, not executing `%s`' % item['command'])

    return commands


def run_commands(module, commands, check_rc=True):
    connection = get_connection(module)

    commands = to_commands(module, to_list(commands))

    responses = list()

    for cmd in commands:
        out = connection.get(**cmd)
        responses.append(to_text(out, errors='surrogate_then_replace'))

    return responses


def load_config(module, config):
    conn = get_connection(module)
    conn.edit_config(config)


def get_defaults_flag(module):
    rc, out, err = exec_command(module, 'show running-config ?')
    out = to_text(out, errors='surrogate_then_replace')

    commands = set()
    for line in out.splitlines():
        if line:
            commands.add(line.strip().split()[0])

    if 'all' in commands:
        return 'all'
    else:
        return 'full'

