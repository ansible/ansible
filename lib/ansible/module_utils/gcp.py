# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Franck Cuny <franck.cuny@gmail.com>, 2014
# All rights reserved.
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

import json
import os
import traceback
from distutils.version import LooseVersion

try:
    import libcloud
    HAS_LIBCLOUD_BASE = True
except ImportError:
    HAS_LIBCLOUD_BASE = False

def gcp_connect(module, provider, get_driver, user_agent_product, user_agent_version):
    """Return a Google Cloud Platform connection."""
    if not HAS_LIBCLOUD_BASE:
        module.fail_json(msg='libcloud must be installed to use this module')

    service_account_email = module.params.get('service_account_email', None)
    credentials_file = module.params.get('credentials_file', None)
    pem_file = module.params.get('pem_file', None)
    project_id = module.params.get('project_id', None)

    # If any of the values are not given as parameters, check the appropriate
    # environment variables.
    if not service_account_email:
        service_account_email = os.environ.get('GCE_EMAIL', None)
    if not project_id:
        project_id = os.environ.get('GCE_PROJECT', None)
    if not pem_file:
        pem_file = os.environ.get('GCE_PEM_FILE_PATH', None)
    if not credentials_file:
        credentials_file = os.environ.get('GCE_CREDENTIALS_FILE_PATH', pem_file)

    # If we still don't have one or more of our credentials, attempt to
    # get the remaining values from the libcloud secrets file.
    if service_account_email is None or pem_file is None:
        try:
            import secrets
        except ImportError:
            secrets = None

        if hasattr(secrets, 'GCE_PARAMS'):
            if not service_account_email:
                service_account_email = secrets.GCE_PARAMS[0]
            if not credentials_file:
                credentials_file = secrets.GCE_PARAMS[1]
        keyword_params = getattr(secrets, 'GCE_KEYWORD_PARAMS', {})
        if not project_id:
            project_id = keyword_params.get('project', None)

    # If we *still* don't have the credentials we need, then it's time to
    # just fail out.
    if service_account_email is None or credentials_file is None or project_id is None:
        module.fail_json(msg='Missing GCE connection parameters in libcloud '
                             'secrets file.')
        return None
    else:
        # We have credentials but lets make sure that if they are JSON we have the minimum
        # libcloud requirement met
        try:
            # Try to read credentials as JSON
            with open(credentials_file) as credentials:
                json.loads(credentials.read())
            # If the credentials are proper JSON and we do not have the minimum
            # required libcloud version, bail out and return a descriptive error
            if LooseVersion(libcloud.__version__) < '0.17.0':
                module.fail_json(msg='Using JSON credentials but libcloud minimum version not met. '
                                     'Upgrade to libcloud>=0.17.0.')
                return None
        except ValueError as e:
            # Not JSON
            pass

    try:
        gcp = get_driver(provider)(service_account_email, credentials_file,
                datacenter=module.params.get('zone', None),
                project=project_id)
        gcp.connection.user_agent_append("%s/%s" % (
            user_agent_product, user_agent_version))
    except (RuntimeError, ValueError) as e:
        module.fail_json(msg=str(e), changed=False)
    except Exception as e:
        module.fail_json(msg=unexpected_error_msg(e), changed=False)

    return gcp

def unexpected_error_msg(error):
    """Create an error string based on passed in error."""
    return 'Unexpected response: (%s). Detail: %s' % (str(error), traceback.format_exc(error))
