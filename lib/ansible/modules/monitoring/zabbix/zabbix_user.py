#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: zabbix_user
short_description: Create/Update/Delete Zabbix users
description:
    - This module allows you to create, modify and delete Zabbix users.
version_added: "2.9"
author:
    - Ruben Tsirunyan (@rubentsirunyan)
requirements:
    - zabbix-api

options:
    username:
        type: str
        description:
            - Username of the user.
            - Term alias is used in Zabbix API
        aliases:
            - alias
        required: true
    state:
        type: str
        description:
            - Desired state of the user.
            - On C(present), it will create a user if it does not exist or update the existing user if the associated data is different.
            - On C(absent), it will remove the user if it exists.
        choices:
            - present
            - absent
        default: 'present'
        required: true
    type:
        type: str
        description:
            - Type of the user.
        choices:
            - zabbix_user
            - zabbix_admin
            - zabbix_superadmin
        default: zabbix_user
    first_name:
        type: str
        description:
            - First name of the User.
        aliases:
            - name
    last_name:
        type: str
        description:
            - Last name of the user.
        aliases:
            - surname
    groups:
        type: list
        description:
            -  User groups to add the user to.
    password:
        type: str
        description:
            - User's password.
    language:
        type: str
        description:
            -  Language code of the user's language.
        choices:
            - en_GB
        default: en_GB
    theme:
        type: 'str'
        description:
            - User's theme.
        choices:
            - default
            - blue-theme
            - dark-theme
        default: default
    auto_login:
        type: bool
        description:
            - Whether to enable auto-login or no.
        default: false
    auto_logout:
        type: str
        description:
            - User session life time.
            - Accepts seconds and time unit with suffix.
            - If set to 0s, the session will never expire.
        default: 0s
    refresh:
        type: str
        description:
            - Automatic refresh period.
            - Accepts seconds and time unit with suffix.
        default: 30s
    rows_per_page:
        type: int
        description:
            - Amount of object rows to show per page.
        default: 50
    redirect_url:
        type: str
        description:
            - URL of the page to redirect the user to after logging in.
    medias:
        type: list
        description:
            - Medias to create for the user.
        suboptions:
            mediatype:
                type: str
                description:
                    - Name of the media type used by the media.
                required: true
            send_to:
                type: raw
                description:
                    - Address, user name or other identifier of the recipient.
                    - Type is 'list' (or 'str' when there is only one element) when >= Zabbix 4.0
                    - Type is 'str' when < Zabbix 4.0
                required: true
            status:
                type: str
                description:
                    -  Whether the media is enabled.
                choices: [enabled, disabled]
                default: enabled
            severities:
                type: list
                description:
                    - Trigger severities to send notifications about.
                    - Choose one or more of
                    - C(not_classified), C(information), C(warning), C(average), C(high), C(disaster)
                default:
                    - not_classified
                    - information
                    - warning
                    - average
                    - high
                    - disaster
            period:
                type: str
                description:
                    - Time when the notifications can be sent as a time period or user macros separated by a semicolon.
                    - To set a time period, the following format has to be used: C(d-d,hh:mm-hh:mm),
                    - where the symbols stand for the following:
                    - d - Day of the week: C(1 - Monday, 2 - Tuesday, ... , 7 - Sunday)
                    - hh - Hours: C(00-24)
                    - mm - Minutes: C(00-59)
                    - You can specify more than one time period using a semicolon C(;) separator: C(d-d,hh:mm-hh:mm;d-d,hh:mm-hh:mm...)
                default: 1-7,00:00-24:00
extends_documentation_fragment:
    - zabbix

'''

RETURN = '''
'''

EXAMPLES = '''
'''


import traceback


from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.common.text.converters import container_to_bytes


try:
    from zabbix_api import ZabbixAPI
    HAS_ZABBIX_API = True
except ImportError:
    ZBX_IMP_ERR = traceback.format_exc()
    HAS_ZABBIX_API = False


def to_numeric_value(value, strs):
    return strs.get(value)


def check_user_password(module, zbx, user_id, username, password):
    try:
        zbx.login(username, password)
        return True
    except Exception as e:
        return False

def get_mediatype_id_by_name(module, zbx, mediatype_name):
    """Returns mediatype ID if exists

    Args:
        module: AnsibleModule object
        zbx: ZabbixAPI object
        mediatype_name: Zabbix user name

    Returns:
        id of the mediatype if mediatype exists. Fails the module otherwise.
    """
    try:
        mediatype_list = zbx.mediatype.get({
            'output': 'extend',
            'filter': {'description': [mediatype_name]}
        })
        if len(mediatype_list) < 1:
            module.fail_json(msg="Mediatype '{mediatype_name}' does not exist".format(mediatype_name=mediatype_name))
        else:
            return mediatype_list[0]['mediatypeid']
    except Exception as e:
        module.fail_json(msg="Failed to get ID of the mediatype '{mediatype_name}': {e}".format(mediatype_name=mediatype_name, e=e))


def get_group_id_by_name(module, zbx, group_name):
    """Returns user group ID if exists

    Args:
        module: AnsibleModule object
        zbx: ZabbixAPI object
        group_name: Zabbix user group name

    Returns:
        id of the group if group exists. Fails the module otherwise.
    """
    try:
        group_list = zbx.usergroup.get({
            'output': 'extend',
            'filter': {'name': [group_name]}
        })
        if len(group_list) < 1:
            module.fail_json(msg="User group '{group_name}' does not exist".format(group_name=group_name))
        else:
            return group_list[0]['usrgrpid']
    except Exception as e:
        module.fail_json(msg="Failed to get ID of the user group '{group_name}': {e}".format(group_name=group_name, e=e))


def construct_media_severity(module, zbx, severities):
    """Converts the list of desired severiries provided
    by the user to an integer suitable for Zabbix API.

    Severities are stored in binary form with each bit
    representing the corresponding severity.
    For example, 12 equals 1100 in binary and means,
    that notifications will be sent from triggers with
    severities 'warning' and 'average'.

    Args:
        module: AnsibleModule object
        zbx: ZabbixAPI object
        severities (list): List of severities

    Returns:
        int: Number suitable for Zabbix API
    """

    severity_list = [
        'not_classified',
        'information',
        'warning',
        'average',
        'high',
        'disaster'
    ]

    binary_repr = ''
    for severity in severity_list:
        if severity in severities:
            binary_repr = binary_repr + '1'
        else:
            binary_repr = binary_repr + '0'

    return int(binary_repr, 2)


def construct_media_parameters(module, zbx, medias):
    """Translates data for parameter 'medias'
    to a format suitable for Zabbix API.

    Args:
        medias (list): List of medias passed to the module.

    Yields:
        (dict): A dictionary of media object
        in the format suitable for Zabbix API:
    """
    for media in medias:
        send_to = media['send_to']
        if float(zbx.api_version().rsplit('.', 1)[0]) >= 4.0:
            if isinstance(send_to, str):
                send_to = [send_to]

        yield dict(
            mediatypeid=get_mediatype_id_by_name(module, zbx, media['mediatype']),
            sendto=send_to,
            active=to_numeric_value(media['status'],
                                    {'enabled': '0',
                                     'disabled': '1'}),
            severity=str(construct_media_severity(module, zbx, media['severities'])),
            period=media['period']
        )


def construct_group_parameters(module, zbx, groups):
    """Translates data for parameter 'groups'
    to a format suitable for Zabbix API.

    Args:
        groups: List of group names.

    Yields:
        (dict): A dictionary in the following format: {'usrgrpid': `group_id`}.
    """
    if groups is None:
        raise StopIteration()
        yield
    if len(groups) < 1:
            module.fail_json(msg="Parameter 'groups' cannot be empty")
    for group in groups:
        group_id = get_group_id_by_name(module, zbx, group)
        yield {'usrgrpid': group_id}


def construct_parameters(module, zbx, **kwargs):
    """Translates data to a format suitable for Zabbix API.

    Args:
        **kwargs: Arguments passed to the module.

    Returns:
        A dictionary of arguments that are in a format
        that is understandable by Zabbix API.
    """

    medias = [media for media in construct_media_parameters(module, zbx, kwargs['medias'])]
    groups = [group for group in construct_group_parameters(module, zbx, kwargs['groups'])]

    return dict(
        alias=kwargs['username'],
        type=to_numeric_value(kwargs['type'],
                              {'zabbix_user': '1',
                               'zabbix_admin': '2',
                               'zabbix_superadmin': '3'}),
        name=kwargs['first_name'],
        surname=kwargs['last_name'],
        usrgrps=groups,
        passwd=kwargs['password'],
        lang=kwargs['language'],
        theme=kwargs['theme'],
        autologin=to_numeric_value(str(kwargs['auto_login']),
                                             {'False': '0',
                                              'True': '1'}),
        autologout=kwargs['auto_logout'],
        refresh=kwargs['refresh'],
        rows_per_page=str(kwargs['rows_per_page']),
        url=kwargs['redirect_url'],
        user_medias=medias
    )


def check_if_user_exists(module, zbx, username):
    """Checks if user exists.

    Args:
        module: AnsibleModule object
        zbx: ZabbixAPI object
        name: Zabbix user name

    Returns:
        Tuple of (True, `id of the user`) if user exists, (False, None) otherwise
    """
    try:
        user_list = zbx.user.get({
            'output': 'extend',
            'filter': {'alias': [username]}
        })
        if len(user_list) < 1:
            return False, None
        else:
            return True, user_list[0]['userid']
    except Exception as e:
        module.fail_json(msg="Failed to get the ID of the user '{username}': {e}".format(username=username, e=e))


def diff(existing, new):
    """Constructs the diff for Ansible's --diff option.

    Args:
        existing (dict): Existing user data.
        new (dict): New user data.

    Returns:
        A dictionary like {'before': existing, 'after': new}
        with filtered empty values.
    """
    before = {}
    after = {}
    for key in new:
        if key == 'user_medias':
            before['user_medias'] = existing['medias']
        # elif key == 'passwd':
            # continue
        else:
            before[key] = existing[key]
        if new[key] is None:
            after[key] = ''
        else:
            after[key] = new[key]
    return {'before': before, 'after': after}


def get_update_params(module, zbx, user_id, check_password, **kwargs):
    """Filters only the parameters that are different and need to be updated.

    Args:
        module: AnsibleModule object.
        zbx: ZabbixAPI object.
        user_id (int): ID of the user to be updated.
        **kwargs: Parameters for the new user.

    Returns:
        A tuple where the first element is a dictionary of parameters
        that need to be updated and the second one is a dictionary
        returned by diff() function with
        existing user data and new params passed to it.
    """
    existing_user = container_to_bytes(zbx.user.get({
        'output': 'extend',
        'selectMedias': 'extend',
        'selectUsrgrps': 'extend',
        'userids': [user_id]
    })[0])

    params_to_update = {}

    new_medias = sorted(kwargs['user_medias'])
    existing_medias = sorted(existing_user['medias'])

    for media in existing_medias:
        del media['userid']
        del media['mediaid']

    if new_medias != existing_medias:
        params_to_update['user_medias'] = new_medias

    password_valid = check_user_password(module, check_password, user_id,
                                         kwargs['alias'], kwargs['passwd'])

    if not password_valid:
        params_to_update['passwd'] = kwargs['passwd']
        existing_user['passwd'] = ''
    else:
        existing_user['passwd'] = kwargs['passwd']

    existing_groups = []
    for group in existing_user['usrgrps']:
        existing_groups.append(dict(usrgrpid=group['usrgrpid']))
    existing_user['usrgrps'] = existing_groups

    for key in kwargs:
        if key in ('user_medias', 'passwd'):
            continue
        if (not (kwargs[key] is None and existing_user[key] == '')) and kwargs[key] != existing_user[key]:
            params_to_update[key] = kwargs[key]

    return params_to_update, diff(existing_user, kwargs)


def delete_user(module, zbx, user_id):
    try:
        return zbx.user.delete([user_id])['userids'][0]
    except Exception as e:
        module.fail_json(msg="Failed to delete user '{username}': {e}".format(username=kwargs['alias'], e=e))


def update_user(module, zbx, username, **kwargs):
    try:
        return zbx.user.update(kwargs)['userids'][0]
    except Exception as e:
        module.fail_json(msg="Failed to update user '{username}': {e}".format(username=username, e=e))


def create_user(module, zbx, **kwargs):
    try:
        return zbx.user.create(kwargs)['userids'][0]
    except Exception as e:
        module.fail_json(msg="Failed to create user '{username}': {e}".format(username=kwargs['alias'], e=e))


def main():
    argument_spec = dict(
        server_url=dict(type='str', required=True, aliases=['url']),
        login_user=dict(type='str', required=True),
        login_password=dict(type='str', required=True, no_log=True),
        http_login_user=dict(type='str', required=False, default=None),
        http_login_password=dict(type='str', required=False, default=None, no_log=True),
        validate_certs=dict(type='bool', required=False, default=True),
        timeout=dict(type='int', default=10),
        username=dict(type='str', required=True, aliases=['alias']),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        type=dict(
            type='str',
            required=False,
            choices=['zabbix_user', 'zabbix_admin', 'zabbix_superadmin'],
            default='zabbix_user'
        ),
        first_name=dict(type='str', required=False, aliases=['name']),
        last_name=dict(type='str', required=False, aliases=['surname']),
        groups=dict(type='list', required=False),
        password=dict(type='str', required=False, no_log=True),
        language=dict(type='str', default='en_GB', required=False),
        theme=dict(
            type='str',
            default='default',
            choices=['default','blue-theme','dark-theme'],
            required=False
        ),
        auto_login=dict(type='bool', default=False, required=False),
        auto_logout=dict(type='str', default='0s', required=False),
        refresh=dict(type='str', default='30s', required=False),
        rows_per_page=dict(type='int', default=50, required=False),
        redirect_url=dict(type='str', default='', required=False),
        medias=dict(
            type='list',
            required=False,
            default=[],
            elements='dict',
            options=dict(
                mediatype=dict(type='str', required=True),
                send_to=dict(type='raw', required=True),
                status=dict(
                    type='str',
                    required=False,
                    default='enabled',
                    choices=['enabled', 'disabled']
                ),
                severities=dict(
                    type='list',
                    required=False,
                    default=[
                        'not_classified',
                        'information',
                        'warning',
                        'average',
                        'high',
                        'disaster'
                    ]
                ),
                period=dict(type='str', required=False, default='1-7,00:00-24:00')
            )
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ['state', 'present', ['groups', 'password']]
        ],
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg=missing_required_lib('zabbix-api', url='https://pypi.org/project/zabbix-api/'), exception=ZBX_IMP_ERR)

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    timeout = module.params['timeout']
    username = module.params['username']
    state = module.params['state']
    type = module.params['type']
    first_name = module.params['first_name']
    last_name = module.params['last_name']
    groups = module.params['groups']
    password = module.params['password']
    language = module.params['language']
    theme = module.params['theme']
    auto_login = module.params['auto_login']
    auto_logout = module.params['auto_logout']
    refresh = module.params['refresh']
    rows_per_page = module.params['rows_per_page']
    redirect_url = module.params['redirect_url']
    medias = module.params['medias']

    zbx = None

    # login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                        validate_certs=validate_certs)
        check_password = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                        validate_certs=validate_certs)
        zbx.login(login_user, login_password)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    user_exists, user_id = check_if_user_exists(module, zbx, username)

    parameters = construct_parameters(
        module, zbx,
        username=username,
        type=type,
        first_name=first_name,
        last_name=last_name,
        groups=groups,
        password=password,
        language=language,
        theme=theme,
        auto_login=auto_login,
        auto_logout=auto_logout,
        refresh=refresh,
        rows_per_page=rows_per_page,
        redirect_url=redirect_url,
        medias=medias
    )

    if user_exists:
        if state == 'absent':
            if module.check_mode:
                module.exit_json(
                    changed=True,
                    msg="User {username} would have been deleted. ID: {_id}".format(
                        username=username,
                        _id=user_id
                    )
                )
            user_id = delete_user(module, zbx, user_id)
            module.exit_json(
                changed=True,
                msg="User {username} has been deleted. ID: {_id}".format(
                    username=username,
                    _id=user_id
                )
            )
        else:
            params_to_update, diff = get_update_params(module, zbx, user_id, check_password, **parameters)
            if params_to_update == {}:
                module.exit_json(
                    changed=False,
                    msg="User {username} is up to date. ID: {_id}".format(
                        username=username,
                        _id=user_id
                    )
                )
            else:
                if module.check_mode:
                    module.exit_json(
                        changed=True,
                        diff=diff,
                        msg="User {username} would have been updated.ID: {_id}".format(
                            username=username,
                            _id=user_id
                        )
                    )
                user_id = update_user(
                    module, zbx, username,
                    userid=user_id,
                    **params_to_update
                )
                module.exit_json(
                    changed=True,
                    diff=diff,
                    msg="User {username} has been updated. ID: {_id}".format(
                        username=username,
                        _id=user_id
                    )
                )
    else:
        if state == "absent":
            module.exit_json(changed=False)
        else:
            if module.check_mode:
                module.exit_json(
                    changed=True,
                    msg="User {username} would have been created. ID: {_id}".format(
                        username=username,
                        _id=user_id
                    )
                )
            user_id = create_user(module, zbx, **parameters)
            module.exit_json(
                changed=True,
                msg="User {username} has been created: ID: {_id}".format(
                    username=username,
                    _id=user_id
                )
            )


if __name__ == '__main__':
    main()
