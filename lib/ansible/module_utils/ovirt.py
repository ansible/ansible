# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

import inspect
import os
import time

from abc import ABCMeta, abstractmethod
from datetime import datetime
from distutils.version import LooseVersion

from ansible.module_utils.cloud import CloudRetry
from ansible.module_utils.common._collections_compat import Mapping

try:
    from enum import Enum  # enum is a ovirtsdk4 requirement
    import ovirtsdk4 as sdk
    import ovirtsdk4.version as sdk_version
    import ovirtsdk4.types as otypes
    HAS_SDK = LooseVersion(sdk_version.VERSION) >= LooseVersion('4.3.0')
except ImportError:
    HAS_SDK = False


BYTES_MAP = {
    'kib': 2**10,
    'mib': 2**20,
    'gib': 2**30,
    'tib': 2**40,
    'pib': 2**50,
}


def check_sdk(module):
    if not HAS_SDK:
        module.fail_json(
            msg='ovirtsdk4 version 4.3.0 or higher is required for this module'
        )


def get_dict_of_struct(struct, connection=None, fetch_nested=False, attributes=None):
    """
    Convert SDK Struct type into dictionary.
    """
    res = {}

    def remove_underscore(val):
        if val.startswith('_'):
            val = val[1:]
            remove_underscore(val)
        return val

    def convert_value(value):
        nested = False

        if isinstance(value, sdk.Struct):
            if not fetch_nested or not value.href:
                return get_dict_of_struct(value)

            # Fetch nested values of struct:
            try:
                value = connection.follow_link(value)
            except sdk.Error:
                value = None
            nested_obj = dict(
                (attr, convert_value(getattr(value, attr)))
                for attr in attributes if getattr(value, attr, None)
            )
            nested_obj['id'] = getattr(value, 'id', None)
            nested_obj['href'] = getattr(value, 'href', None)
            return nested_obj
        elif isinstance(value, Enum) or isinstance(value, datetime):
            return str(value)
        elif isinstance(value, list) or isinstance(value, sdk.List):
            if isinstance(value, sdk.List) and fetch_nested and value.href:
                try:
                    value = connection.follow_link(value)
                    nested = True
                except sdk.Error:
                    value = []

            ret = []
            for i in value:
                if isinstance(i, sdk.Struct):
                    if not nested:
                        ret.append(get_dict_of_struct(i))
                    else:
                        nested_obj = dict(
                            (attr, convert_value(getattr(i, attr)))
                            for attr in attributes if getattr(i, attr, None)
                        )
                        nested_obj['id'] = getattr(i, 'id', None)
                        ret.append(nested_obj)
                elif isinstance(i, Enum):
                    ret.append(str(i))
                else:
                    ret.append(i)
            return ret
        else:
            return value

    if struct is not None:
        for key, value in struct.__dict__.items():
            if value is None:
                continue

            key = remove_underscore(key)
            res[key] = convert_value(value)

    return res


def engine_version(connection):
    """
    Return string representation of oVirt engine version.
    """
    engine_api = connection.system_service().get()
    engine_version = engine_api.product_info.version
    return '%s.%s' % (engine_version.major, engine_version.minor)


def create_connection(auth):
    """
    Create a connection to Python SDK, from task `auth` parameter.
    If user doesnt't have SSO token the `auth` dictionary has following parameters mandatory:
     url, username, password

    If user has SSO token the `auth` dictionary has following parameters mandatory:
     url, token

    The `ca_file` parameter is mandatory in case user want to use secure connection,
    in case user want to use insecure connection, it's mandatory to send insecure=True.

    :param auth: dictionary which contains needed values for connection creation
    :return: Python SDK connection
    """

    url = auth.get('url')
    if url is None and auth.get('hostname') is not None:
        url = 'https://{0}/ovirt-engine/api'.format(auth.get('hostname'))

    return sdk.Connection(
        url=url,
        username=auth.get('username'),
        password=auth.get('password'),
        ca_file=auth.get('ca_file', None),
        insecure=auth.get('insecure', False),
        token=auth.get('token', None),
        kerberos=auth.get('kerberos', None),
        headers=auth.get('headers', None),
    )


def convert_to_bytes(param):
    """
    This method convert units to bytes, which follow IEC standard.

    :param param: value to be converted
    """
    if param is None:
        return None

    # Get rid of whitespaces:
    param = ''.join(param.split())

    # Convert to bytes:
    if len(param) > 3 and param[-3].lower() in ['k', 'm', 'g', 't', 'p']:
        return int(param[:-3]) * BYTES_MAP.get(param[-3:].lower(), 1)
    elif param.isdigit():
        return int(param) * 2**10
    else:
        raise ValueError(
            "Unsupported value(IEC supported): '{value}'".format(value=param)
        )


def follow_link(connection, link):
    """
    This method returns the entity of the element which link points to.

    :param connection: connection to the Python SDK
    :param link: link of the entity
    :return: entity which link points to
    """

    if link:
        return connection.follow_link(link)
    else:
        return None


def get_link_name(connection, link):
    """
    This method returns the name of the element which link points to.

    :param connection: connection to the Python SDK
    :param link: link of the entity
    :return: name of the entity, which link points to
    """

    if link:
        return connection.follow_link(link).name
    else:
        return None


def equal(param1, param2, ignore_case=False):
    """
    Compare two parameters and return if they are equal.
    This parameter doesn't run equal operation if first parameter is None.
    With this approach we don't run equal operation in case user don't
    specify parameter in their task.

    :param param1: user inputted parameter
    :param param2: value of entity parameter
    :return: True if parameters are equal or first parameter is None, otherwise False
    """
    if param1 is not None:
        if ignore_case:
            return param1.lower() == param2.lower()
        return param1 == param2
    return True


def search_by_attributes(service, list_params=None, **kwargs):
    """
    Search for the entity by attributes. Nested entities don't support search
    via REST, so in case using search for nested entity we return all entities
    and filter them by specified attributes.
    """
    list_params = list_params or {}
    # Check if 'list' method support search(look for search parameter):
    if 'search' in inspect.getargspec(service.list)[0]:
        res = service.list(
            search=' and '.join('{0}={1}'.format(k, v) for k, v in kwargs.items()),
            **list_params
        )
    else:
        res = [
            e for e in service.list(**list_params) if len([
                k for k, v in kwargs.items() if getattr(e, k, None) == v
            ]) == len(kwargs)
        ]

    res = res or [None]
    return res[0]


def search_by_name(service, name, **kwargs):
    """
    Search for the entity by its name. Nested entities don't support search
    via REST, so in case using search for nested entity we return all entities
    and filter them by name.

    :param service: service of the entity
    :param name: name of the entity
    :return: Entity object returned by Python SDK
    """
    # Check if 'list' method support search(look for search parameter):
    if 'search' in inspect.getargspec(service.list)[0]:
        res = service.list(
            search="name={name}".format(name=name)
        )
    else:
        res = [e for e in service.list() if e.name == name]

    if kwargs:
        res = [
            e for e in service.list() if len([
                k for k, v in kwargs.items() if getattr(e, k, None) == v
            ]) == len(kwargs)
        ]

    res = res or [None]
    return res[0]


def get_entity(service, get_params=None):
    """
    Ignore SDK Error in case of getting an entity from service.
    """
    entity = None
    try:
        if get_params is not None:
            entity = service.get(**get_params)
        else:
            entity = service.get()
    except sdk.Error:
        # We can get here 404, we should ignore it, in case
        # of removing entity for example.
        pass
    return entity


def get_id_by_name(service, name, raise_error=True, ignore_case=False):
    """
    Search an entity ID by it's name.
    """
    entity = search_by_name(service, name)

    if entity is not None:
        return entity.id

    if raise_error:
        raise Exception("Entity '%s' was not found." % name)


def wait(
    service,
    condition,
    fail_condition=lambda e: False,
    timeout=180,
    wait=True,
    poll_interval=3,
):
    """
    Wait until entity fulfill expected condition.

    :param service: service of the entity
    :param condition: condition to be fulfilled
    :param fail_condition: if this condition is true, raise Exception
    :param timeout: max time to wait in seconds
    :param wait: if True wait for condition, if False don't wait
    :param poll_interval: Number of seconds we should wait until next condition check
    """
    # Wait until the desired state of the entity:
    if wait:
        start = time.time()
        while time.time() < start + timeout:
            # Exit if the condition of entity is valid:
            entity = get_entity(service)
            if condition(entity):
                return
            elif fail_condition(entity):
                raise Exception("Error while waiting on result state of the entity.")

            # Sleep for `poll_interval` seconds if none of the conditions apply:
            time.sleep(float(poll_interval))

        raise Exception("Timeout exceed while waiting on result state of the entity.")


def __get_auth_dict():
    OVIRT_URL = os.environ.get('OVIRT_URL')
    OVIRT_HOSTNAME = os.environ.get('OVIRT_HOSTNAME')
    OVIRT_USERNAME = os.environ.get('OVIRT_USERNAME')
    OVIRT_PASSWORD = os.environ.get('OVIRT_PASSWORD')
    OVIRT_TOKEN = os.environ.get('OVIRT_TOKEN')
    OVIRT_CAFILE = os.environ.get('OVIRT_CAFILE')
    OVIRT_INSECURE = OVIRT_CAFILE is None

    env_vars = None
    if OVIRT_URL is None and OVIRT_HOSTNAME is not None:
        OVIRT_URL = 'https://{0}/ovirt-engine/api'.format(OVIRT_HOSTNAME)
    if OVIRT_URL and ((OVIRT_USERNAME and OVIRT_PASSWORD) or OVIRT_TOKEN):
        env_vars = {
            'url': OVIRT_URL,
            'username': OVIRT_USERNAME,
            'password': OVIRT_PASSWORD,
            'insecure': OVIRT_INSECURE,
            'token': OVIRT_TOKEN,
            'ca_file': OVIRT_CAFILE,
        }
    if env_vars is not None:
        auth = dict(default=env_vars, type='dict')
    else:
        auth = dict(required=True, type='dict')

    return auth


def ovirt_facts_full_argument_spec(**kwargs):
    """
    Extend parameters of facts module with parameters which are common to all
    oVirt facts modules.

    :param kwargs: kwargs to be extended
    :return: extended dictionary with common parameters
    """
    spec = dict(
        auth=__get_auth_dict(),
        fetch_nested=dict(default=False, type='bool'),
        nested_attributes=dict(type='list', default=list()),
    )
    spec.update(kwargs)
    return spec


def ovirt_full_argument_spec(**kwargs):
    """
    Extend parameters of module with parameters which are common to all oVirt modules.

    :param kwargs: kwargs to be extended
    :return: extended dictionary with common parameters
    """
    spec = dict(
        auth=__get_auth_dict(),
        timeout=dict(default=180, type='int'),
        wait=dict(default=True, type='bool'),
        poll_interval=dict(default=3, type='int'),
        fetch_nested=dict(default=False, type='bool'),
        nested_attributes=dict(type='list', default=list()),
    )
    spec.update(kwargs)
    return spec


def check_params(module):
    """
    Most modules must have either `name` or `id` specified.
    """
    if module.params.get('name') is None and module.params.get('id') is None:
        module.fail_json(msg='"name" or "id" is required')


def engine_supported(connection, version):
    return LooseVersion(engine_version(connection)) >= LooseVersion(version)


def check_support(version, connection, module, params):
    """
    Check if parameters used by user are supported by oVirt Python SDK
    and oVirt engine.
    """
    api_version = LooseVersion(engine_version(connection))
    version = LooseVersion(version)
    for param in params:
        if module.params.get(param) is not None:
            return LooseVersion(sdk_version.VERSION) >= version and api_version >= version

    return True


class BaseModule(object):
    """
    This is base class for oVirt modules. oVirt modules should inherit this
    class and override method to customize specific needs of the module.
    The only abstract method of this class is `build_entity`, which must
    to be implemented in child class.
    """
    __metaclass__ = ABCMeta

    def __init__(self, connection, module, service, changed=False):
        self._connection = connection
        self._module = module
        self._service = service
        self._changed = changed
        self._diff = {'after': dict(), 'before': dict()}

    @property
    def changed(self):
        return self._changed

    @changed.setter
    def changed(self, changed):
        if not self._changed:
            self._changed = changed

    @abstractmethod
    def build_entity(self):
        """
        This method should return oVirt Python SDK type, which we want to
        create or update, initialized by values passed by Ansible module.

        For example if we want to create VM, we will return following:
          types.Vm(name=self._module.params['vm_name'])

        :return: Specific instance of sdk.Struct.
        """
        pass

    def param(self, name, default=None):
        """
        Return a module parameter specified by it's name.
        """
        return self._module.params.get(name, default)

    def update_check(self, entity):
        """
        This method handle checks whether the entity values are same as values
        passed to ansible module. By default we don't compare any values.

        :param entity: Entity we want to compare with Ansible module values.
        :return: True if values are same, so we don't need to update the entity.
        """
        return True

    def pre_create(self, entity):
        """
        This method is called right before entity is created.

        :param entity: Entity to be created or updated.
        """
        pass

    def post_create(self, entity):
        """
        This method is called right after entity is created.

        :param entity: Entity which was created.
        """
        pass

    def post_update(self, entity):
        """
        This method is called right after entity is updated.

        :param entity: Entity which was updated.
        """
        pass

    def diff_update(self, after, update):
        for k, v in update.items():
            if isinstance(v, Mapping):
                after[k] = self.diff_update(after.get(k, dict()), v)
            else:
                after[k] = update[k]
        return after

    def create(
        self,
        entity=None,
        result_state=None,
        fail_condition=lambda e: False,
        search_params=None,
        update_params=None,
        _wait=None,
        force_create=False,
        **kwargs
    ):
        """
        Method which is called when state of the entity is 'present'. If user
        don't provide `entity` parameter the entity is searched using
        `search_params` parameter. If entity is found it's updated, whether
        the entity should be updated is checked by `update_check` method.
        The corresponding updated entity is build by `build_entity` method.

        Function executed after entity is created can optionally be specified
        in `post_create` parameter. Function executed after entity is updated
        can optionally be specified in `post_update` parameter.

        :param entity: Entity we want to update, if exists.
        :param result_state: State which should entity has in order to finish task.
        :param fail_condition: Function which checks incorrect state of entity, if it returns `True` Exception is raised.
        :param search_params: Dictionary of parameters to be used for search.
        :param update_params: The params which should be passed to update method.
        :param kwargs: Additional parameters passed when creating entity.
        :return: Dictionary with values returned by Ansible module.
        """
        if entity is None and not force_create:
            entity = self.search_entity(search_params)

        self.pre_create(entity)

        if entity:
            # Entity exists, so update it:
            entity_service = self._service.service(entity.id)
            if not self.update_check(entity):
                new_entity = self.build_entity()
                if not self._module.check_mode:
                    update_params = update_params or {}
                    updated_entity = entity_service.update(
                        new_entity,
                        **update_params
                    )
                    self.post_update(entity)

                # Update diffs only if user specified --diff parameter,
                # so we don't useless overload API:
                if self._module._diff:
                    before = get_dict_of_struct(
                        entity,
                        self._connection,
                        fetch_nested=True,
                        attributes=['name'],
                    )
                    after = before.copy()
                    self.diff_update(after, get_dict_of_struct(new_entity))
                    self._diff['before'] = before
                    self._diff['after'] = after

                self.changed = True
        else:
            # Entity don't exists, so create it:
            if not self._module.check_mode:
                entity = self._service.add(
                    self.build_entity(),
                    **kwargs
                )
                self.post_create(entity)
            self.changed = True

        if not self._module.check_mode:
            # Wait for the entity to be created and to be in the defined state:
            entity_service = self._service.service(entity.id)

            def state_condition(entity):
                return entity

            if result_state:

                def state_condition(entity):
                    return entity and entity.status == result_state

            wait(
                service=entity_service,
                condition=state_condition,
                fail_condition=fail_condition,
                wait=_wait if _wait is not None else self._module.params['wait'],
                timeout=self._module.params['timeout'],
                poll_interval=self._module.params['poll_interval'],
            )

        return {
            'changed': self.changed,
            'id': getattr(entity, 'id', None),
            type(entity).__name__.lower(): get_dict_of_struct(
                struct=entity,
                connection=self._connection,
                fetch_nested=self._module.params.get('fetch_nested'),
                attributes=self._module.params.get('nested_attributes'),
            ),
            'diff': self._diff,
        }

    def pre_remove(self, entity):
        """
        This method is called right before entity is removed.

        :param entity: Entity which we want to remove.
        """
        pass

    def entity_name(self, entity):
        return "{e_type} '{e_name}'".format(
            e_type=type(entity).__name__.lower(),
            e_name=getattr(entity, 'name', None),
        )

    def remove(self, entity=None, search_params=None, **kwargs):
        """
        Method which is called when state of the entity is 'absent'. If user
        don't provide `entity` parameter the entity is searched using
        `search_params` parameter. If entity is found it's removed.

        Function executed before remove is executed can optionally be specified
        in `pre_remove` parameter.

        :param entity: Entity we want to remove.
        :param search_params: Dictionary of parameters to be used for search.
        :param kwargs: Additional parameters passed when removing entity.
        :return: Dictionary with values returned by Ansible module.
        """
        if entity is None:
            entity = self.search_entity(search_params)

        if entity is None:
            return {
                'changed': self.changed,
                'msg': "Entity wasn't found."
            }

        self.pre_remove(entity)

        entity_service = self._service.service(entity.id)
        if not self._module.check_mode:
            entity_service.remove(**kwargs)
            wait(
                service=entity_service,
                condition=lambda entity: not entity,
                wait=self._module.params['wait'],
                timeout=self._module.params['timeout'],
                poll_interval=self._module.params['poll_interval'],
            )
        self.changed = True

        return {
            'changed': self.changed,
            'id': entity.id,
            type(entity).__name__.lower(): get_dict_of_struct(
                struct=entity,
                connection=self._connection,
                fetch_nested=self._module.params.get('fetch_nested'),
                attributes=self._module.params.get('nested_attributes'),
            ),
        }

    def action(
        self,
        action,
        entity=None,
        action_condition=lambda e: e,
        wait_condition=lambda e: e,
        fail_condition=lambda e: False,
        pre_action=lambda e: e,
        post_action=lambda e: None,
        search_params=None,
        **kwargs
    ):
        """
        This method is executed when we want to change the state of some oVirt
        entity. The action to be executed on oVirt service is specified by
        `action` parameter. Whether the action should be executed can be
        specified by passing `action_condition` parameter. State which the
        entity should be in after execution of the action can be specified
        by `wait_condition` parameter.

        Function executed before an action on entity can optionally be specified
        in `pre_action` parameter. Function executed after an action on entity can
        optionally be specified in `post_action` parameter.

        :param action: Action which should be executed by service on entity.
        :param entity: Entity we want to run action on.
        :param action_condition: Function which is executed when checking if action should be executed.
        :param fail_condition: Function which checks incorrect state of entity, if it returns `True` Exception is raised.
        :param wait_condition: Function which is executed when waiting on result state.
        :param pre_action: Function which is executed before running the action.
        :param post_action: Function which is executed after running the action.
        :param search_params: Dictionary of parameters to be used for search.
        :param kwargs: Additional parameters passed to action.
        :return: Dictionary with values returned by Ansible module.
        """
        if entity is None:
            entity = self.search_entity(search_params)

        entity = pre_action(entity)

        if entity is None:
            self._module.fail_json(
                msg="Entity not found, can't run action '{0}'.".format(
                    action
                )
            )

        entity_service = self._service.service(entity.id)
        entity = entity_service.get()
        if action_condition(entity):
            if not self._module.check_mode:
                getattr(entity_service, action)(**kwargs)
            self.changed = True

        post_action(entity)

        wait(
            service=self._service.service(entity.id),
            condition=wait_condition,
            fail_condition=fail_condition,
            wait=self._module.params['wait'],
            timeout=self._module.params['timeout'],
            poll_interval=self._module.params['poll_interval'],
        )
        return {
            'changed': self.changed,
            'id': entity.id,
            type(entity).__name__.lower(): get_dict_of_struct(
                struct=entity,
                connection=self._connection,
                fetch_nested=self._module.params.get('fetch_nested'),
                attributes=self._module.params.get('nested_attributes'),
            ),
            'diff': self._diff,
        }

    def wait_for_import(self, condition=lambda e: True):
        if self._module.params['wait']:
            start = time.time()
            timeout = self._module.params['timeout']
            poll_interval = self._module.params['poll_interval']
            while time.time() < start + timeout:
                entity = self.search_entity()
                if entity and condition(entity):
                    return entity
                time.sleep(poll_interval)

    def search_entity(self, search_params=None, list_params=None):
        """
        Always first try to search by `ID`, if ID isn't specified,
        check if user constructed special search in `search_params`,
        if not search by `name`.
        """
        entity = None

        if 'id' in self._module.params and self._module.params['id'] is not None:
            entity = get_entity(self._service.service(self._module.params['id']), get_params=list_params)
        elif search_params is not None:
            entity = search_by_attributes(self._service, list_params=list_params, **search_params)
        elif self._module.params.get('name') is not None:
            entity = search_by_attributes(self._service, list_params=list_params, name=self._module.params['name'])

        return entity

    def _get_major(self, full_version):
        if full_version is None or full_version == "":
            return None
        if isinstance(full_version, otypes.Version):
            return int(full_version.major)
        return int(full_version.split('.')[0])

    def _get_minor(self, full_version):
        if full_version is None or full_version == "":
            return None
        if isinstance(full_version, otypes.Version):
            return int(full_version.minor)
        return int(full_version.split('.')[1])


def _sdk4_error_maybe():
    """
    Allow for ovirtsdk4 not being installed.
    """
    if HAS_SDK:
        return sdk.Error
    return type(None)


class OvirtRetry(CloudRetry):
    base_class = _sdk4_error_maybe()

    @staticmethod
    def status_code_from_exception(error):
        return error.code

    @staticmethod
    def found(response_code, catch_extra_error_codes=None):
        # This is a list of error codes to retry.
        retry_on = [
            # HTTP status: Conflict
            409,
        ]
        if catch_extra_error_codes:
            retry_on.extend(catch_extra_error_codes)

        return response_code in retry_on
