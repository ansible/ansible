#!/usr/bin/python

# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
short_description: NetApp ONTAP FlexCache - create/delete relationship
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
  - Create/Delete FlexCache volume relationships
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_flexcache
options:
  state:
    choices: ['present', 'absent']
    description:
      - Whether the specified relationship should exist or not.
    default: present
  origin_volume:
    description:
      - Name of the origin volume for the FlexCache.
      - Required for creation.
  origin_vserver:
    description:
      - Name of the origin vserver for the FlexCache.
      - Required for creation.
  origin_cluster:
    description:
      - Name of the origin cluster for the FlexCache.
      - Defaults to cluster associated with target vserver if absent.
      - Not used for creation.
  volume:
    description:
      - Name of the target volume for the FlexCache.
    required: true
  junction_path:
    description:
      - Junction path of the cache volume.
  auto_provision_as:
    description:
      - Use this parameter to automatically select existing aggregates for volume provisioning.Eg flexgroup
      - Note that the fastest aggregate type with at least one aggregate on each node of the cluster will be selected.
  size:
    description:
      - Size of cache volume.
  size_unit:
    description:
    - The unit used to interpret the size parameter.
    choices: ['bytes', 'b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb']
    default: gb
  vserver:
    description:
      - Name of the target vserver for the FlexCache.
      - Note that hostname, username, password are intended for the target vserver.
    required: true
  aggr_list:
    description:
      - List of aggregates to host target FlexCache volume.
  aggr_list_multiplier:
    description:
      - Aggregate list repeat count.
  force_unmount:
    description:
      - Unmount FlexCache volume. Delete the junction path at which the volume is mounted before deleting the FlexCache relationship.
    type: bool
    default: false
  force_offline:
    description:
      - Offline FlexCache volume before deleting the FlexCache relationship.
      - The volume will be destroyed and data can be lost.
    type: bool
    default: false
  time_out:
    description:
      - time to wait for flexcache creation or deletion in seconds
      - if 0, the request is asynchronous
      - default is set to 3 minutes
    default: 180
version_added: "2.8"
'''

EXAMPLES = """

    - name: Create FlexCache
      na_ontap_FlexCache:
        state: present
        origin_volume: test_src
        volume: test_dest
        origin_vserver: ansible_src
        vserver: ansible_dest
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Delete FlexCache
      na_ontap_FlexCache:
        state: absent
        volume: test_dest
        vserver: ansible_dest
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

"""

RETURN = """
"""

import time
import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPFlexCache(object):
    """
    Class with FlexCache methods
    """

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', choices=['present', 'absent'],
                       default='present'),
            origin_volume=dict(required=False, type='str'),
            origin_vserver=dict(required=False, type='str'),
            origin_cluster=dict(required=False, type='str'),
            auto_provision_as=dict(required=False, type='str'),
            volume=dict(required=True, type='str'),
            junction_path=dict(required=False, type='str'),
            size=dict(required=False, type='int'),
            size_unit=dict(default='gb',
                           choices=['bytes', 'b', 'kb', 'mb', 'gb', 'tb',
                                    'pb', 'eb', 'zb', 'yb'], type='str'),
            vserver=dict(required=True, type='str'),
            aggr_list=dict(required=False, type='list'),
            aggr_list_multiplier=dict(required=False, type='int'),
            force_offline=dict(required=False, type='bool', default=False),
            force_unmount=dict(required=False, type='bool', default=False),
            time_out=dict(required=False, type='int', default=180),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            mutually_exclusive=[
                ('aggr_list', 'auto_provision_as'),
            ],
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        if self.parameters.get('size'):
            self.parameters['size'] = self.parameters['size'] * \
                netapp_utils.POW2_BYTE_MAP[self.parameters['size_unit']]
        # setup later if required
        self.origin_server = None
        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])

    def add_parameter_to_dict(self, adict, name, key=None, tostr=False):
        ''' add defined parameter (not None) to adict using key '''
        if key is None:
            key = name
        if self.parameters.get(name) is not None:
            if tostr:
                adict[key] = str(self.parameters.get(name))
            else:
                adict[key] = self.parameters.get(name)

    def get_job(self, jobid, server):
        """
        Get job details by id
        """
        job_get = netapp_utils.zapi.NaElement('job-get')
        job_get.add_new_child('job-id', jobid)
        try:
            result = server.invoke_successfully(job_get, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            if to_native(error.code) == "15661":
                # Not found
                return None
            self.module.fail_json(msg='Error fetching job info: %s' % to_native(error),
                                  exception=traceback.format_exc())
        results = dict()
        job_info = result.get_child_by_name('attributes').get_child_by_name('job-info')
        results = {
            'job-progress': job_info['job-progress'],
            'job-state': job_info['job-state']
        }
        if job_info.get_child_by_name('job-completion') is not None:
            results['job-completion'] = job_info['job-completion']
        else:
            results['job-completion'] = None
        return results

    def check_job_status(self, jobid):
        """
        Loop until job is complete
        """
        server = self.server
        sleep_time = 5
        time_out = self.parameters['time_out']
        while time_out > 0:
            results = self.get_job(jobid, server)
            # If running as cluster admin, the job is owned by cluster vserver
            # rather than the target vserver.
            if results is None and server == self.server:
                results = netapp_utils.get_cserver(self.server)
                server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
                continue
            if results is None:
                error = 'cannot locate job with id: %d' % jobid
                break
            if results['job-state'] in ('queued', 'running'):
                time.sleep(sleep_time)
                time_out -= sleep_time
                continue
            if results['job-state'] in ('success', 'failure'):
                break
            else:
                self.module.fail_json(msg='Unexpected job status in: %s' % repr(results))

        if results is not None:
            if results['job-state'] == 'success':
                error = None
            elif results['job-state'] in ('queued', 'running'):
                error = 'job completion exceeded expected timer of: %s seconds' % \
                        self.parameters['time_out']
            else:
                if results['job-completion'] is not None:
                    error = results['job-completion']
                else:
                    error = results['job-progress']
        return error

    def flexcache_get_iter(self):
        """
        Compose NaElement object to query current FlexCache relation
        """
        options = {'volume': self.parameters['volume']}
        self.add_parameter_to_dict(options, 'origin_volume', 'origin-volume')
        self.add_parameter_to_dict(options, 'origin_vserver', 'origin-vserver')
        self.add_parameter_to_dict(options, 'origin_cluster', 'origin-cluster')
        flexcache_info = netapp_utils.zapi.NaElement.create_node_with_children(
            'flexcache-info', **options)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(flexcache_info)
        flexcache_get_iter = netapp_utils.zapi.NaElement('flexcache-get-iter')
        flexcache_get_iter.add_child_elem(query)
        return flexcache_get_iter

    def flexcache_get(self):
        """
        Get current FlexCache relations
        :return: Dictionary of current FlexCache details if query successful, else None
        """
        flexcache_get_iter = self.flexcache_get_iter()
        flex_info = dict()
        try:
            result = self.server.invoke_successfully(flexcache_get_iter, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching FlexCache info: %s' % to_native(error),
                                  exception=traceback.format_exc())
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:
            flexcache_info = result.get_child_by_name('attributes-list') \
                                   .get_child_by_name('flexcache-info')
            flex_info['origin_cluster'] = flexcache_info.get_child_content('origin-cluster')
            flex_info['origin_volume'] = flexcache_info.get_child_content('origin-volume')
            flex_info['origin_vserver'] = flexcache_info.get_child_content('origin-vserver')
            flex_info['size'] = flexcache_info.get_child_content('size')
            flex_info['volume'] = flexcache_info.get_child_content('volume')
            flex_info['vserver'] = flexcache_info.get_child_content('vserver')
            flex_info['auto_provision_as'] = flexcache_info.get_child_content('auto-provision-as')

            return flex_info
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) > 1:
            msg = 'Multiple records found for %s:' % self.parameters['volume']
            self.module.fail_json(msg='Error fetching FlexCache info: %s' % msg)
        return None

    def flexcache_create_async(self):
        """
        Create a FlexCache relationship
        """
        options = {'origin-volume': self.parameters['origin_volume'],
                   'origin-vserver': self.parameters['origin_vserver'],
                   'volume': self.parameters['volume']}
        self.add_parameter_to_dict(options, 'junction_path', 'junction-path')
        self.add_parameter_to_dict(options, 'auto_provision_as', 'auto-provision-as')
        self.add_parameter_to_dict(options, 'size', 'size', tostr=True)
        if self.parameters.get('aggr_list'):
            if self.parameters.get('aggr_list_multiplier'):
                self.tobytes_aggr_list_multiplier = bytes(self.parameters['aggr_list_multiplier'])
                self.add_parameter_to_dict(options, 'tobytes_aggr_list_multiplier', 'aggr-list-multiplier')
        flexcache_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'flexcache-create-async', **options)
        if self.parameters.get('aggr_list'):
            aggregates = netapp_utils.zapi.NaElement('aggr-list')
            for aggregate in self.parameters['aggr_list']:
                aggregates.add_new_child('aggr-name', aggregate)
            flexcache_create.add_child_elem(aggregates)
        try:
            result = self.server.invoke_successfully(flexcache_create, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating FlexCache %s' % to_native(error),
                                  exception=traceback.format_exc())
        results = dict()
        for key in ('result-status', 'result-jobid'):
            if result.get_child_by_name(key):
                results[key] = result[key]
        return results

    def flexcache_create(self):
        """
        Create a FlexCache relationship
        Check job status
        """
        results = self.flexcache_create_async()
        status = results.get('result-status')
        if status == 'in_progress' and 'result-jobid' in results:
            if self.parameters['time_out'] == 0:
                # asynchronous call, assuming success!
                return
            error = self.check_job_status(results['result-jobid'])
            if error is None:
                return
            else:
                self.module.fail_json(msg='Error when creating flexcache: %s' % error)
        self.module.fail_json(msg='Unexpected error when creating flexcache: results is: %s' % repr(results))

    def flexcache_delete_async(self):
        """
        Delete FlexCache relationship at destination cluster
        """
        options = {'volume': self.parameters['volume']}
        flexcache_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'flexcache-destroy-async', **options)
        try:
            result = self.server.invoke_successfully(flexcache_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting FlexCache : %s'
                                  % (to_native(error)),
                                  exception=traceback.format_exc())
        results = dict()
        for key in ('result-status', 'result-jobid'):
            if result.get_child_by_name(key):
                results[key] = result[key]
        return results

    def volume_offline(self):
        """
        Offline FlexCache volume at destination cluster
        """
        options = {'name': self.parameters['volume']}
        xml = netapp_utils.zapi.NaElement.create_node_with_children(
            'volume-offline', **options)
        try:
            self.server.invoke_successfully(xml, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error offlining FlexCache volume: %s'
                                  % (to_native(error)),
                                  exception=traceback.format_exc())

    def volume_unmount(self):
        """
        Unmount FlexCache volume at destination cluster
        """
        options = {'volume-name': self.parameters['volume']}
        xml = netapp_utils.zapi.NaElement.create_node_with_children(
            'volume-unmount', **options)
        try:
            self.server.invoke_successfully(xml, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error unmounting FlexCache volume: %s'
                                  % (to_native(error)),
                                  exception=traceback.format_exc())

    def flexcache_delete_async(self):
        """
        Delete FlexCache relationship at destination cluster
        """
        options = {'volume': self.parameters['volume']}
        flexcache_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'flexcache-destroy-async', **options)
        try:
            result = self.server.invoke_successfully(flexcache_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting FlexCache : %s'
                                  % (to_native(error)),
                                  exception=traceback.format_exc())
        results = dict()
        for key in ('result-status', 'result-jobid'):
            if result.get_child_by_name(key):
                results[key] = result[key]
        return results

    def flexcache_delete(self):
        """
        Delete FlexCache relationship at destination cluster
        Check job status
        """
        if self.parameters['force_unmount']:
            self.volume_unmount()
        if self.parameters['force_offline']:
            self.volume_offline()
        results = self.flexcache_delete_async()
        status = results.get('result-status')
        if status == 'in_progress' and 'result-jobid' in results:
            if self.parameters['time_out'] == 0:
                # asynchronous call, assuming success!
                return
            error = self.check_job_status(results['result-jobid'])
            if error is None:
                return
            else:
                self.module.fail_json(msg='Error when deleting flexcache: %s' % error)
        self.module.fail_json(msg='Unexpected error when deleting flexcache: results is: %s' % repr(results))

    def check_parameters(self):
        """
        Validate parameters and fail if one or more required params are missing
        """
        missings = list()
        expected = ('origin_volume', 'origin_vserver')
        if self.parameters['state'] == 'present':
            for param in expected:
                if not self.parameters.get(param):
                    missings.append(param)
        if missings:
            plural = 's' if len(missings) > 1 else ''
            msg = 'Missing parameter%s: %s' % (plural, ', '.join(missings))
            self.module.fail_json(msg=msg)

    def apply(self):
        """
        Apply action to FlexCache
        """
        netapp_utils.ems_log_event("na_ontap_flexcache", self.server)
        current = self.flexcache_get()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if cd_action == 'create':
            self.check_parameters()
            self.flexcache_create()
        elif cd_action == 'delete':
            self.flexcache_delete()
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """Execute action"""
    community_obj = NetAppONTAPFlexCache()
    community_obj.apply()


if __name__ == '__main__':
    main()
