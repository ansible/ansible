# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
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

from distutils.version import LooseVersion

AZURE_LOCATIONS = ['East Asia',
                   'Southeast Asia',
                   'Brazil South',
                   'North Europe',
                   'West Europe',
                   'Japan West',
                   'East US',
                   'South Central US',
                   'West US']


def get_azure_creds(module):
    # Check modul args for credentials, then check environment vars
    subscription_id = module.params.get('subscription_id')
    management_cert_path = module.params.get('management_cert_path')

    if not subscription_id:
        subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
        management_cert_path = os.environ['AZURE_CERT_PATH']

    return subscription_id, management_cert_path

def get_azure_sms(subscription_id, management_cert_path, wait_timeout_redirects):
    if LooseVersion(windows_azure.__version__) <= "0.8.0":
        # wrapper for handling redirects which the sdk <= 0.8.0 is not following
        return AzureSDKWrapper(ServiceManagementService(subscription_id, management_cert_path), wait_timeout_redirects)
    else:
        return ServiceManagementService(subscription_id, management_cert_path)


def wait_for_completion(azure, promise, wait_timeout, msg):
    if not promise: return
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time():
        operation_result = azure.get_operation_status(promise.request_id)
        time.sleep(5)
        if operation_result.status == "Succeeded":
            return

    raise WindowsAzureError('Timed out waiting for async operation ' + msg + ' "' + str(promise.request_id) + '" to complete.')



class AzureSDKWrapper(object):
    def __init__(self, obj, wait_timeout):
        self.other = obj
        self.wait_timeout = wait_timeout

    def __getattr__(self, name):
        if hasattr(self.other, name):
            func = getattr(self.other, name)
            return lambda *args, **kwargs: self._wrap(func, args, kwargs)
        raise AttributeError(name)

    def _wrap(self, func, args, kwargs):
        return self._handle_temporary_redirects(lambda: func(*args, **kwargs))

    def _handle_temporary_redirects(self, f):
        wait_timeout = time.time() + self.wait_timeout
        while wait_timeout > time.time():
            try:
                return f()
            except WindowsAzureError as e:
                if not str(e).lower().find("temporary redirect") == -1:
                    time.sleep(5)
                    pass
                else:
                    raise e

