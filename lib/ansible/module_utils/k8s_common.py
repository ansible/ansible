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

HAS_KUBE = True
HAS_KUBE_EXC = None

from ansible.module_utils.basic import *

try:
    from kubernetes import client, config
    from kubernetes.config.config_exception import ConfigException
except ImportError as exc:
    HAS_KUBE_EXC = str(exc)
    HAS_KUBE = False

# TODO Add https://github.com/cdrage/kubeshift for OpenShit specific objects (e.g. routes)

# TODO Add common authentication parameters

class K8SClient(object):
    '''
    Performs tasks that are common to all of the k8s modules. Instantiates a Kubernetes client, AnsibleModule, and
    optionally an OpenShift client.

    Pass in kubernetes=True to instantiate the Kubernetes client, and access via .k8s_client property. In general the
    Kubernetes client will work with OpenShift. But, if you need to access an OpenShift specific endpoint, pass
    openshift=True, and access it as .os_client.
    '''

    module = None
    k8s_client = None
    os_client = None

    def __init__(self, kubernetes=True, openshift=False, **kwargs):
        '''
        Performs any common module init tasks including: kubernetes and openshift_client instantiation, and handling
        missing Python requirements.
        :param kubernetes: bool. Set to True, if kubernetes client is desired. This will generally be True, except
                                  in select cases where an object or endpoint is unique to OpenShift. For example,
                                  routes.
        :param openshift: bool. Set to True, if openshift client is desired. As above, this will only be True when
                                  accessing an object or API endpoint unique to OpenShift.
        :param kwargs: Ansible module parameters (see lib/ansible/module_utils/basic.py)
        :return: None
        '''

        #TODO add commont module params to kwargs['argument_spec']
        
        self.module = AnsibleModule(**kwargs)

        if kubernetes:
            if not HAS_KUBE:
                self.module.fail_json(msg="Failed to load kubernetes. Try `pip install kuberenetes`.")

            # The module needs the kubernetes client
            try:
                config.load_kube_config()
            except ConfigException as exc:
                self.module.fail_json(msg="Exception calling load_kube_config: {}".format(str(exc)))

            self.k8s_client = client.CoreV1Api()

        if openshift:
            pass
            # TODO Add OpenShift client instantiation

