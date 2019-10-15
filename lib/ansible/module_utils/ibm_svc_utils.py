# Copyright (C) 2019 IBM CORPORATION
# Author(s): John Hetherington <john.hetherington@uk.ibm.com>
#
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

''' Support class for IBM SVC ansible modules '''

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import logging

from ansible.module_utils.basic import jsonify
from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.parse import quote
from ansible.module_utils.six.moves.urllib.error import HTTPError


def svc_argument_spec():
    """
    Returns argument_spec of options common to ibm_svc_*-modules

    :returns: argument_spec
    :rtype: dict
    """
    return dict(
        clustername=dict(type='str', required=True),
        domain=dict(type='str', default=None),
        validate_certs=dict(type='bool', default=False),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        log_path=dict(type='str')
    )


class IBMSVCRestApi(object):
    """ Communicate with SVC via RestApi
    SVC commands usually have the format
    $ command -opt1 value1 -opt2 value2 arg1 arg2 arg3
    to use the RestApi we transform this into
    https://host:7443/rest/command/arg1/arg2/arg3 data={'opt1':'value1', 'opt2':'value2'}
    """
    def __init__(self, module, clustername, domain, username, password, validate_certs, log_path):
        """ Initialize module with what we need for initial connection
        :param clustername: name of the SVC cluster
        :type clustername: string
        :param domain: domain name to make a fully qualified host name
        :type domain: string
        :param username: SVC username 
        :type username: string
        :param password: Password for user
        :type password: string
        :param validate_certs: whether or not the connection is insecure
        :type validate_certs: bool
        """
        self.module = module
        self.clustername = clustername
        self.domain = domain
        self.username = username
        self.password = password
        self.validate_certs = validate_certs

        # logging setup
        self._logger = logging.getLogger(self.__class__.__name__)
        self.debug = self._logger.debug
        if log_path:
            logging.basicConfig(level=logging.DEBUG, filename=log_path)

        # Make sure we can connect via the RestApi
        self.token = self._svc_authorize()
        self.debug("_connect token={}".format(self.token))
        if not self.token:
            self.module.fail_json(msg='Failed to obtain access token')


    @property
    def port(self):
        return getattr(self, '_port', None) or '7443'


    @property
    def protocol(self):
        return getattr(self, '_protocol', None) or 'https'


    @property
    def resturl(self):
        if self.domain:
            hostname = '{}.{}'.format(self.clustername,self.domain)
        else:
            hostname = self.clustername
        return getattr(self, '_resturl', None) or "{protocol}://{host}:{port}/rest".format(protocol=self.protocol, host=hostname, port=self.port)


    @property
    def token(self):
        return getattr(self, '_token', None) or None

    @token.setter
    def token(self, value):
        return setattr(self, '_token', value)


    def _svc_rest(self, method, headers, cmd, cmdopts, cmdargs):
        """ Run SVC command with token info added into header
        :param method: http method, POST or GET
        :type method: string
        :param headers: http headers
        :type headers: dict
        :param cmd: svc command to run
        :type cmd: string
        :param cmdopts: svc command options, name paramter and value
        :type cmdopts: dict
        :param cmdargs: svc command arguments, non-named paramaters
        :return: dict of command results 
        :rtype: dict
        """

        # Catch any output or errors and pass back to the caller to deal with.
        r = {
            'url'   : None,
            'code'  : None,
            'err'   : None,
            'out'   : None,
            'data'  : None
        }

        postfix = cmd
        if cmdargs:
            postfix = '/'.join([postfix] + [quote(str(a)) for a in cmdargs])
        url = '/'.join([self.resturl] + [postfix])
        r['url']  = url # Pass back in result for error handling 
        self.debug("_svc_rest: url={}".format(url))

        payload = cmdopts if cmdopts else None
        data=jsonify(payload, encoding="utf-8")
        r['data'] = cmdopts # Original payload data has nicer formatting
        self.debug("_svc_rest: payload={}".format(payload))

        try:
            o = open_url(url, method=method, headers=headers, validate_certs=self.validate_certs, data=bytes(data))
        except HTTPError as e:
            self.debug('_svc_rest: httperror {}'.format(str(e)))
            r['code'] = e.getcode()
            r['out'] = e.read()
            r['err'] = "HTTPError {}".format(str(e))
            return r 
        except Exception as e:
            self.debug('_svc_rest: exception : {}'.format(str(e)))
            r['err'] = "Exception {}".format(str(e))
            return r 

        try:
            j = json.load(o)
        except ValueError:
            self.debug("_svc_rest: value error pass: {}".format(str(e)))
            # pass, will mean both data and error are None.
            return r

        r['out'] = j
        return r


    def _svc_authorize(self):
        """ Obtain a token if we are authoized to connect
        :return: None or token string
        """

        headers={
            'Content-Type':   'application/json',
            'X-Auth-Username': self.username,
            'X-Auth-Password': self.password
        }

        rest = self._svc_rest(method='POST', headers=headers, cmd='auth', cmdopts=None, cmdargs=None)
        assert rest is not None
        assert 'err' in rest
        assert 'out' in rest

        if rest['err']:
            return None

        out = rest['out']
        if out:
            if 'token' in out:
                return out['token']

        return None


    def _svc_token_wrap(self, cmd, cmdopts, cmdargs):
        """ Run SVC command with token info added into header
        :param cmd: svc command to run
        :type cmd: string
        :param cmdopts: svc command options, name paramter and value
        :type cmdopts: dict
        :param cmdargs: svc command arguments, non-named paramaters
        :type cmdargs: list
        :returns: command results 
        """

        if self.token is None:
            self.module.fail_json(msg="No authorize token")
            # Abort

        headers={
            'Content-Type': 'application/json',
            'X-Auth-Token': self.token
        }

        return self._svc_rest(method='POST', headers=headers, cmd=cmd, cmdopts=cmdopts, cmdargs=cmdargs)


    def svc_run_command(self, cmd, cmdopts, cmdargs):
        """ Generic execute a SVC command
        :param cmd: svc command to run
        :type cmd: string
        :param cmdopts: svc command options, name parameter and value
        :type cmdopts: dict
        :param cmdargs: svc command arguments, non-named parameters
        :type cmdargs: list
        :returns: command output
        """

        rest = self._svc_token_wrap(cmd, cmdopts, cmdargs)
        self.debug("svc_run_command rest={}".format(rest))

        if rest['err']:
            msg=rest
            self.module.fail_json(msg=msg)
            # Aborts

        # Might be None
        return rest['out']


    def svc_obj_info(self, cmd, cmdopts, cmdargs):
        """ Obtain information about an SVC object via the ls command
        :param cmd: svc command to run
        :type cmd: string
        :param cmdopts: svc command options, name parameter and value
        :type cmdopts: dict
        :param cmdargs: svc command arguments, non-named paramaters
        :type cmdargs: list
        :returns: command output
        :rtype: dict
        """

        rest = self._svc_token_wrap(cmd, cmdopts, cmdargs)
        self.debug("svc_obj_info rest={}".format(rest))
       
        if rest['code']:
            if rest['code'] == 500:
                # Object did not exist, which is quite valid.
                return None

        # Fail for anything else  
        if rest['err']:
            self.module.fail_json(msg=rest)
            # Aborts

        # Might be None
        return rest['out']

