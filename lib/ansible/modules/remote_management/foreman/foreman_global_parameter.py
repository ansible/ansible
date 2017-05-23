#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c)Matthias Dellweg & Bernhard Hopfenmüller 2017

try:
    from nailgun.config import ServerConfig
    import nailgun.entity_mixins
    import nailgun.entities
    HAS_NAILGUN_PACKAGE = True
except:
    HAS_NAILGUN_PACKAGE = False

from ansible.module_utils.basic import *

'''CommonParameter needs to inherit functionalities
   for searching, updating and deleting'''


class CommonParameter(
                      nailgun.entities.CommonParameter,
                      nailgun.entity_mixins.Entity,
                      nailgun.entity_mixins.EntityCreateMixin,
                      nailgun.entity_mixins.EntityDeleteMixin,
                      nailgun.entity_mixins.EntityReadMixin,
                      nailgun.entity_mixins.EntitySearchMixin,
                      nailgun.entity_mixins.EntityUpdateMixin,
                     ):
    pass


def create_CommonParameter(name, value):
    CommonParameter(name=name, value=value).create()


def update_CommonParameter(name, value):
    CommonParameter(name=name, value=value).update()


def create_Server(server_url, auth, verify_ssl):
    ServerConfig(
        url=server_url,
        auth=auth,
        verify=verify_ssl,
    ).save()


def find_Entity(entity, **kwargs):
    instance = entity(**kwargs)
    return instance.search(
        set(),
        {'search': '{}="{}"'.format(key, kwargs[key]) for key in kwargs}
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True),
            username=dict(required=True, no_log=True),
            password=dict(required=True, no_log=True),
            verify_ssl=dict(required=False, type='bool', default=False),
            name=dict(required=True, no_log=False),
            value=dict(required=False, no_log=False),
            state=dict(required=True, no_log=False),
        ),
        supports_check_mode=True
    )
    if not HAS_NAILGUN_PACKAGE:
        module.fail_json(
            msg="""Missing required nailgun module (check docs or install
            with: pip install nailgun"""
        )

    server_url = module.params['server_url']
    username = module.params['username']
    password = module.params['password']
    verify_ssl = module.params['verify_ssl']
    name = module.params['name']
    value = module.params['value']
    state = module.params['state']
    auth = (username, password)
    changed = False
    try:
        create_Server(server_url, auth, verify_ssl)
        param = find_Entity(CommonParameter, name=name)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Foreman server: %s " % e)
    try:
        if state == 'present':
            if not value:
                module.fail_json(msg='value is required when state=present')
            if len(param) == 1:
                if param[0].value != value:
                    param[0].value = value
                    param[0].update()
                    changed = True
            else:
                create_CommonParameter(name, value)
                changed = True
        elif state == 'absent':
            if len(param) == 1:
                param[0].delete()
                changed = True
        else:
            module.fail_json(msg='state can only be present or absent')
    except Exception as e:
        module.fail_json(msg=e)

    module.exit_json(changed=changed)

if __name__ == '__main__':
    main()
