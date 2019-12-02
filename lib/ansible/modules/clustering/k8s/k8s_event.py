#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2019 Emily Moss
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """

module: k8s_events

short_description: Create Kubernetes Events

version_added: "2.8"

author: Emily Moss for Red Hat

description:
  - Create Kubernetes Events for Metering

extends_documentation_fragment:
  - k8s_auth_options

options:
  resource_definition:
    description:
    - A partial YAML definition of the Event object being created/updated. Here you can define Kubernetes
      Event Resource parameters not covered by this module's parameters.
    - "NOTE: I(resource_definition) has lower priority than module parameters. If you try to define e.g.
      I(metadata.namespace) here, that value will be ignored and I(metadata) used instead."
    aliases:
    - definition
    - inline
    type: dict
  state:
    description:
    - Determines if an object should be created, patched, or deleted. When set to C(present), an object will be
      created, if it does not already exist. If set to C(absent), an existing object will be deleted. If set to
      C(present), an existing object will be patched, if its attributes differ from those specified using
      module options and I(resource_definition).
    default: present
    choices:
    - present
    - absent
  force:
    description:
    - If set to C(True), and I(state) is C(present), an existing object will be replaced.
    default: false
    type: bool
  merge_type:
    description:
    - Whether to override the default patch merge approach with a specific type. By default, the strategic
      merge will typically be used.
    - For example, Custom Resource Definitions typically aren't updatable by the usual strategic merge. You may
      want to use C(merge) if you see "strategic merge patch format is not supported"
    - See U(https://kubernetes.io/docs/tasks/run-application/update-api-object-kubectl-patch/#use-a-json-merge-patch-to-update-a-deployment)
    - Requires openshift >= 0.6.2
    - If more than one merge_type is given, the merge_types will be tried in order
    - If openshift >= 0.6.2, this defaults to C(['strategic-merge', 'merge']), which is ideal for using the same parameters
      on resource kinds that combine Custom Resources and built-in resources. For openshift < 0.6.2, the default
      is simply C(strategic-merge).
    choices:
    - json
    - merge
    - strategic-merge
    type: list
  name:
    description:
      - Use to specify a Event object name.
    required: true
    type: str
  namespace:
    description:
      - Use to specify a Event object namespace.
    required: true
    type: str
  message:
    description:
      - Status for Operation
    required: true
    type: str
  reason:
    description:
      - Reason for the transition into the objects current status
    required: true
    type: str
  reportingComponent:
    description:
      - Component responsible for event
    required: true
    type: str
  type:
    description:
      - Type of Event
    choices:
      - Warning
      - Normal
  source:
    description: EventSource
      - Component for reporting this Event
    - component
      required: true
      type: string
  involvedObject:
    description: ObjectReference
      - Object event is reporting on. ApiVersion, kind, name and namespace are of the involvedObject.
    - apiVersion
      required: true
      type: string
    - kind
      required: true
      type: string
    - name
      required: true
      type: string
    - namespace
      required: true
      type: string

requirements:
  - python >= 2.7
  - openshift >= 0.6.2
"""

EXAMPLES = """

- name: Create Kubernetes Event
  k8s_events
    state: present
    name: test-https-emily109
    namespace: default
    message: Event created
    reason: Created
    reportingComponent: Reporting components
    type: Normal
    source:
      component: Metering components
    involvedObject:
      apiVersion: v1
      kind: Service
      name: test-https-emily107
      namespace: default
"""

RETURN = """
result:
  description:
  - The created, patched, or otherwise present Event object. Will be empty in the case of a deletion.
  returned: success
  type: complex
  contains:
     api_version:
        description: The versioned schema of this representation of an object.
        returned: success
        type: str
     count:
       description: Count of Event occurance
       returned: success
       type: int
     firstTimestamp:
       description: Timestamp of first occurance of Event
       returned: success
       type: timestamp
     involvedObject:
       description: Object event is reporting on. Includes apiVersion, kind, name, namespace, resourceVersion and uid.
       returned: success
       type: complex
     kind:
       description: Always 'Event'.
       returned: success
       type: str
     lastTimestamp:
       description: Timestamp of last occurance of Event
       returned: success
       type: timestamp
     message:
       description: Status for operation
       returned: success
       type: str
     metadata:
       description: Standard object metadata. Includes name, namespace, annotations, labels, etc.
       returned: success
       type: complex
     reason:
       description: Reason for the transition into the objects current status
       returned: success
       type: str
     reportingComponent:
       description: Component responsible for event
       returned: success
       type: str
     source:
       description: Source contains information for an Event
       returned: success
       type: complex
     type:
       description: Type of Event. Either Normal or Warning
       returned: success
       type: string

"""

import copy
import traceback
import datetime
import kubernetes.config.dateutil
import openshift

from collections import defaultdict

from ansible.module_utils.k8s.common import AUTH_ARG_SPEC
from ansible.module_utils.k8s.raw import KubernetesRawModule

EVENT_ARG_SPEC = {
    "state": {"default": "present", "choices": ["present", "absent"]},
    "name": {"required": True},
    "namespace": {"required": True},
    "merge_type": {"type": "list", "choices": ["json", "merge", "strategic-merge"]},
    "message": {"type": "str", "required": True},
    "reason": {"type": "str", "required": True},
    "reportingComponent": {"type": "str", "required": True},
    "type": {"choices": ["Normal", "Warning"]},
    "source": {
        "type": "dict",
        "component": {"type": "str", "required": True}
    },
    "involvedObject": {
        "type": "dict",
        "apiVersion": {"type": "str", "required": True},
        "kind": {"type": "str", "required": True},
        "name": {"type": "str", "required": True},
        "namespace": {"type": "str", "required": True},
    },
}


class KubernetesEvent(KubernetesRawModule):
    def __init__(self, *args, **kwargs):
        super(KubernetesEvent, self).__init__(*args, k8s_kind="Event", **kwargs)

    @property
    def argspec(self):
        """ argspec property builder """
        argumentSpec = copy.deepcopy(AUTH_ARG_SPEC)
        argumentSpec.update(EVENT_ARG_SPEC)
        return argumentSpec

    def execute_module(self):
        """ Module execution """
        self.client = self.get_api_client()

        message = self.params.get("message")
        reason = self.params.get("reason")
        reporting_component = self.params.get("reportingComponent")
        event_type = self.params.get("type")
        source = self.params.get("source")

        definition = defaultdict(defaultdict)

        meta = definition["metadata"]
        meta["name"] = self.params.get("name")
        meta["namespace"] = self.params.get("namespace")

        involved_obj = self.params.get("involvedObject")

        resource = self.find_resource("Event", "v1", fail=True)

        prior_event = None
        try:
            prior_event = resource.get(
                name=meta["name"],
                namespace=meta["namespace"])

        except openshift.dynamic.exceptions.NotFoundError:
            pass

        prior_count = 1
        now = datetime.datetime.now()
        rfc = kubernetes.config.dateutil.format_rfc3339(now)
        first_timestamp = rfc
        last_timestamp = rfc

        if prior_event and prior_event["reason"] == reason:
            prior_count = prior_event["count"] + 1
            first_timestamp = prior_event["firstTimestamp"]
            last_timestamp = rfc

        involved_object_resource = self.find_resource(involved_obj["kind"], "v1", fail=True)

        if involved_object_resource:
            try:
                api_involved_object = involved_object_resource.get(
                   name=involved_obj["name"], namespace=involved_obj["namespace"])

                involved_obj["uid"] = api_involved_object["metadata"]["uid"]
                involved_obj["resourceVersion"] = api_involved_object["metadata"]["resourceVersion"]

            except openshift.dynamic.exceptions.NotFoundError:
                pass

        event = {
            "count": prior_count,
            "eventTime": None,
            "firstTimestamp": first_timestamp,
            "involvedObject": involved_obj,
            "lastTimestamp": last_timestamp,
            "message": message,
            "metadata": {
                "name": meta["name"],
                "namespace": meta["namespace"]
            },
            "reason": reason,
            "reportingComponent": reporting_component,
            "reportingInstance": "",
            "source": source,
            "type": event_type,
        }

        result = self.perform_action(resource, event)
        self.exit_json(**result)


def main():
    module = KubernetesEvent()
    try:
        module.execute_module()
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())


if __name__ == "__main__":
    main()
