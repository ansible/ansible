#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Yannig Perré <yannig.perre@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# pylint: disable=invalid-name,dangerous-default-value,duplicate-code

"""This class handle kops communication for Kops Ansible modules"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.utils.vars import merge_hash
import yaml


def to_camel_case(snake_str):
    """
        Convert snake case variable to camel case
        snake_case => snakeCase
        camel_case => camelCase
        min_node   => minNode
    """
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class Kops():
    """handle kops communication by detecting kops bin path and setting kops options"""

    module = None
    kops_cmd = None
    kops_cluster = []
    kops_args = []
    default_module_args = dict(
        state_store=dict(type='str'),
        name=dict(type='str'),
        kops_cmd=dict(type='str'),
    )
    optional_module_args = None
    options_definition = {}

    def __init__(self, additional_module_args=None, options_definition=None):
        """Init Ansible module options"""
        if additional_module_args is not None:
            self.additional_module_args = additional_module_args

        self.module = AnsibleModule(
            argument_spec=dict(
                self.default_module_args,
                **additional_module_args
            )
        )
        if options_definition is not None:
            self.options_definition = options_definition
        self._detect_kops_cmd()


    def _detect_kops_cmd(self):
        """Find where is stored kops binary"""
        self.kops_cmd = self.module.params['kops_cmd']
        if self.kops_cmd is None:
            self.kops_cmd = self.module.get_bin_path('kops')

        if self.kops_cmd is None:
            self.module.fail_json(msg="Unable to locate kops binary")

        if self.module.params['state_store'] is not None:
            self.kops_args += ['--state', self.module.params['state_store']]


    def _get_optional_args(self, tag=None):
        if tag is None:
            return []

        optional_args = []
        # Construct command to launch using options definition
        for k, v in iteritems(self.options_definition):
            if v.get('tag') != tag:
                continue

            if self.module.params[k] is None:
                continue

            if v['type'] == 'bool':
                if bool(self.module.params[k]):
                    optional_args += ['--' + v['alias']]
            else:
                optional_args += ['--' + v['alias'], str(self.module.params[k])]

        return optional_args


    def run_command(self, options, add_optional_args_from_tag=None, data=None):
        """Run kops using kops arguments"""
        optional_args = self._get_optional_args(tag=add_optional_args_from_tag)

        try:
            cmd = [self.kops_cmd] + self.kops_args + options + optional_args
            return self.module.run_command(cmd, data=data)
        # pylint: disable=broad-except
        except Exception as e:
            self.module.fail_json(
                exception=e,
                msg="error while launching kops",
                kops_cmd=self.kops_cmd,
                kops_args=self.kops_args,
                kops_options=options,
                optional_args=optional_args,
                cmd=cmd
            )


    def update_object_definition(self, cluster_name, object_definition, spec_to_update):
        """Update object definition (cluster or instance group)"""
        if not spec_to_update:
            return False

        new_object_definition = merge_hash(object_definition, {'spec': spec_to_update})

        cmd = ["replace", "-f", "-"]
        # Remove timestamp metadata in object definition to avoid parsing issue
        del new_object_definition['metadata']['creationTimestamp']
        (result, _, err) = self.run_command(cmd, data=yaml.dump(new_object_definition))
        if result > 0:
            self.module.fail_json(
                msg="Error while updating object definition",
                kops_error=err,
                object_definition=object_definition,
                spec_to_update=spec_to_update,
                new_object_definition=new_object_definition
            )
        self._update_cluster_definition(cluster_name)

        return True


    def _update_cluster_definition(self, cluster_name):
        """Update cluster definition"""
        cmd = ["update", "cluster", cluster_name, "--yes"]
        (result, update_output, update_operations) = self.run_command(cmd)
        if result > 0:
            self.module.fail_json(
                msg="Error while updating cluster definition",
                error=update_operations
            )
        return (update_output, update_operations)


    def _is_cluster_need_rolling_update(self, cluster_name):
        """Check if cluster need rolling update"""
        cmd = ["rolling-update", "cluster", cluster_name, "--cloudonly"]
        (result, out, err) = self.run_command(cmd)
        if result > 0:
            self.module.fail_json(msg=err)
        return "No rolling-update required." not in out


    def _rolling_update(self, cluster_name):
        """Apply cluster modifications"""
        cmd = ["rolling-update", "cluster", cluster_name, "--yes"]
        if self.module.params['cloudonly']:
            cmd += ["--cloudonly"]

        (result, out, err) = self.run_command(cmd)
        if result > 0:
            self.module.fail_json(msg=err)
        return (out, err)


    def _apply_modifications(self, cluster_name):
        # Update definition then check if rolling update is needed
        (update_output, update_operations) = self._update_cluster_definition(cluster_name)
        changed = self._is_cluster_need_rolling_update(cluster_name)
        results = {
            'changed': changed,
            'cluster_name': cluster_name,
            'update_operations': update_operations,
            'update_output': update_output,
        }
        if changed:
            (out, err) = self._rolling_update(cluster_name)
            results['rolling_update_output'] = out
            results['rolling_update_operations'] = err

        return results


    def get_nodes(self, cluster_name, ig_name=None):
        """Retrieve instance groups (nodes, master)"""
        cmd = ["get", "instancegroups", "--name", cluster_name]
        if ig_name is not None:
            cmd += [ig_name]

        (result, out, err) = self.run_command(cmd + ["-o=yaml"])
        if result > 0:
            self.module.fail_json(msg=err.strip())

        nodes_definitions = {}
        for istance_group in out.split("---\n"):
            definition = yaml.load(istance_group)
            name = definition['metadata']['name']
            nodes_definitions[name] = definition

        if ig_name is not None:
            return nodes_definitions[ig_name]
        return nodes_definitions


    def get_clusters(self, cluster_name=None, retrieve_ig=True,
                     failed_when_not_found=True, full=False):
        """Retrieve defined clusters"""
        cmd = ["get", "clusters"]
        if cluster_name is not None:
            cmd += ["--name", cluster_name]
        if full:
            cmd += ["--full"]

        (result, out, err) = self.run_command(cmd + ["-o=yaml"])
        if result > 0:
            if not failed_when_not_found and cluster_name is not None:
                return {}
            self.module.fail_json(msg=err.strip())

        if full:
            # Clean up returned strings
            out = re.sub(r'^\s*//.*', '', out, flags=re.M)

        clusters_definitions = {}
        for cluster in out.split("---\n"):
            cluster_definition = yaml.load(cluster)
            _cluster_name = cluster_definition['metadata']['name']
            if retrieve_ig:
                cluster_definition["instancegroups"] = self.get_nodes(_cluster_name)
            clusters_definitions[_cluster_name] = cluster_definition
        if cluster_name is not None:
            return clusters_definitions[cluster_name]
        return clusters_definitions
