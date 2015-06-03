# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Etienne Carrière <etienne.carriere@gmail.com>,2015
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

try:
    import bigsuds
except ImportError:
    bigsuds_found = False
else:
    bigsuds_found = True


def f5_argument_spec():
    return dict(
        server=dict(type='str', required=True),
        user=dict(type='str', required=True),
        password=dict(type='str', aliases=['pass', 'pwd'], required=True, no_log=True),
        validate_certs = dict(default='yes', type='bool'),
        state = dict(type='str', default='present', choices=['present', 'absent']),
        partition = dict(type='str', default='Common')
    )


def f5_parse_arguments(module):
    if not bigsuds_found:
        module.fail_json(msg="the python bigsuds module is required")
    if not module.params['validate_certs']:
        disable_ssl_cert_validation()
    return (module.params['server'],module.params['user'],module.params['password'],module.params['state'],module.params['partition'],module.params['validate_certs'])

def bigip_api(bigip, user, password):
    api = bigsuds.BIGIP(hostname=bigip, username=user, password=password)
    return api

def disable_ssl_cert_validation():
    # You probably only want to do this for testing and never in production.
    # From https://www.python.org/dev/peps/pep-0476/#id29
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context

# Fully Qualified name (with the partition)
def fq_name(partition,name):
    if name is not None and not name.startswith('/'):
        return '/%s/%s' % (partition,name)
    return name

# Fully Qualified name (with partition) for a list 
def fq_list_names(partition,list_names):
    if list_names is None:
        return None
    return map(lambda x: fq_name(partition,x),list_names)


