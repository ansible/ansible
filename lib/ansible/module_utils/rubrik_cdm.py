#
# This code is part of Ansible, but is an independent component.
#
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2018 Rubrik, Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from ansible.module_utils.six import iteritems

try:
    import urllib3
    urllib3.disable_warnings()
except ImportError:
    pass


def sdk_validation():
    """Verify that the rubrik_cdm SDK is present.

    Returns:
        bool -- Flag that determines whether or not the SDK is present.
        class -- The rubrik_cdm module class.
    """

    try:
        import rubrik_cdm
        sdk_present = True
    except BaseException:
        sdk_present = False

    return sdk_present, rubrik_cdm


def connect(rubrik_cdm, module):
    """Helper function to establish inital connectivity to the Rubrik cluster. The function will first attempt
    to read the relevant credentials from environment variables and then if those are not found try to manually provie
    the values through supplied parameters.

    Arguments:
        rubrik_cdm {class} -- The rubrik_cdm module class.
        module {class} -- Ansible module helper class.

    Returns:
        [str] -- Any potential error that may occur during the initial connection.
        [class] -- On success, return rubrik_cdm.Connect
    """

    ansible = module.params

    try:
        rubrik = rubrik_cdm.Connect()
        return rubrik
    except SystemExit as error:
        if "has not been provided" in str(error):
            try:
                ansible["node_ip"]
                ansible["username"]
                ansible["password"]
            except KeyError:
                return "Error: The Rubrik login credentials are missing. Verify the correct env vars are present or provide them through the `provider` param."
        else:
            return str(error)

        try:
            rubrik = rubrik_cdm.Connect(ansible['node_ip'], ansible['username'], ansible['password'])
        except SystemExit as error:
            return str(error)

        return rubrik


login_credentials_spec = {
    'node_ip': dict(),
    'username': dict(),
    'password': dict(no_log=True),
}

rubrik_argument_spec = {
    'provider': dict(type='dict', options=login_credentials_spec),
}


def load_provider_variables(module):
    """Pull the node_ip, username, and password arguments from the provider
    variable
    """

    provider = module.params.get('provider') or dict()
    for key, value in iteritems(provider):
        if key in login_credentials_spec:
            if module.params.get(key) is None and value is not None:
                module.params[key] = value
