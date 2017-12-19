#
#  Copyright 2018 Red Hat | Ansible
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

import copy

from ansible.module_utils.k8s_common import KubernetesAnsibleModule, AnsibleMixin, ARG_SPEC

try:
    from openshift.helper.openshift import OpenShiftObjectHelper
    from openshift.helper.exceptions import KubernetesException
    HAS_OPENSHIFT_HELPER = True
except ImportError as exc:
    class OpenShiftObjectHelper(object):
        pass
    HAS_OPENSHIFT_HELPER = False


class OpenShiftAnsibleModuleHelper(AnsibleMixin, OpenShiftObjectHelper):
    pass


class OpenShiftAnsibleModule(KubernetesAnsibleModule):
    def __init__(self):

        if not HAS_OPENSHIFT_HELPER:
            raise Exception(
                "This module requires the OpenShift Python client. Try `pip install openshift`"
            )

        super(OpenShiftAnsibleModule, self).__init__()

    @property
    def _argspec(self):
        return copy.deepcopy(ARG_SPEC)

    def _get_helper(self, api_version, kind):
        try:
            helper = OpenShiftAnsibleModuleHelper(api_version=api_version, kind=kind, debug=False)
            helper.get_model(api_version, kind)
            return helper
        except KubernetesException as exc:
            self.exit_json(msg="Error initializing module helper {}".format(exc.message))

    def _create(self, namespace):
        if self.kind.lower() == 'project':
            return self._create_project()
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
