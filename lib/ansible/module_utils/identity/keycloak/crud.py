# Copyright: (c) 2018, Nicolas Duclert <nicolas.duclert@metronlab.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

from ansible.module_utils._text import to_text

__metaclass__ = type


def crud_with_instance(instance_to_crud, result_key):
    """Function managing actions from the wanted state given by the user.
    :param instance_to_crud: a class with the following functions:
    * delete: a function deleting the object on Keycloak,
    * update: a function updating the object on Keycolak,
    * create: a function creating the object on Keycloak,
    and the following properties:
    * module: the ansible module,
    * initial_representation: the initial state of the instance on the Keycloak,
    * representation: the state of the instance at the line of the program (this property do a new
      call to Keycloak),
    * description: the nature of the instance and its given id (mainly name or uuid).
    :param result_key: the key name where the final representation will be written
    :return: a dictionary with three keys:
    * changed: if the Keycloak object has been modified,
    * msg: a text message resuming the action done,
    * result_key: the final representation of the object.
    """
    module = instance_to_crud.module
    waited_state = module.params.get('state')

    if waited_state == 'absent':
        if instance_to_crud.initial_representation:
            if not module.check_mode:
                instance_to_crud.delete()
            result = {
                'changed': True,
                'msg': '{description} deleted.'.format(
                    description=instance_to_crud.description.capitalize(),
                ),
                result_key: {},
            }
        else:
            result = {
                'changed': False,
                'msg': '{description} does not exist, doing nothing.'.format(
                    description=instance_to_crud.description.capitalize()
                ),
                result_key: {},
            }
    else:
        if instance_to_crud.initial_representation:
            if module.check_mode:
                payload = instance_to_crud.update(check=True)
            else:
                payload = instance_to_crud.update()
            if payload:
                result = {
                    'msg': to_text(
                        '{description} updated.'.format(
                            description=instance_to_crud.description.capitalize()
                        )
                    ),
                    'changed': True,
                    result_key: instance_to_crud.representation,
                }
            else:
                result = {
                    'changed': False,
                    'msg': '{description} up to date, doing nothing.'.format(
                        description=instance_to_crud.description.capitalize()
                    ),
                    result_key: instance_to_crud.initial_representation,
                }
        else:
            if module.check_mode:
                payload = instance_to_crud.create(check=True)
            else:
                instance_to_crud.create()
                payload = instance_to_crud.representation

            result = {
                'msg': to_text(
                    '{description} created.'.format(
                        description=instance_to_crud.description.capitalize()
                    )
                ),
                'changed': True,
                result_key: payload,
            }

    return result
