from __future__ import absolute_import

"""
Created on Aug 16, 2016

@author: Gaurav Rastogi (grastogi@avinetworks.com)
"""
import os
import re
import logging
import sys
from copy import deepcopy
from ansible.module_utils.basic import env_fallback

try:
    from ansible.module_utils.network.avi.avi_api import (
        ApiSession, ObjectNotFound, avi_sdk_syslog_logger, AviCredentials, HAS_AVI)
except ImportError:
    HAS_AVI = False


if os.environ.get('AVI_LOG_HANDLER', '') != 'syslog':
    log = logging.getLogger(__name__)
else:
    # Ansible does not allow logging from the modules.
    log = avi_sdk_syslog_logger()


def _check_type_string(x):
    """
    :param x:
    :return: True if it is of type string
    """
    if isinstance(x, str):
        return True
    if sys.version_info[0] < 3:
        try:
            return isinstance(x, unicode)
        except NameError:
            return False


class AviCheckModeResponse(object):
    """
    Class to support ansible check mode.
    """

    def __init__(self, obj, status_code=200):
        self.obj = obj
        self.status_code = status_code

    def json(self):
        return self.obj


def ansible_return(module, rsp, changed, req=None, existing_obj=None,
                   api_context=None):
    """
    :param module: AnsibleModule
    :param rsp: ApiResponse from avi_api
    :param changed: boolean
    :param req: ApiRequest to avi_api
    :param existing_obj: object to be passed debug output
    :param api_context: api login context

    helper function to return the right ansible based on the error code and
    changed
    Returns: specific ansible module exit function
    """

    if rsp is not None and rsp.status_code > 299:
        return module.fail_json(
            msg='Error %d Msg %s req: %s api_context:%s ' % (
                rsp.status_code, rsp.text, req, api_context))
    api_creds = AviCredentials()
    api_creds.update_from_ansible_module(module)
    key = '%s:%s:%s' % (api_creds.controller, api_creds.username,
                        api_creds.port)
    disable_fact = module.params.get('avi_disable_session_cache_as_fact')

    fact_context = None
    if not disable_fact:
        fact_context = module.params.get('api_context', {})
        if fact_context:
            fact_context.update({key: api_context})
        else:
            fact_context = {key: api_context}

    obj_val = rsp.json() if rsp else existing_obj

    if (obj_val and module.params.get("obj_username", None) and
            "username" in obj_val):
        obj_val["obj_username"] = obj_val["username"]
    if (obj_val and module.params.get("obj_password", None) and
            "password" in obj_val):
        obj_val["obj_password"] = obj_val["password"]
    old_obj_val = existing_obj if changed and existing_obj else None
    api_context_val = api_context if disable_fact else None
    ansible_facts_val = dict(
        avi_api_context=fact_context) if not disable_fact else {}

    return module.exit_json(
        changed=changed, obj=obj_val, old_obj=old_obj_val,
        ansible_facts=ansible_facts_val, api_context=api_context_val)


def purge_optional_fields(obj, module):
    """
    It purges the optional arguments to be sent to the controller.
    :param obj: dictionary of the ansible object passed as argument.
    :param module: AnsibleModule
    return modified obj
    """
    purge_fields = []
    for param, spec in module.argument_spec.items():
        if not spec.get('required', False):
            if param not in obj:
                # these are ansible common items
                continue
            if obj[param] is None:
                purge_fields.append(param)
    log.debug('purging fields %s', purge_fields)
    for param in purge_fields:
        obj.pop(param, None)
    return obj


def cleanup_absent_fields(obj):
    """
    cleans up any field that is marked as state: absent. It needs to be removed
    from the object if it is present.
    :param obj:
    :return: Purged object
    """
    if type(obj) != dict:
        return obj
    cleanup_keys = []
    for k, v in obj.items():
        if type(v) == dict:
            if (('state' in v and v['state'] == 'absent') or
                    (v == "{'state': 'absent'}")):
                cleanup_keys.append(k)
            else:
                cleanup_absent_fields(v)
                if not v:
                    cleanup_keys.append(k)
        elif type(v) == list:
            new_list = []
            for elem in v:
                elem = cleanup_absent_fields(elem)
                if elem:
                    # remove the item from list
                    new_list.append(elem)
            if new_list:
                obj[k] = new_list
            else:
                cleanup_keys.append(k)
        elif isinstance(v, str) or isinstance(v, str):
            if v == "{'state': 'absent'}":
                cleanup_keys.append(k)
    for k in cleanup_keys:
        del obj[k]
    return obj


RE_REF_MATCH = re.compile(r'^/api/[\w/]+\?name\=[\w]+[^#<>]*$')
# if HTTP ref match then strip out the #name
HTTP_REF_MATCH = re.compile(r'https://[\w.0-9:-]+/api/.+')
HTTP_REF_W_NAME_MATCH = re.compile(r'https://[\w.0-9:-]+/api/.*#.+')


def ref_n_str_cmp(x, y):
    """
    compares two references
    1. check for exact reference
    2. check for obj_type/uuid
    3. check for name

    if x is ref=name then extract uuid and name from y and use it.
    if x is http_ref then
        strip x and y
        compare them.

    if x and y are urls then match with split on #
    if x is a RE_REF_MATCH then extract name
    if y is a REF_MATCH then extract name
    :param x: first string
    :param y: second string from controller's object

    Returns
        True if they are equivalent else False
    """
    if type(y) in (int, float, bool, int, complex):
        y = str(y)
        x = str(x)
    if not (_check_type_string(x) and _check_type_string(y)):
        return False
    y_uuid = y_name = str(y)
    x = str(x)
    if RE_REF_MATCH.match(x):
        x = x.split('name=')[1]
    elif HTTP_REF_MATCH.match(x):
        x = x.rsplit('#', 1)[0]
        y = y.rsplit('#', 1)[0]
    elif RE_REF_MATCH.match(y):
        y = y.split('name=')[1]

    if HTTP_REF_W_NAME_MATCH.match(y):
        path = y.split('api/', 1)[1]
        # Fetching name or uuid from path /xxxx_xx/xx/xx_x/uuid_or_name
        uuid_or_name = path.split('/')[-1]
        parts = uuid_or_name.rsplit('#', 1)
        y_uuid = parts[0]
        y_name = parts[1] if len(parts) > 1 else ''
        # is just string but y is a url so match either uuid or name
    result = (x in (y, y_name, y_uuid))
    if not result:
        log.debug('x: %s y: %s y_name %s y_uuid %s',
                  x, y, y_name, y_uuid)
    return result


def avi_obj_cmp(x, y, sensitive_fields=None):
    """
    compares whether x is fully contained in y. The comparision is different
    from a simple dictionary compare for following reasons
    1. Some fields could be references. The object in controller returns the
        full URL for those references. However, the ansible script would have
        it specified as /api/pool?name=blah. So, the reference fields need
        to match uuid, relative reference based on name and actual reference.

    2. Optional fields with defaults: In case there are optional fields with
        defaults then controller automatically fills it up. This would
        cause the comparison with Ansible object specification to always return
        changed.

    3. Optional fields without defaults: This is most tricky. The issue is
        how to specify deletion of such objects from ansible script. If the
        ansible playbook has object specified as Null then Avi controller will
        reject for non Message(dict) type fields. In addition, to deal with the
        defaults=null issue all the fields that are set with None are purged
        out before comparing with Avi controller's version

        So, the solution is to pass state: absent if any optional field needs
        to be deleted from the configuration. The script would return changed
        =true if it finds a key in the controller version and it is marked with
        state: absent in ansible playbook. Alternatively, it would return
        false if key is not present in the controller object. Before, doing
        put or post it would purge the fields that are marked state: absent.

    :param x: first string
    :param y: second string from controller's object
    :param sensitive_fields: sensitive fields to ignore for diff

    Returns:
        True if x is subset of y else False
    """
    if not sensitive_fields:
        sensitive_fields = set()
    if isinstance(x, str) or isinstance(x, str):
        # Special handling for strings as they can be references.
        return ref_n_str_cmp(x, y)
    if type(x) not in [list, dict]:
        # if it is not list or dict or string then simply compare the values
        return x == y
    if type(x) == list:
        # should compare each item in the list and that should match
        if len(x) != len(y):
            log.debug('x has %d items y has %d', len(x), len(y))
            return False
        for i in zip(x, y):
            if not avi_obj_cmp(i[0], i[1], sensitive_fields=sensitive_fields):
                # no need to continue
                return False

    if type(x) == dict:
        x.pop('_last_modified', None)
        x.pop('tenant', None)
        y.pop('_last_modified', None)
        x.pop('api_version', None)
        y.pop('api_verison', None)
        d_xks = [k for k in x.keys() if k in sensitive_fields]

        if d_xks:
            # if there is sensitive field then always return changed
            return False
        # pop the keys that are marked deleted but not present in y
        # return false if item is marked absent and is present in y
        d_x_absent_ks = []
        for k, v in x.items():
            if v is None:
                d_x_absent_ks.append(k)
                continue
            if isinstance(v, dict):
                if ('state' in v) and (v['state'] == 'absent'):
                    if type(y) == dict and k not in y:
                        d_x_absent_ks.append(k)
                    else:
                        return False
                elif not v:
                    d_x_absent_ks.append(k)
            elif isinstance(v, list) and not v:
                d_x_absent_ks.append(k)
            # Added condition to check key in dict.
            elif isinstance(v, str) or (k in y and isinstance(y[k], str)):
                # this is the case when ansible converts the dictionary into a
                # string.
                if v == "{'state': 'absent'}" and k not in y:
                    d_x_absent_ks.append(k)
                elif not v and k not in y:
                    # this is the case when x has set the value that qualifies
                    # as not but y does not have that value
                    d_x_absent_ks.append(k)
        for k in d_x_absent_ks:
            x.pop(k)
        x_keys = set(x.keys())
        y_keys = set(y.keys())
        if not x_keys.issubset(y_keys):
            # log.debug('x has %s and y has %s keys', len(x_keys), len(y_keys))
            return False
        for k, v in x.items():
            if k not in y:
                # log.debug('k %s is not in y %s', k, y)
                return False
            if not avi_obj_cmp(v, y[k], sensitive_fields=sensitive_fields):
                # log.debug('k %s v %s did not match in y %s', k, v, y[k])
                return False
    return True


POP_FIELDS = ['state', 'controller', 'username', 'password', 'api_version',
              'avi_credentials', 'avi_api_update_method', 'avi_api_patch_op',
              'api_context', 'tenant', 'tenant_uuid', 'avi_disable_session_cache_as_fact']


def get_api_context(module, api_creds):
    api_context = module.params.get('api_context')
    if api_context and module.params.get('avi_disable_session_cache_as_fact'):
        return api_context
    elif api_context and not module.params.get(
            'avi_disable_session_cache_as_fact'):
        key = '%s:%s:%s' % (api_creds.controller, api_creds.username,
                            api_creds.port)
        return api_context.get(key)
    else:
        return None


def avi_ansible_api(module, obj_type, sensitive_fields):
    """
    This converts the Ansible module into AVI object and invokes APIs
    :param module: Ansible module
    :param obj_type: string representing Avi object type
    :param sensitive_fields: sensitive fields to be excluded for comparison
        purposes.
    Returns:
        success: module.exit_json with obj=avi object
        faliure: module.fail_json
    """

    api_creds = AviCredentials()
    api_creds.update_from_ansible_module(module)
    api_context = get_api_context(module, api_creds)
    if api_context:
        api = ApiSession.get_session(
            api_creds.controller,
            api_creds.username,
            password=api_creds.password,
            timeout=api_creds.timeout,
            tenant=api_creds.tenant,
            tenant_uuid=api_creds.tenant_uuid,
            token=api_context['csrftoken'],
            port=api_creds.port,
            session_id=api_context['session_id'],
            csrftoken=api_context['csrftoken'])
    else:
        api = ApiSession.get_session(
            api_creds.controller,
            api_creds.username,
            password=api_creds.password,
            timeout=api_creds.timeout,
            tenant=api_creds.tenant,
            tenant_uuid=api_creds.tenant_uuid,
            token=api_creds.token,
            port=api_creds.port)
    state = module.params['state']
    # Get the api version.
    avi_update_method = module.params.get('avi_api_update_method', 'put')
    avi_patch_op = module.params.get('avi_api_patch_op', 'add')

    api_version = api_creds.api_version
    name = module.params.get('name', None)
    # Added Support to get uuid
    uuid = module.params.get('uuid', None)
    check_mode = module.check_mode
    if uuid and obj_type != 'cluster':
        obj_path = '%s/%s' % (obj_type, uuid)
    else:
        obj_path = '%s/' % obj_type
    obj = deepcopy(module.params)
    tenant = obj.pop('tenant', '')
    tenant_uuid = obj.pop('tenant_uuid', '')
    # obj.pop('cloud_ref', None)
    for k in POP_FIELDS:
        obj.pop(k, None)
    purge_optional_fields(obj, module)

    # Special code to handle situation where object has a field
    # named username. This is used in case of api/user
    # The following code copies the username and password
    # from the obj_username and obj_password fields.
    if 'obj_username' in obj:
        obj['username'] = obj['obj_username']
        obj.pop('obj_username')
    if 'obj_password' in obj:
        obj['password'] = obj['obj_password']
        obj.pop('obj_password')
    if 'full_name' not in obj and 'name' in obj and obj_type == "user":
        obj['full_name'] = obj['name']
        # Special case as name represent full_name in user module
        # As per API response, name is always same as username regardless of full_name
        obj['name'] = obj['username']

    log.info('passed object %s ', obj)

    if uuid:
        # Get the object based on uuid.
        try:
            existing_obj = api.get(
                obj_path, tenant=tenant, tenant_uuid=tenant_uuid,
                params={'include_refs': '', 'include_name': ''},
                api_version=api_version)
            existing_obj = existing_obj.json()
        except ObjectNotFound:
            existing_obj = None
    elif name:
        params = {'include_refs': '', 'include_name': ''}
        if obj.get('cloud_ref', None):
            # this is the case when gets have to be scoped with cloud
            cloud = obj['cloud_ref'].split('name=')[1]
            params['cloud_ref.name'] = cloud
        existing_obj = api.get_object_by_name(
            obj_type, name, tenant=tenant, tenant_uuid=tenant_uuid,
            params=params, api_version=api_version)

        # Need to check if tenant_ref was provided and the object returned
        # is actually in admin tenant.
        if existing_obj and 'tenant_ref' in obj and 'tenant_ref' in existing_obj:
            # https://10.10.25.42/api/tenant/admin#admin
            existing_obj_tenant = existing_obj['tenant_ref'].split('#')[1]
            obj_tenant = obj['tenant_ref'].split('name=')[1]
            if obj_tenant != existing_obj_tenant:
                existing_obj = None
    else:
        # added api version to avi api call.
        existing_obj = api.get(obj_path, tenant=tenant, tenant_uuid=tenant_uuid,
                               params={'include_refs': '', 'include_name': ''},
                               api_version=api_version).json()

    if state == 'absent':
        rsp = None
        changed = False
        err = False
        if not check_mode and existing_obj:
            try:
                if name is not None:
                    # added api version to avi api call.
                    rsp = api.delete_by_name(
                        obj_type, name, tenant=tenant, tenant_uuid=tenant_uuid,
                        api_version=api_version)
                else:
                    # added api version to avi api call.
                    rsp = api.delete(
                        obj_path, tenant=tenant, tenant_uuid=tenant_uuid,
                        api_version=api_version)
            except ObjectNotFound:
                pass
        if check_mode and existing_obj:
            changed = True

        if rsp:
            if rsp.status_code == 204:
                changed = True
            else:
                err = True
        if not err:
            return ansible_return(
                module, rsp, changed, existing_obj=existing_obj,
                api_context=api.get_context())
        elif rsp:
            return module.fail_json(msg=rsp.text)

    rsp = None
    req = None
    if existing_obj:
        # this is case of modify as object exists. should find out
        # if changed is true or not
        if name is not None and obj_type != 'cluster':
            obj_uuid = existing_obj['uuid']
            obj_path = '%s/%s' % (obj_type, obj_uuid)
        if avi_update_method == 'put':
            changed = not avi_obj_cmp(obj, existing_obj, sensitive_fields)
            obj = cleanup_absent_fields(obj)
            if changed:
                req = obj
                if check_mode:
                    # No need to process any further.
                    rsp = AviCheckModeResponse(obj=existing_obj)
                else:
                    rsp = api.put(
                        obj_path, data=req, tenant=tenant,
                        tenant_uuid=tenant_uuid, api_version=api_version)
            elif check_mode:
                rsp = AviCheckModeResponse(obj=existing_obj)
        else:
            if check_mode:
                # No need to process any further.
                rsp = AviCheckModeResponse(obj=existing_obj)
                changed = True
            else:
                obj.pop('name', None)
                patch_data = {avi_patch_op: obj}
                rsp = api.patch(
                    obj_path, data=patch_data, tenant=tenant,
                    tenant_uuid=tenant_uuid, api_version=api_version)
                obj = rsp.json()
                changed = not avi_obj_cmp(obj, existing_obj)
        if changed:
            log.debug('EXISTING OBJ %s', existing_obj)
            log.debug('NEW OBJ %s', obj)
    else:
        changed = True
        req = obj
        if check_mode:
            rsp = AviCheckModeResponse(obj=None)
        else:
            rsp = api.post(obj_type, data=obj, tenant=tenant,
                           tenant_uuid=tenant_uuid, api_version=api_version)
    return ansible_return(module, rsp, changed, req, existing_obj=existing_obj,
                          api_context=api.get_context())


def avi_common_argument_spec():
    """
    Returns common arguments for all Avi modules
    :return: dict
    """
    credentials_spec = dict(
        controller=dict(fallback=(env_fallback, ['AVI_CONTROLLER'])),
        username=dict(fallback=(env_fallback, ['AVI_USERNAME'])),
        password=dict(fallback=(env_fallback, ['AVI_PASSWORD']), no_log=True),
        api_version=dict(default='16.4.4', type='str'),
        tenant=dict(default='admin'),
        tenant_uuid=dict(default='', type='str'),
        port=dict(type='int'),
        timeout=dict(default=300, type='int'),
        token=dict(default='', type='str', no_log=True),
        session_id=dict(default='', type='str', no_log=True),
        csrftoken=dict(default='', type='str', no_log=True)
    )

    return dict(
        controller=dict(fallback=(env_fallback, ['AVI_CONTROLLER'])),
        username=dict(fallback=(env_fallback, ['AVI_USERNAME'])),
        password=dict(fallback=(env_fallback, ['AVI_PASSWORD']), no_log=True),
        tenant=dict(default='admin'),
        tenant_uuid=dict(default=''),
        api_version=dict(default='16.4.4', type='str'),
        avi_credentials=dict(default=None, type='dict',
                             options=credentials_spec),
        api_context=dict(type='dict'),
        avi_disable_session_cache_as_fact=dict(default=False, type='bool'))
