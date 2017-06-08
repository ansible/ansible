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

import subprocess

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

CLIPASSWORDSDK_CMD = '/opt/CARKaim/sdk/clipasswordsdk'
if os.getenv('AIM_CLIPASSWORDSDK_CMD') is not None:
    CLIPASSWORDSDK_CMD = os.environ['AIM_CLIPASSWORDSDK_CMD']


class CyberarkPassword:

    def __init__(self, **kwargs):

        self.appid = kwargs.pop('appid', None)
        self.query = kwargs.pop('query', None)
        self.output = kwargs.pop('output', None)

        # Support for Generic parameters to be able to specify
        # FailRequestOnPasswordChange, Queryformat, Reason, etc.
        self.extraParms = []
        for key, value in kwargs.items():
            self.extraParms.append('-p')
            self.extraParms.append(key + "=" + value)

        if self.appid is None:
            raise AnsibleError("No Application ID specified")
        if self.query is None:
            raise AnsibleError("No Vault query specified")

        if self.output is None:
            # If no output is specified, return at least the password
            self.output = "password"
        else:
            # To avoid reference issues/confusion to values, all
            # output 'keys' will be in lowercase.
            self.output = self.output.lower()

        self.delimiter = "@#@"  # Known delimiter to split output results

    def get(self):

        resultDict = {}

        try:
            allParms = [
                CLIPASSWORDSDK_CMD,
                'GetPassword',
                '-p',
                'AppDescs.AppID=' +
                self.appid,
                '-p',
                'Query=' +
                self.query,
                '-o',
                self.output,
                '-d',
                self.delimiter]
            allParms.extend(self.extraParms)

            credential = subprocess.check_output(allParms)

            if len(credential) > 0 and credential.endswith("\n"):
                credential = credential[:-1]

            outputNames = self.output.split(",")
            outputValues = credential.split(self.delimiter)

            for i in range(len(outputNames)):
                if outputNames[i].startswith("passprops."):
                    if "passprops" not in resultDict:
                        resultDict["passprops"] = {}
                    outputPropName = outputNames[i][10:]
                    resultDict["passprops"][outputPropName] = outputValues[i]
                else:
                    resultDict[outputNames[i]] = outputValues[i]

        except subprocess.CalledProcessError as e:
            raise AnsibleError(e.output)
        except OSError as e:
            raise AnsibleError("ERROR - AIM not installed or clipasswordsdk not in standard location. ERROR=(" + to_text(e.errno) + ") => " + e.strerror)

        return [resultDict]


class LookupModule(LookupBase):

    """
    USAGE: {{lookup('cyberarkpassword', appid='Application1', query='safe=Safe1;Folder=root;Object=User1',
                    output='password,passprops.username,passprops.address' [, extraParms])}}

    It Requires CyberArk AIM Installed, and /opt/CARKaim/sdk/clipasswordsdk in place or set environment variable AIM_CLIPASSWORDSDK_CMD to the AIM
    CLI Password SDK executable.

     Parameter names AppID, Query, Output are case sensitive.

     Args:
         appid (str): Defines the unique ID of the application that is issuing the password request.
         query (str): Describes the filter criteria for the password retrieval.
         output (str): Specifies the desired output fields separated by commas. They could be: Password, PassProps.<property>, PasswordChangeInProcess
         Optionally, you can specify extra parameters recognized by clipasswordsdk (like FailRequestOnPasswordChange, Queryformat, Reason, etc.)

     Returns:
         dict: A dictionary with 'password' as key for the credential, passprops.<property>, passwordchangeinprocess
               If the specified property does not exist for this password, the value <na> will be returned for this property.
               If the value of the specified property is empty, <null> will be returned.


    for extraParms values please check parameters for clipasswordsdk in CyberArk's "Credential Provider and ASCP Implementation Guide"

    For Ansible on windows, please change the -parameters (-p, -d, and -o) to /parameters (/p, /d, and /o) and change the location of CLIPasswordSDK.exe
    """

    def run(self, terms, variables, **kwargs):

        cyberark_conn = CyberarkPassword(**kwargs)

        result = cyberark_conn.get()

        return result
