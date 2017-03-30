#
#  Copyright 2017 Red Hat | Ansible
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

from ansible.module_utils.k8s_common import KubernetesAnsibleException, KubernetesAnsibleModule

try:
    from openshift.helper.ansible import OpenShiftAnsibleModuleHelper, ARG_ATTRIBUTES_BLACKLIST
    from openshift.helper.exceptions import KubernetesException, OpenShiftException
    HAS_OPENSHIFT_HELPER = True
except ImportError as exc:
    HAS_OPENSHIFT_HELPER = False


class OpenShiftAnsibleException(KubernetesAnsibleException):
    pass


class OpenShiftAnsibleModule(KubernetesAnsibleModule):
    def __init__(self, kind, api_version):
        if not HAS_OPENSHIFT_HELPER:
            raise OpenShiftAnsibleException(
                "This module requires the OpenShift Python client. Try `pip install openshift`"
            )

        try:
            super(OpenShiftAnsibleModule, self).__init__(kind, api_version)
        except KubernetesAnsibleException as exc:
            raise OpenShiftAnsibleException(exc.args)

    @staticmethod
    def get_helper(api_version, kind):
        return OpenShiftAnsibleModuleHelper(api_version, kind)

    def _create(self, namespace):
        if self.kind.lower() == 'project':
            return self._create_project()
        else:
            return super(OpenShiftAnsibleModule, self)._create(namespace)

    def _create_project(self):
        new_obj = None
        k8s_obj = None
        try:
            new_obj = self.helper.object_from_params(self.params)
        except KubernetesException as exc:
            self.fail_json(msg="Failed to create object: {}".format(exc.message))
        try:
            k8s_obj = self.helper.create_project(metadata=new_obj.metadata,
                                                 display_name=self.params.get('display_name'),
                                                 description=self.params.get('description'))
        except KubernetesException as exc:
            self.fail_json(msg='Failed to retrieve requested object',
                           error=exc.value.get('status'))
        return k8s_obj
