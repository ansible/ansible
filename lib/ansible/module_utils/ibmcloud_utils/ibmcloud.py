#!/usr/bin/env python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import jinja2
from textwrap import dedent
import os
import sys
import shutil
import re
import json
from datetime import datetime
from ansible.module_utils._text import to_text
from ansible.module_utils.six import iteritems
from ansible.module_utils.six import ensure_str
from ansible.module_utils.six import string_types

DEFAULT_TF_DIR = '/var/tmp/ansible/ibmcloud/'
RM_OBJECT_SUBDIRS = True


def ibmcloud_terraform(
        resource_type,
        tf_type,
        parameters,
        ibm_provider_version,
        tl_required_params,
        tl_all_params,
        terraform_dir=DEFAULT_TF_DIR):
    """
    Use Terraform to interact with IBM Cloud resources

    Args:
        resource_type (str): Resource type (e.g.: 'ibm_is_vpc')
        tf_type (str): Terraform block type ('resource' or 'data')
        parameters (dict): Resource parameter dictionary
        ibm_provider_version (str): IBM Cloud Terraform provider version
        tl_required_params (list of tuple): Top Level Parameters
            required by TF. Each tuple consists of two strings:
            (<name>, <type>)
        tl_all_params (list): Top Level Parameters supported by TF.
            Each tuple consists of two strings:(<name>, <type>)
        terraform_dir (str, optional): Path to Terraform working
                                       directory

    Returns:
        dict: Ansible 'result' dictionary. The 'resource' key contains
              the resource's primary.attributes dictionary retrieved
              from tfstate data. e.g.:
              {
                  'changed': <bool>,
                  'resource': <dict>,
                  'rc': <int>,
                  'stdout': <str>,
                  'stderr': <str>,
                  'warnings': <list of str>
              }
    """
    # Initialize environment variable mapping
    # Import any env vars set within ansible
    env = dict(os.environ)
    # Set 'no_log' provider parameters via env vars to prevent
    # exposing key in plaintext provider file
    if ('ibmcloud_api_key' in parameters and
            parameters['ibmcloud_api_key'] is not None):
        env['IC_API_KEY'] = parameters['ibmcloud_api_key']
    if ('iaas_classic_username' in parameters and
            parameters['iaas_classic_username'] is not None):
        env['IAAS_CLASSIC_USERNAME'] = parameters['iaas_classic_username']
    if ('iaas_classic_api_key' in parameters and
            parameters['iaas_classic_api_key'] is not None):
        env['IAAS_CLASSIC_API_KEY'] = parameters['iaas_classic_api_key']

    # Initialize result dictionary
    result = {
        'changed': False,
        'resource': {},
        'rc': 0,
        'stdout': '',
        'stderr': '',
        'warnings': []
    }

    # Initialize Terraform object
    terraform = Terraform(
        parameters,
        terraform_dir,
        ibm_provider_version,
        env=env)

    resource = Resource(
        resource_type,
        tf_type,
        parameters,
        tl_required_params,
        tl_all_params)
    terraform.add_resource(resource)
    terraform.init()

    if tf_type == 'data':
        result['rc'], result['stdout'], result['stderr'] = (
            terraform.apply())
        result['resource'] = terraform.get_tfstate_attributes(resource.target)

    elif tf_type == 'resource':
        resource_absent = False

        # Attempt to import resource tfstate if 'id' is given
        if resource.tf_type == 'resource' and resource.id_ is not None:
            if not terraform.set_existing_args(resource):
                resource_absent = True
                if resource.parameters['state'] == 'available':
                    result['warnings'].append(
                        "Unable to import resource id '{}' (type {}). "
                        "Attempting to create new resource."
                        .format(resource.id_, resource.resource_type))

        # Create/update resource
        if resource.parameters['state'] == 'available':
            result['rc'], result['stdout'], result['stderr'] = (
                terraform.apply())
            # Determine 'changed' result value
            if (result['rc'] == 0 and not re.search(
                    '0 added, 0 changed, 0 destroyed', result['stdout'])):
                result['changed'] = True
            # Load resource return data
            result['resource'] = terraform.get_tfstate_attributes(
                resource.target)

        # Remove resource
        elif resource.parameters['state'] == 'absent':
            if not resource_absent:
                result['rc'], result['stdout'], result['stderr'] = (
                    terraform.destroy(None))
                # Determine 'changed' result value
                if (result['rc'] == 0 and not re.search(
                        'Resources: 0 destroyed', result['stdout'])):
                    result['changed'] = True

    terraform.cleanup(result, RM_OBJECT_SUBDIRS)
    return result


def to_unicode(string):
    """
    Ensure string is unicode

    Args:
        string (str or bytes): String can be type 'str' or 'bytes'

    Returns:
        str: Unicode string (utf-8 encoding)
    """
    try:
        unicode_string = to_text(string, errors='surrogate_or_strict')
    except UnicodeError:
        unicode_string = string
    return unicode_string


def run_process(command, cwd=None, env=None):
    """
    Run system subprocess

    Args:
        command (str): Full command string
        cwd (str, optional): Process current working directory
        env (dict, optional): Mapping of environment variables

    Returns:
        (int, str, str): Tuple with (return code, stdout, stderr)
    """
    import subprocess
    import shlex

    args = shlex.split(command)

    process = subprocess.Popen(
        args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    returncode = process.returncode

    return (returncode, to_unicode(stdout), to_unicode(stderr))


class Resource:
    """
    TODO: Docstring

    Args:
        resource_type (str): Resouce type (e.g.: 'ibm_is_vpc')
        tf_type (str): Terraform block type ('resource' or 'data')
        parameters (dict): Resource parameter dictionary
        tl_required_params (list of tuple): Top Level Parameters
            required by TF. Each tuple consists of two strings:
            (<name>, <type>)
        tl_all_params (list): Top Level Parameters supported by TF.
            Each tuple consists of two strings:(<name>, <type>)
    """
    def __init__(
            self,
            resource_type,
            tf_type,
            parameters,
            tl_required_params,
            tl_all_params):
        self.resource_type = resource_type
        self.tf_type = tf_type
        self.parameters = parameters
        self.tl_required_params = tl_required_params
        self.tl_all_params = tl_all_params

        # Terraform requires a name, if no 'name' paramter set use
        # timestamp
        if 'name' in self.parameters and self.parameters['name'] is not None:
            self.tf_name = self.parameters['name']
        else:
            self.tf_name = (
                "ansible_" + datetime.now().strftime("%Y%m%d-%H%M%S"))

        # Target is used to identify resource within Terraform
        self.target = '{}.{}'.format(
            self.resource_type, self.tf_name)
        # if self.tf_type == 'data':
        #     self.target = 'data.' + self.target

        self.id_ = None
        if 'id' in parameters:
            self.id_ = parameters['id']


class Terraform:
    """
    Interaction with Terraform

    Constructor looks for Terraform executable and IBM Cloud Terraform
    provider that satisfy version requirements passed into arguments. If
    specified versions are not found they will be downloaded and
    installed within the 'terraform_dir'.

    Args:
        parameters (dict): Resource parameter dictionary
        terraform_dir (str): Terraform working directory
        ibm_provider_version (str): IBM Cloud Terraform provider version
        terraform_version (str, optional): Terraform version. TODO: If
                                           not specified version is set
                                           via table lookup.
        env (dict, optional): Mapping of environment variables
    """
    IBM_PROVIDER_BASE_URL = (
        "https://github.com"
        "/IBM-Cloud/terraform-provider-ibm/releases/download/")
    TERRAFORM_BASE_URL = "https://releases.hashicorp.com/terraform/"
    TF_PROVIDER_TEMPLATE = """\
    provider "ibm" {{
        version          = ">= {ibm_provider_version}"
    {{% if generation is not none %}}
        generation       = "{{{{ generation }}}}"
    {{% endif %}}
    {{% if region is not none %}}
        region           = "{{{{ region }}}}"
    {{% endif %}}
    {{% if zone is not none %}}
        zone             = "{{{{ zone }}}}"
    {{% endif %}}
    {{% if function_namespace is not none %}}
        function_namespace = "{{{{ function_namespace }}}}"
    {{% endif %}}
    }}
    """

    def __init__(
            self,
            parameters,
            terraform_dir,
            ibm_provider_version,
            terraform_version='0.12.20',
            env=None):

        self.generation = None
        if 'generation' in parameters:
            self.generation = parameters['generation']
        self.region = None
        if 'region' in parameters:
            self.region = parameters['region']
        self.zone = None
        if 'zone' in parameters:
            self.zone = parameters['zone']
        self.function_namespace = None
        if 'function_namespace' in parameters:
            self.function_namespace = parameters['function_namespace']
        self.terraform_dir = terraform_dir
        self.ibm_provider_version = ibm_provider_version
        self.terraform_version = terraform_version
        self.executable = os.path.join(terraform_dir, 'terraform')
        self.env = env
        self.platform = sys.platform
        if self.platform.startswith('linux'):
            self.platform = 'linux'

        # Create a subdirectory in 'terraform_dir' to use as a working
        # directory for a single object instance
        def tf_subdir_path():
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
            return os.path.join(self.terraform_dir, timestamp)
        path = tf_subdir_path()
        while os.path.isdir(path):
            path = tf_subdir_path()
        else:
            self.directory = path
            os.makedirs(self.directory)

        # Create provider file in object subdir
        self._render_provider_file()

        # Check for existing Terraform executable
        if os.path.isfile(self.executable):
            returncode, stdout, stderr = run_process(
                '{} version'.format(self.executable))
            try:
                existing_version = re.findall(
                    r"Terraform v(\d+\.\d+\.\d+)\n", stdout)[0]
            except IndexError:
                existing_version = None

        # Download and install Terraform if desired version not found
        if (not os.path.isfile(self.executable) or
                existing_version != self.terraform_version):
            self._install_terraform()

        # Check for existing IBM Cloud provider
        provider_found = False
        for item in os.listdir(self.terraform_dir):
            if item.startswith('terraform-provider-ibm_v'):
                if item == 'terraform-provider-ibm_v' + ibm_provider_version:
                    provider_found = True
                else:
                    os.remove(os.path.join(self.terraform_dir, item))

        # Download and install IBM Cloud provider if desired version not
        # found
        if not provider_found:
            self._install_ibmcloud_tf_provider()

        # Initialize Terraform
        self.init()
        self.refresh()

    def _download_extract_zip(self, url):
        from ansible.module_utils.urls import open_url
        from ansible.module_utils.six import BytesIO
        from zipfile import ZipFile
        if not os.path.isdir(self.directory):
            os.makedirs(self.directory)
        resp = open_url(url)
        zip_archive = ZipFile(BytesIO(resp.read()))
        zip_archive.extractall(path=self.terraform_dir)

    def _install_terraform(self):
        filename = 'terraform'
        filepath = os.path.join(self.terraform_dir, filename)
        if os.path.isfile(filepath):
            os.remove(filepath)
        self._download_extract_zip(
            "{0}{1}/terraform_{1}_{2}_amd64.zip".format(
                self.TERRAFORM_BASE_URL, self.terraform_version, self.platform))
        os.chmod(filepath, 0o755)
        self.executable = filepath

    def _install_ibmcloud_tf_provider(self):
        filename = 'terraform-provider-ibm_v' + self.ibm_provider_version
        self._download_extract_zip(
            "{0}v{1}/{2}_amd64.zip".format(
                self.IBM_PROVIDER_BASE_URL, self.ibm_provider_version, self.platform))
        os.chmod(os.path.join(self.terraform_dir, filename), 0o755)

    def _render_provider_file(self):
        # Render terraform provider file
        templateEnv = jinja2.Environment(trim_blocks=True)
        provider_template = templateEnv.from_string(
            dedent(self.TF_PROVIDER_TEMPLATE.format(
                ibm_provider_version=self.ibm_provider_version)))
        with open(
                os.path.join(self.directory, 'provider.tf'), 'w') as file_obj:
            file_obj.write(provider_template.render(
                {'generation': self.generation,
                 'region': self.region,
                 'zone': self.zone,
                 'function_namespace': self.function_namespace}))
            file_obj.write("\n")

    def cleanup(self, result, rm_subdir):
        """
        Clean up Terraform environment

        Args:
            result (dict): Ansible result dictionary. If returncode is
                           non-zero subdir is saved, renamed with
                           '_failed' suffix, and the result is written
                           to file.
            rm_subdir (bool): If True subdir and all contents are
                              removed
        """
        if os.path.isdir(self.directory):
            if result['rc'] != 0:
                result_path = os.path.join(
                    self.directory, 'ansible_result.json')
                with open(result_path, 'w') as file_obj:
                    file_obj.write(json.dumps(result))
                os.rename(self.directory, self.directory + '_fail')
            elif rm_subdir:
                shutil.rmtree(self.directory)

    def init(self):
        """
        Run Terraform init to 'Initialize a Terraform working directory'

        Returns:
            (int, str, str): Tuple with (return code, stdout, stderr)
        """
        command = '{} init -no-color'.format(self.executable)
        return run_process(command, cwd=self.directory, env=self.env)

    def refresh(self):
        """
        Run Terraform refresh to 'Update local state file against real
        resources'

        Returns:
            (int, str, str): Tuple with (return code, stdout, stderr)
        """
        returncode, stdout, stderr = self.init()
        if returncode > 0:
            return (returncode, stdout, stderr)
        command = '{} refresh -no-color'.format(self.executable)
        return run_process(command, cwd=self.directory, env=self.env)

    def apply(self, target=None):
        """
        Run Terraform apply to 'Build or change infrastructure'

        Args:
            target (str, optional): Resource Address to target

        Returns:
            (int, str, str): Tuple with (return code, stdout, stderr)
        """
        returncode, stdout, stderr = self.init()
        if returncode > 0:
            return (returncode, stdout, stderr)
        command = '{} apply '.format(self.executable)
        if target is not None:
            command += '-target={} '.format(target)
        command += '-no-color -auto-approve'
        return run_process(command, cwd=self.directory, env=self.env)

    def destroy(self, target):
        """
        Run Terraform destroy to 'Destroy Terraform-managed
        infrastructure'

        Args:
            target (str): Resource Address to target

        Returns:
            (int, str, str): Tuple with (return code, stdout, stderr)
        """
        command = '{} destroy '.format(self.executable)
        if target is not None:
            command += '-target={} '.format(target)
        command += '-no-color -auto-approve'
        return run_process(command, cwd=self.directory, env=self.env)

    def import_(self, target, resource_id):
        """
        Run Terraform import to 'Import existing infrastructure into
        Terraform'

        Args:
            target (str, optional): Resource Address to target

        Returns:
            (int, str, str): Tuple with (return code, stdout, stderr)
        """
        command = '{} import {} {} -no-color'.format(
            self.executable, target, resource_id)
        return run_process(command, cwd=self.directory, env=self.env)

    def set_existing_args(self, resource):
        """
        Set any missing required arguments for an existing resource.
        This method requires the 'resource.id_' attribute to be set in
        order to call the 'self.import()' method.

        Args:
            resource (Resource): Resource object

        Returns:
            bool: True if TF is able to import the resource ID, else false
        """
        def filter_args(args):
            if isinstance(args, string_types):
                return args
            elif isinstance(args, list):
                safe_list = []
                for arg in args:
                    if isinstance(arg, dict):
                        _dict = {}
                        if 'name' in arg:
                            _dict['name'] = arg['name']
                        if 'subnet' in arg:
                            _dict['subnet'] = arg['subnet']
                        safe_list.append(_dict)
                    else:
                        safe_list.append(arg)
                return safe_list
            elif isinstance(args, dict):
                return args

        return_code, _, _ = self.import_(resource.target, resource.id_)
        if return_code != 0:
            return False
        existing_args = self.get_tfstate_attributes(resource.target)
        for arg, arg_type in resource.tl_required_params:
            if resource.parameters[arg] is None:
                try:
                    resource.parameters[arg] = filter_args(existing_args[arg])
                except KeyError:
                    if arg_type == 'str':
                        resource.parameters[arg] = ''
                    elif arg_type == 'list':
                        resource.parameters[arg] = []
                    elif arg_type == 'dict':
                        resource.parameters[arg] = {}
        self.add_resource(resource)
        return True

    def add_resource(self, resource):
        """
        Add resource to Terraform environment.

        Args:
            resource (Resource): Resource object
        """
        # Generate TF resource block
        tf_block = (
            '{} {} "{}" '.format(
                resource.tf_type,
                resource.resource_type,
                resource.tf_name) + '{\n' +
            fmt_tf_block(
                resource.parameters,
                indent_count=1,
                indent_spaces=2,
                validate_tl_params=resource.tl_all_params) + '}\n')

        # Write terraform resource block to file
        resource_file = '{}_{}.tf'.format(
            resource.resource_type, resource.tf_name)
        with open(
                os.path.join(self.directory, resource_file), 'w') as file_obj:
            file_obj.write(tf_block)

    def get_tfstate_attributes(self, target):
        """
        Retrieve resource primary.attributes dictionary from Terraform
        tfstate data.

        Args:
            target (str): Resource Address to target

        Returns:
            dict: Resource/DataSource return data structure, empty dict
                  if no 'terraform.tfstate' file exists
        """
        def str_keys(dictionary):
            output = {}
            for key, value in iteritems(attributes):
                output[ensure_str(key)] = value
            return output

        # Load 'tfstate' json file to extract result data
        if not os.path.isfile(
                os.path.join(self.directory, 'terraform.tfstate')):
            return dict()
        with open(
                os.path.join(self.directory, 'terraform.tfstate')) as file_obj:
            tfstate = json.load(file_obj)

        _type, _name = target.split('.', 1)
        for resource in tfstate['resources']:
            if resource['name'] == _name and resource['type'] == _type:
                attributes = resource['instances'][0]['attributes']
                break
        else:
            return {'_type': _type, '_name': _name, 'target': target}

        try:
            expanded_attributes = dict()
            for key, value in iteritems(attributes):
                if key.endswith('.#'):
                    continue
                sub_keys = key.split('.')
                nested_pointer = expanded_attributes
                for index, sub_key in enumerate(sub_keys):
                    if sub_key.isdigit():
                        sub_key = int(sub_key)
                        if sub_key > 10000:
                            sub_key = len(nested_pointer)
                            nested_pointer += ['']
                        elif sub_key >= len(nested_pointer):
                            nested_pointer += (
                                [''] * (
                                    int(sub_key) + 1 - len(nested_pointer)))
                        elif type(nested_pointer[sub_key]) is not str:
                            nested_pointer = nested_pointer[sub_key]
                            continue

                    if (type(nested_pointer) is list and
                            sub_key in nested_pointer):
                        nested_pointer = nested_pointer[sub_key]
                        continue

                    if (type(nested_pointer) is dict and
                            sub_key in nested_pointer):
                        nested_pointer = nested_pointer[sub_key]
                        continue

                    if (index + 1) == len(sub_keys):
                        nested_pointer[sub_key] = value
                    if (index + 1) < len(sub_keys):
                        if sub_keys[index + 1].isdigit():
                            nested_pointer[sub_key] = list()
                        else:
                            nested_pointer[sub_key] = dict()
                        nested_pointer = nested_pointer[sub_key]

            return str_keys(expanded_attributes)
        except KeyError:
            return str_keys(attributes)

    @staticmethod
    def parse_stderr(stderr):
        """
        Parse Terraform error messages into an easily readable message.
        The return string is intended to be used as the error message
        passed to the 'AnsibleModule.exit_json' method.

        Args:
            stderr (str): Stderr output from a Terraform failure

        Returns:
            str: Error message formatted for human readability
        """
        import json
        errors = dict()
        for line in stderr.splitlines():
            if line.strip().startswith('*'):
                resource, msg = line.strip().split(':', 1)
                resource = resource.replace('*', '').strip()
                if resource not in errors:
                    errors[resource] = []
                try:
                    err_msg = json.loads(msg.strip())
                    if 'errors' in err_msg:
                        errors[resource].append(err_msg['errors'])
                    else:
                        errors[resource].append([err_msg])
                except ValueError:
                    if not re.search(r'\d+ error\S* occurred:', msg):
                        if ':' in msg:
                            key, value = msg.strip().split(':', 1)
                        else:
                            key, value = '', msg
                        errors[resource].append([{key: value.strip()}])
        formatted_msg = ''
        count = 1
        for resource, err_list in errors.items():
            first = True
            formatted_msg += "Errors for resource: {}\n".format(resource)
            for errors in err_list:
                for error in errors:
                    for key, value in error.items():
                        if first:
                            formatted_msg += "   {}) ".format(str(count))
                            first = False
                        else:
                            formatted_msg += "      "
                        formatted_msg += "{}: {}\n".format(key, value)

        return formatted_msg


def fmt_tf_block(
        arg_dict,
        indent_count=0,
        indent_spaces=2,
        filter_None=True,
        validate_tl_params=[]):
    """
    Format a dictionary of configuration arguments into Terraform
    block syntax.

    Args:
        arg_dict (dict): Dictionary of configuration arguments
        indent_count (int, optional): Starting number of indentations
        indent_space (int, optional): Number of spaces per indentation
        filter_None (bool, optional): Do not print any 'None' values
        validate_tl_params (list, optional): Only allow top level
            parameters found on this list. If list is empty any top
            level parameter is allowed.

    Returns:
        str: Terraform block format
    """
    output = ''

    def indent(extra_count=0):
        return ' ' * ((indent_count + extra_count) * indent_spaces)

    for key, value in arg_dict.items():
        if len(validate_tl_params) > 0 and key not in validate_tl_params:
            continue
        if isinstance(value, dict):
            output += indent() + key + ' {\n'
            output += fmt_tf_block(value, indent_count + 1, indent_spaces)
            output += indent(-1) + '}\n'
        elif isinstance(value, list):
            if len(value) >= 1 and isinstance(value[0], dict):
                output += indent() + key + ' {\n'
                for item in value:
                    output += fmt_tf_block(
                        item, indent_count + 1, indent_spaces)
                    output += indent(1) + '}\n'
            else:
                output += indent() + key + ' = ' + json.dumps(value) + '\n'
        elif (isinstance(value, bool) or (
                isinstance(value, string_types) and
                value.lower() in ['true', 'false'])):
            output += indent() + key + ' = ' + str(value).lower() + '\n'
        elif value is None and filter_None:
            pass
        else:
            output += indent() + key + ' = ' + json.dumps(value) + '\n'

    return output
