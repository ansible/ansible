
from ansible.errors import AnsibleError
from ansible.module_utils.k8s_lookup import KubernetesLookup

try:
    from openshift.helper.openshift import OpenShiftObjectHelper
    from openshift.helper.exceptions import KubernetesException
    HAS_K8S_MODULE_HELPER = True
except ImportError as exc:
    HAS_K8S_MODULE_HELPER = False


class OpenShiftLookup(KubernetesLookup):

    def __init__(self):

        if not HAS_K8S_MODULE_HELPER:
            raise AnsibleError(
                "The OpenShift lookup requires the OpenShift Python client. Try `pip install openshift`"
            )

        super(OpenShiftLookup, self).__init__()

    def get_helper(self):
        try:
            helper = OpenShiftObjectHelper(api_version=self.api_version, kind=self.kind, debug=False)
            helper.get_model(self.api_version, self.kind)
        except KubernetesException as exc:
            raise AnsibleError("Error initializing OpenShift helper {0}".format(exc.message))
        return helper
