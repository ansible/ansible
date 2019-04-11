# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2017 Fortinet, Inc
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

from ansible.module_utils.network.fortimanager.common import FMGR_RC
from ansible.module_utils.network.fortimanager.common import FMGBaseException
from ansible.module_utils.network.fortimanager.common import FMGRCommon
from ansible.module_utils.network.fortimanager.common import scrub_dict

# check for pyFMG lib - DEPRECATING
try:
    from pyFMG.fortimgr import FortiManager
    HAS_PYFMGR = True
except ImportError:
    HAS_PYFMGR = False

# ACTIVE BUG WITH OUR DEBUG IMPORT CALL -- BECAUSE IT'S UNDER MODULE_UTILITIES
# WHEN module_common.recursive_finder() runs under the module loader, it looks for this namespace debug import
# and because it's not there, it always fails, regardless of it being under a try/catch here.
# we're going to move it to a different namespace.
# # check for debug lib
# try:
#     from ansible.module_utils.network.fortimanager.fortimanager_debug import debug_dump
#     HAS_FMGR_DEBUG = True
# except:
#     HAS_FMGR_DEBUG = False


# BEGIN HANDLER CLASSES
class FortiManagerHandler(object):
    def __init__(self, conn, module):
        self._conn = conn
        self._module = module
        self._tools = FMGRCommon

    def process_request(self, url, datagram, method):
        """
        Formats and Runs the API Request via Connection Plugin. Streamlined for use FROM Modules.

        :param url: Connection URL to access
        :type url: string
        :param datagram: The prepared payload for the API Request in dictionary format
        :type datagram: dict
        :param method: The preferred API Request method (GET, ADD, POST, etc....)
        :type method: basestring

        :return: Dictionary containing results of the API Request via Connection Plugin
        :rtype: dict
        """
        data = self._tools.format_request(method, url, **datagram)
        response = self._conn.send_request(method, data)

        # if HAS_FMGR_DEBUG:
        #     try:
        #         debug_dump(response, datagram, self._module.paramgram, url, method)
        #     except BaseException:
        #         pass

        return response

    def govern_response(self, module, results, msg=None, good_codes=None,
                        stop_on_fail=None, stop_on_success=None, skipped=None,
                        changed=None, unreachable=None, failed=None, success=None, changed_if_success=None,
                        ansible_facts=None):
        """
        This function will attempt to apply default values to canned responses from FortiManager we know of.
        This saves time, and turns the response in the module into a "one-liner", while still giving us...
        the flexibility to directly use return_response in modules if we have too. This function saves repeated code.

        :param module: The Ansible Module CLASS object, used to run fail/exit json
        :type module: object
        :param msg: An overridable custom message from the module that called this.
        :type msg: string
        :param results: A dictionary object containing an API call results
        :type results: dict
        :param good_codes: A list of exit codes considered successful from FortiManager
        :type good_codes: list
        :param stop_on_fail: If true, stops playbook run when return code is NOT IN good codes (default: true)
        :type stop_on_fail: boolean
        :param stop_on_success: If true, stops playbook run when return code is IN good codes (default: false)
        :type stop_on_success: boolean
        :param changed: If True, tells Ansible that object was changed (default: false)
        :type skipped: boolean
        :param skipped: If True, tells Ansible that object was skipped (default: false)
        :type skipped: boolean
        :param unreachable: If True, tells Ansible that object was unreachable (default: false)
        :type unreachable: boolean
        :param failed: If True, tells Ansible that execution was a failure. Overrides good_codes. (default: false)
        :type unreachable: boolean
        :param success: If True, tells Ansible that execution was a success. Overrides good_codes. (default: false)
        :type unreachable: boolean
        :param changed_if_success: If True, defaults to changed if successful if you specify or not"
        :type changed_if_success: boolean
        :param ansible_facts: A prepared dictionary of ansible facts from the execution.
        :type ansible_facts: dict
        """
        if module is None and results is None:
            raise FMGBaseException("govern_response() was called without a module and/or results tuple! Fix!")
        # Get the Return code from results
        try:
            rc = results[0]
        except BaseException:
            raise FMGBaseException("govern_response() was called without the return code at results[0]")

        # init a few items
        rc_data = None

        # Get the default values for the said return code.
        try:
            rc_codes = FMGR_RC.get('fmgr_return_codes')
            rc_data = rc_codes.get(rc)
        except BaseException:
            pass

        if not rc_data:
            rc_data = {}
        # ONLY add to overrides if not none -- This is very important that the keys aren't added at this stage
        # if they are empty. And there aren't that many, so let's just do a few if then statements.
        if good_codes is not None:
            rc_data["good_codes"] = good_codes
        if stop_on_fail is not None:
            rc_data["stop_on_fail"] = stop_on_fail
        if stop_on_success is not None:
            rc_data["stop_on_success"] = stop_on_success
        if skipped is not None:
            rc_data["skipped"] = skipped
        if changed is not None:
            rc_data["changed"] = changed
        if unreachable is not None:
            rc_data["unreachable"] = unreachable
        if failed is not None:
            rc_data["failed"] = failed
        if success is not None:
            rc_data["success"] = success
        if changed_if_success is not None:
            rc_data["changed_if_success"] = changed_if_success
        if results is not None:
            rc_data["results"] = results
        if msg is not None:
            rc_data["msg"] = msg
        if ansible_facts is None:
            rc_data["ansible_facts"] = {}
        else:
            rc_data["ansible_facts"] = ansible_facts

        return self.return_response(module=module,
                                    results=results,
                                    msg=rc_data.get("msg", "NULL"),
                                    good_codes=rc_data.get("good_codes", (0,)),
                                    stop_on_fail=rc_data.get("stop_on_fail", True),
                                    stop_on_success=rc_data.get("stop_on_success", False),
                                    skipped=rc_data.get("skipped", False),
                                    changed=rc_data.get("changed", False),
                                    changed_if_success=rc_data.get("changed_if_success", False),
                                    unreachable=rc_data.get("unreachable", False),
                                    failed=rc_data.get("failed", False),
                                    success=rc_data.get("success", False),
                                    ansible_facts=rc_data.get("ansible_facts", dict()))

    @staticmethod
    def return_response(module, results, msg="NULL", good_codes=(0,),
                        stop_on_fail=True, stop_on_success=False, skipped=False,
                        changed=False, unreachable=False, failed=False, success=False, changed_if_success=True,
                        ansible_facts=()):
        """
        This function controls the logout and error reporting after an method or function runs. The exit_json for
        ansible comes from logic within this function. If this function returns just the msg, it means to continue
        execution on the playbook. It is called from the ansible module, or from the self.govern_response function.

        :param module: The Ansible Module CLASS object, used to run fail/exit json
        :type module: object
        :param msg: An overridable custom message from the module that called this.
        :type msg: string
        :param results: A dictionary object containing an API call results
        :type results: dict
        :param good_codes: A list of exit codes considered successful from FortiManager
        :type good_codes: list
        :param stop_on_fail: If true, stops playbook run when return code is NOT IN good codes (default: true)
        :type stop_on_fail: boolean
        :param stop_on_success: If true, stops playbook run when return code is IN good codes (default: false)
        :type stop_on_success: boolean
        :param changed: If True, tells Ansible that object was changed (default: false)
        :type skipped: boolean
        :param skipped: If True, tells Ansible that object was skipped (default: false)
        :type skipped: boolean
        :param unreachable: If True, tells Ansible that object was unreachable (default: false)
        :type unreachable: boolean
        :param failed: If True, tells Ansible that execution was a failure. Overrides good_codes. (default: false)
        :type unreachable: boolean
        :param success: If True, tells Ansible that execution was a success. Overrides good_codes. (default: false)
        :type unreachable: boolean
        :param changed_if_success: If True, defaults to changed if successful if you specify or not"
        :type changed_if_success: boolean
        :param ansible_facts: A prepared dictionary of ansible facts from the execution.
        :type ansible_facts: dict

        :return: A string object that contains an error message
        :rtype: str
        """

        # VALIDATION ERROR
        if (len(results) == 0) or (failed and success) or (changed and unreachable):
            module.exit_json(msg="Handle_response was called with no results, or conflicting failed/success or "
                                 "changed/unreachable parameters. Fix the exit code on module. "
                                 "Generic Failure", failed=True)

        # IDENTIFY SUCCESS/FAIL IF NOT DEFINED
        if not failed and not success:
            if len(results) > 0:
                if results[0] not in good_codes:
                    failed = True
                elif results[0] in good_codes:
                    success = True

        if len(results) > 0:
            # IF NO MESSAGE WAS SUPPLIED, GET IT FROM THE RESULTS, IF THAT DOESN'T WORK, THEN WRITE AN ERROR MESSAGE
            if msg == "NULL":
                try:
                    msg = results[1]['status']['message']
                except BaseException:
                    msg = "No status message returned at results[1][status][message], " \
                          "and none supplied to msg parameter for handle_response."

            if failed:
                # BECAUSE SKIPPED/FAILED WILL OFTEN OCCUR ON CODES THAT DON'T GET INCLUDED, THEY ARE CONSIDERED FAILURES
                # HOWEVER, THEY ARE MUTUALLY EXCLUSIVE, SO IF IT IS MARKED SKIPPED OR UNREACHABLE BY THE MODULE LOGIC
                # THEN REMOVE THE FAILED FLAG SO IT DOESN'T OVERRIDE THE DESIRED STATUS OF SKIPPED OR UNREACHABLE.
                if failed and skipped:
                    failed = False
                if failed and unreachable:
                    failed = False
                if stop_on_fail:
                    module.exit_json(msg=msg, failed=failed, changed=changed, unreachable=unreachable, skipped=skipped,
                                     results=results[1], ansible_facts=ansible_facts, rc=results[0],
                                     invocation={"module_args": ansible_facts["ansible_params"]})
            elif success:
                if changed_if_success:
                    changed = True
                    success = False
                if stop_on_success:
                    module.exit_json(msg=msg, success=success, changed=changed, unreachable=unreachable,
                                     skipped=skipped, results=results[1], ansible_facts=ansible_facts, rc=results[0],
                                     invocation={"module_args": ansible_facts["ansible_params"]})
        return msg

    def construct_ansible_facts(self, response, ansible_params, paramgram, *args, **kwargs):
        """
        Constructs a dictionary to return to ansible facts, containing various information about the execution.

        :param response: Contains the response from the FortiManager.
        :type response: dict
        :param ansible_params: Contains the parameters Ansible was called with.
        :type ansible_params: dict
        :param paramgram: Contains the paramgram passed to the modules' local modify function.
        :type paramgram: dict
        :param args: Free-form arguments that could be added.
        :param kwargs: Free-form keyword arguments that could be added.

        :return: A dictionary containing lots of information to append to Ansible Facts.
        :rtype: dict
        """

        facts = {
            "response": response,
            "ansible_params": scrub_dict(ansible_params),
            "paramgram": scrub_dict(paramgram),
            "connected_fmgr": self._conn.return_connected_fmgr()
        }

        if args:
            facts["custom_args"] = args
        if kwargs:
            facts.update(kwargs)

        return facts


##########################
# BEGIN DEPRECATED METHODS
##########################

# SOME OF THIS CODE IS DUPLICATED IN THE PLUGIN, BUT THOSE ARE PLUGIN SPECIFIC. THIS VERSION STILL ALLOWS FOR
# THE USAGE OF PYFMG FOR CUSTOMERS WHO HAVE NOT YET UPGRADED TO ANSIBLE 2.7

# LEGACY PYFMG METHODS START
# USED TO DETERMINE LOCK CONTEXT ON A FORTIMANAGER. A DATABASE LOCKING CONCEPT THAT NEEDS TO BE ACCOUNTED FOR.

class FMGLockContext(object):
    """
    - DEPRECATING: USING CONNECTION MANAGER NOW INSTEAD. EVENTUALLY THIS CLASS WILL DISAPPEAR. PLEASE
    - CONVERT ALL MODULES TO CONNECTION MANAGER METHOD.
    - LEGACY pyFMG HANDLER OBJECT: REQUIRES A CHECK FOR PY FMG AT TOP OF PAGE
    """
    def __init__(self, fmg):
        self._fmg = fmg
        self._locked_adom_list = list()
        self._uses_workspace = False
        self._uses_adoms = False

    @property
    def uses_workspace(self):
        return self._uses_workspace

    @uses_workspace.setter
    def uses_workspace(self, val):
        self._uses_workspace = val

    @property
    def uses_adoms(self):
        return self._uses_adoms

    @uses_adoms.setter
    def uses_adoms(self, val):
        self._uses_adoms = val

    def add_adom_to_lock_list(self, adom):
        if adom not in self._locked_adom_list:
            self._locked_adom_list.append(adom)

    def remove_adom_from_lock_list(self, adom):
        if adom in self._locked_adom_list:
            self._locked_adom_list.remove(adom)

    def check_mode(self):
        url = "/cli/global/system/global"
        code, resp_obj = self._fmg.get(url, fields=["workspace-mode", "adom-status"])
        try:
            if resp_obj["workspace-mode"] != 0:
                self.uses_workspace = True
        except KeyError:
            self.uses_workspace = False
        try:
            if resp_obj["adom-status"] == 1:
                self.uses_adoms = True
        except KeyError:
            self.uses_adoms = False

    def run_unlock(self):
        for adom_locked in self._locked_adom_list:
            self.unlock_adom(adom_locked)

    def lock_adom(self, adom=None, *args, **kwargs):
        if adom:
            if adom.lower() == "global":
                url = "/dvmdb/global/workspace/lock/"
            else:
                url = "/dvmdb/adom/{adom}/workspace/lock/".format(adom=adom)
        else:
            url = "/dvmdb/adom/root/workspace/lock"
        code, respobj = self._fmg.execute(url, {}, *args, **kwargs)
        if code == 0 and respobj["status"]["message"].lower() == "ok":
            self.add_adom_to_lock_list(adom)
        return code, respobj

    def unlock_adom(self, adom=None, *args, **kwargs):
        if adom:
            if adom.lower() == "global":
                url = "/dvmdb/global/workspace/unlock/"
            else:
                url = "/dvmdb/adom/{adom}/workspace/unlock/".format(adom=adom)
        else:
            url = "/dvmdb/adom/root/workspace/unlock"
        code, respobj = self._fmg.execute(url, {}, *args, **kwargs)
        if code == 0 and respobj["status"]["message"].lower() == "ok":
            self.remove_adom_from_lock_list(adom)
        return code, respobj

    def commit_changes(self, adom=None, aux=False, *args, **kwargs):
        if adom:
            if aux:
                url = "/pm/config/adom/{adom}/workspace/commit".format(adom=adom)
            else:
                if adom.lower() == "global":
                    url = "/dvmdb/global/workspace/commit/"
                else:
                    url = "/dvmdb/adom/{adom}/workspace/commit".format(adom=adom)
        else:
            url = "/dvmdb/adom/root/workspace/commit"
        return self._fmg.execute(url, {}, *args, **kwargs)


# DEPRECATED -- USE PLUGIN INSTEAD
class AnsibleFortiManager(object):
    """
    - DEPRECATING: USING CONNECTION MANAGER NOW INSTEAD. EVENTUALLY THIS CLASS WILL DISAPPEAR. PLEASE
    - CONVERT ALL MODULES TO CONNECTION MANAGER METHOD.
    - LEGACY pyFMG HANDLER OBJECT: REQUIRES A CHECK FOR PY FMG AT TOP OF PAGE
    """

    def __init__(self, module, ip=None, username=None, passwd=None, use_ssl=True, verify_ssl=False, timeout=300):
        self.ip = ip
        self.username = username
        self.passwd = passwd
        self.use_ssl = use_ssl
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.fmgr_instance = None

        if not HAS_PYFMGR:
            module.fail_json(msg='Could not import the python library pyFMG required by this module')

        self.module = module

    def login(self):
        if self.ip is not None:
            self.fmgr_instance = FortiManager(self.ip, self.username, self.passwd, use_ssl=self.use_ssl,
                                              verify_ssl=self.verify_ssl, timeout=self.timeout, debug=False,
                                              disable_request_warnings=True)
            return self.fmgr_instance.login()

    def logout(self):
        if self.fmgr_instance.sid is not None:
            self.fmgr_instance.logout()

    def get(self, url, data):
        return self.fmgr_instance.get(url, **data)

    def set(self, url, data):
        return self.fmgr_instance.set(url, **data)

    def update(self, url, data):
        return self.fmgr_instance.update(url, **data)

    def delete(self, url, data):
        return self.fmgr_instance.delete(url, **data)

    def add(self, url, data):
        return self.fmgr_instance.add(url, **data)

    def execute(self, url, data):
        return self.fmgr_instance.execute(url, **data)

    def move(self, url, data):
        return self.fmgr_instance.move(url, **data)

    def clone(self, url, data):
        return self.fmgr_instance.clone(url, **data)

##########################
# END DEPRECATED METHODS
##########################
