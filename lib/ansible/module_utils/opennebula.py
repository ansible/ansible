#
# Copyright 2018 www.privaz.io Valletech AB
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)


import time
import ssl
from os import environ
from ansible.module_utils.six import string_types
from ansible.module_utils.basic import AnsibleModule


HAS_PYONE = True

try:
    from pyone import OneException
    from pyone.server import OneServer
except ImportError:
    OneException = Exception
    HAS_PYONE = False


class OpenNebulaModule:
    """
    Base class for all OpenNebula Ansible Modules.
    This is basically a wrapper of the common arguments, the pyone client and
    some utility methods.
    """

    common_args = dict(
        api_url=dict(type='str', aliases=['api_endpoint'], default=environ.get("ONE_URL")),
        api_username=dict(type='str', default=environ.get("ONE_USERNAME")),
        api_password=dict(type='str', no_log=True, aliases=['api_token'], default=environ.get("ONE_PASSWORD")),
        validate_certs=dict(default=True, type='bool'),
        wait_timeout=dict(type='int', default=300),
    )

    def __init__(self, argument_spec, supports_check_mode=False, mutually_exclusive=None):

        module_args = OpenNebulaModule.common_args
        module_args.update(argument_spec)

        self.module = AnsibleModule(argument_spec=module_args,
                                    supports_check_mode=supports_check_mode,
                                    mutually_exclusive=mutually_exclusive)
        self.result = dict(changed=False,
                           original_message='',
                           message='')
        self.one = self.create_one_client()

        self.resolved_parameters = self.resolve_parameters()

    def create_one_client(self):
        """
        Creates an XMLPRC client to OpenNebula.

        Returns: the new xmlrpc client.

        """

        # context required for not validating SSL, old python versions won't validate anyway.
        if hasattr(ssl, '_create_unverified_context'):
            no_ssl_validation_context = ssl._create_unverified_context()
        else:
            no_ssl_validation_context = None

        # Check if the module can run
        if not HAS_PYONE:
            self.fail("pyone is required for this module")

        if self.module.params.get("api_url"):
            url = self.module.params.get("api_url")
        else:
            self.fail("Either api_url or the environment variable ONE_URL must be provided")

        if self.module.params.get("api_username"):
            username = self.module.params.get("api_username")
        else:
            self.fail("Either api_username or the environment vairable ONE_USERNAME must be provided")

        if self.module.params.get("api_password"):
            password = self.module.params.get("api_password")
        else:
            self.fail("Either api_password or the environment vairable ONE_PASSWORD must be provided")

        session = "%s:%s" % (username, password)

        if not self.module.params.get("validate_certs") and "PYTHONHTTPSVERIFY" not in environ:
            return OneServer(url, session=session, context=no_ssl_validation_context)
        else:
            return OneServer(url, session)

    def close_one_client(self):
        """
        Close the pyone session.
        """
        self.one.server_close()

    def fail(self, msg):
        """
        Utility failure method, will ensure pyone is properly closed before failing.
        Args:
            msg: human readable failure reason.
        """
        if hasattr(self, 'one'):
            self.close_one_client()
        self.module.fail_json(msg=msg)

    def exit(self):
        """
        Utility exit method, will ensure pyone is properly closed before exiting.

        """
        if hasattr(self, 'one'):
            self.close_one_client()
        self.module.exit_json(**self.result)

    def resolve_parameters(self):
        """
        This method resolves parameters provided by a secondary ID to the primary ID.
        For example if cluster_name is present, cluster_id will be introduced by performing
        the required resolution

        Returns: a copy of the parameters that includes the resolved parameters.

        """

        resolved_params = dict(self.module.params)

        if 'cluster_name' in self.module.params:
            clusters = self.one.clusterpool.info()
            for cluster in clusters.CLUSTER:
                if cluster.NAME == self.module.params.get('cluster_name'):
                    resolved_params['cluster_id'] = cluster.ID

        return resolved_params

    def is_parameter(self, name):
        """
        Utility method to check if a parameter was provided or is resolved
        Args:
            name: the parameter to check
        """
        if name in self.resolved_parameters:
            return self.get_parameter(name) is not None
        else:
            return False

    def get_parameter(self, name):
        """
        Utility method for accessing parameters that includes resolved ID
        parameters from provided Name parameters.
        """
        return self.resolved_parameters.get(name)

    def get_host_by_name(self, name):
        '''
        Returns a host given its name.
        Args:
            name: the name of the host

        Returns: the host object or None if the host is absent.

        '''
        hosts = self.one.hostpool.info()
        for h in hosts.HOST:
            if h.NAME == name:
                return h
        return None

    def get_cluster_by_name(self, name):
        """
        Returns a cluster given its name.
        Args:
            name: the name of the cluster

        Returns: the cluster object or None if the host is absent.
        """

        clusters = self.one.clusterpool.info()
        for c in clusters.CLUSTER:
            if c.NAME == name:
                return c
        return None

    def get_template_by_name(self, name):
        '''
        Returns a template given its name.
        Args:
            name: the name of the template

        Returns: the template object or None if the host is absent.

        '''
        templates = self.one.templatepool.info()
        for t in templates.TEMPLATE:
            if t.NAME == name:
                return t
        return None

    def cast_template(self, template):
        """
        OpenNebula handles all template elements as strings
        At some point there is a cast being performed on types provided by the user
        This function mimics that transformation so that required template updates are detected properly
        additionally an array will be converted to a comma separated list,
        which works for labels and hopefully for something more.

        Args:
            template: the template to transform

        Returns: the transformed template with data casts applied.
        """

        # TODO: check formally available data types in templates
        # TODO: some arrays might be converted to space separated

        for key in template:
            value = template[key]
            if isinstance(value, dict):
                self.cast_template(template[key])
            elif isinstance(value, list):
                template[key] = ', '.join(value)
            elif not isinstance(value, string_types):
                template[key] = str(value)

    def requires_template_update(self, current, desired):
        """
        This function will help decide if a template update is required or not
        If a desired key is missing from the current dictionary an update is required
        If the intersection of both dictionaries is not deep equal, an update is required
        Args:
            current: current template as a dictionary
            desired: desired template as a dictionary

        Returns: True if a template update is required
        """

        if not desired:
            return False

        self.cast_template(desired)
        intersection = dict()
        for dkey in desired.keys():
            if dkey in current.keys():
                intersection[dkey] = current[dkey]
            else:
                return True
        return not (desired == intersection)

    def wait_for_state(self, element_name, state, state_name, target_states,
                       invalid_states=None, transition_states=None,
                       wait_timeout=None):
        """
        Args:
            element_name: the name of the object we are waiting for: HOST, VM, etc.
            state: lambda that returns the current state, will be queried until target state is reached
            state_name: lambda that returns the readable form of a given state
            target_states: states expected to be reached
            invalid_states: if any of this states is reached, fail
            transition_states: when used, these are the valid states during the transition.
            wait_timeout: timeout period in seconds. Defaults to the provided parameter.
        """

        if not wait_timeout:
            wait_timeout = self.module.params.get("wait_timeout")

        start_time = time.time()

        while (time.time() - start_time) < wait_timeout:
            current_state = state()

            if current_state in invalid_states:
                self.fail('invalid %s state %s' % (element_name, state_name(current_state)))

            if transition_states:
                if current_state not in transition_states:
                    self.fail('invalid %s transition state %s' % (element_name, state_name(current_state)))

            if current_state in target_states:
                return True

            time.sleep(self.one.server_retry_interval())

        self.fail(msg="Wait timeout has expired!")

    def run_module(self):
        """
        trigger the start of the execution of the module.
        Returns:

        """
        try:
            self.run(self.one, self.module, self.result)
        except OneException as e:
            self.fail(msg="OpenNebula Exception: %s" % e)

    def run(self, one, module, result):
        """
        to be implemented by subclass with the actual module actions.
        Args:
            one: the OpenNebula XMLRPC client
            module: the Ansible Module object
            result: the Ansible result
        """
        raise NotImplementedError("Method requires implementation")
