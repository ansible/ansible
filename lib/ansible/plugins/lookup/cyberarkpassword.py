# (c) 2017, Edward Nunez <edward.nunez@cyberark.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import os
import subprocess

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_text

CLIPASSWORDSDK_CMD = os.getenv('AIM_CLIPASSWORDSDK_CMD', '/opt/CARKaim/sdk/clipasswordsdk')


class CyberarkPassword:

    def __init__(self, appid=None, query=None, output=None, **kwargs):

        self.appid = appid
        self.query = query
        self.output = output

        # Support for Generic parameters to be able to specify
        # FailRequestOnPasswordChange, Queryformat, Reason, etc.
        self.extra_parms = []
        for key, value in kwargs.items():
            self.extra_parms.append('-p')
            self.extra_parms.append("%s=%s" % (key, value))

        if self.appid is None:
            raise AnsibleError("CyberArk Error: No Application ID specified")
        if self.query is None:
            raise AnsibleError("CyberArk Error: No Vault query specified")

        if self.output is None:
            # If no output is specified, return at least the password
            self.output = "password"
        else:
            # To avoid reference issues/confusion to values, all
            # output 'keys' will be in lowercase.
            self.output = self.output.lower()

        self.delimiter = "@#@"  # Known delimiter to split output results

    def get(self):

        result_dict = {}

        try:
            allParms = [
                CLIPASSWORDSDK_CMD,
                'GetPassword',
                '-p', 'AppDescs.AppID=%s' % self.appid,
                '-p', 'Query=%s' % self.query,
                '-o', self.output,
                '-d', self.delimiter]
            allParms.extend(self.extra_parms)

            credential = subprocess.check_output(allParms)

            if credential and credential.endswith(b'\n'):
                credential = credential[:-1]

            output_names = self.output.split(",")
            output_values = credential.split(self.delimiter)

            for i in range(len(output_names)):
                if output_names[i].startswith("passprops."):
                    if "passprops" not in result_dict:
                        result_dict["passprops"] = {}
                    output_prop_name = output_names[i][10:]
                    result_dict["passprops"][output_prop_name] = output_values[i]
                else:
                    result_dict[output_names[i]] = output_values[i]

        except subprocess.CalledProcessError as e:
            raise AnsibleError(e.output)
        except OSError as e:
            raise AnsibleError("ERROR - AIM not installed or clipasswordsdk not in standard location. ERROR=(%s) => %s " % (to_text(e.errno), e.strerror))

        return [result_dict]


class LookupModule(LookupBase):

    """
    USAGE: {{lookup('cyberarkpassword', appid='Application1', query='safe=Safe1;Folder=root;Object=User1',
                    output='password,passprops.username,passprops.address' [, extra_parms])}}

    It Requires CyberArk AIM Installed, and /opt/CARKaim/sdk/clipasswordsdk in place or set environment variable AIM_CLIPASSWORDSDK_CMD to the AIM
    CLI Password SDK executable.

     Args:
         appid (str): Defines the unique ID of the application that is issuing the password request.
         query (str): Describes the filter criteria for the password retrieval.
         output (str): Specifies the desired output fields separated by commas. They could be: Password, PassProps.<property>, PasswordChangeInProcess
         Optionally, you can specify extra parameters recognized by clipasswordsdk (like FailRequestOnPasswordChange, Queryformat, Reason, etc.)

     Returns:
         dict: A dictionary with 'password' as key for the credential, passprops.<property>, passwordchangeinprocess
               If the specified property does not exist for this password, the value <na> will be returned for this property.
               If the value of the specified property is empty, <null> will be returned.


    for extra_parms values please check parameters for clipasswordsdk in CyberArk's "Credential Provider and ASCP Implementation Guide"

    For Ansible on windows, please change the -parameters (-p, -d, and -o) to /parameters (/p, /d, and /o) and change the location of CLIPasswordSDK.exe

    cyberarkpassword lookup can not be used as a source for loop
    """

    def run(self, terms, variables=None, **kwargs):

        cyberark_conn = CyberarkPassword(**kwargs)
        result = cyberark_conn.get()
        return result
