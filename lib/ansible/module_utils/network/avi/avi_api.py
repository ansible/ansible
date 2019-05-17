from __future__ import absolute_import
import os
import sys
import copy
import json
import logging
import time
from datetime import datetime, timedelta
from ssl import SSLError


class MockResponse(object):
    def __init__(self, *args, **kwargs):
        raise Exception("Requests library Response object not found. Using fake one.")


class MockRequestsConnectionError(Exception):
    pass


class MockSession(object):
    def __init__(self, *args, **kwargs):
        raise Exception("Requests library Session object not found. Using fake one.")


HAS_AVI = True
try:
    from requests import ConnectionError as RequestsConnectionError
    from requests import Response
    from requests.sessions import Session
except ImportError:
    HAS_AVI = False
    Response = MockResponse
    RequestsConnectionError = MockRequestsConnectionError
    Session = MockSession


logger = logging.getLogger(__name__)

sessionDict = {}


def avi_timedelta(td):
    '''
    This is a wrapper class to workaround python 2.6 builtin datetime.timedelta
    does not have total_seconds method
    :param timedelta object
    '''
    if type(td) != timedelta:
        raise TypeError()
    if sys.version_info >= (2, 7):
        ts = td.total_seconds()
    else:
        ts = td.seconds + (24 * 3600 * td.days)
    return ts


def avi_sdk_syslog_logger(logger_name='avi.sdk'):
    # The following sets up syslog module to log underlying avi SDK messages
    # based on the environment variables:
    #   AVI_LOG_HANDLER: names the logging handler to use. Only syslog is
    #     supported.
    #   AVI_LOG_LEVEL: Logging level used for the avi SDK. Default is DEBUG
    #   AVI_SYSLOG_ADDRESS: Destination address for the syslog handler.
    #   Default is /dev/log
    from logging.handlers import SysLogHandler
    lf = '[%(asctime)s] %(levelname)s [%(module)s.%(funcName)s:%(lineno)d] %(message)s'
    log = logging.getLogger(logger_name)
    log_level = os.environ.get('AVI_LOG_LEVEL', 'DEBUG')
    if log_level:
        log.setLevel(getattr(logging, log_level))
    formatter = logging.Formatter(lf)
    sh = SysLogHandler(address=os.environ.get('AVI_SYSLOG_ADDRESS', '/dev/log'))
    sh.setFormatter(formatter)
    log.addHandler(sh)
    return log


class ObjectNotFound(Exception):
    pass


class APIError(Exception):
    def __init__(self, arg, rsp=None):
        self.args = [arg, rsp]
        self.rsp = rsp


class AviServerError(APIError):
    def __init__(self, arg, rsp=None):
        super(AviServerError, self).__init__(arg, rsp)


class APINotImplemented(Exception):
    pass


class ApiResponse(Response):
    """
    Returns copy of the requests.Response object provides additional helper
    routines
        1. obj: returns dictionary of Avi Object
    """
    def __init__(self, rsp):
        super(ApiResponse, self).__init__()
        for k, v in list(rsp.__dict__.items()):
            setattr(self, k, v)

    def json(self):
        """
        Extends the session default json interface to handle special errors
        and raise Exceptions
        returns the Avi object as a dictionary from rsp.text
        """
        if self.status_code in (200, 201):
            if not self.text:
                # In cases like status_code == 201 the response text could be
                # empty string.
                return None
            return super(ApiResponse, self).json()
        elif self.status_code == 204:
            # No response needed; e.g., delete operation
            return None
        elif self.status_code == 404:
            raise ObjectNotFound('HTTP Error: %s Error Msg %s' % (
                self.status_code, self.text), self)
        elif self.status_code >= 500:
            raise AviServerError('HTTP Error: %s Error Msg %s' % (
                self.status_code, self.text), self)
        else:
            raise APIError('HTTP Error: %s Error Msg %s' % (
                self.status_code, self.text), self)

    def count(self):
        """
        return the number of objects in the collection response. If it is not
        a collection response then it would simply return 1.
        """
        obj = self.json()
        if 'count' in obj:
            # this was a resposne to collection
            return obj['count']
        return 1

    @staticmethod
    def to_avi_response(resp):
        if type(resp) == Response:
            return ApiResponse(resp)
        return resp


class AviCredentials(object):
    controller = ''
    username = ''
    password = ''
    api_version = '16.4.4'
    tenant = None
    tenant_uuid = None
    token = None
    port = None
    timeout = 300
    session_id = None
    csrftoken = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def update_from_ansible_module(self, m):
        """
        :param m: ansible module
        :return:
        """
        if m.params.get('avi_credentials'):
            for k, v in m.params['avi_credentials'].items():
                if hasattr(self, k):
                    setattr(self, k, v)
        if m.params['controller']:
            self.controller = m.params['controller']
        if m.params['username']:
            self.username = m.params['username']
        if m.params['password']:
            self.password = m.params['password']
        if (m.params['api_version'] and
                (m.params['api_version'] != '16.4.4')):
            self.api_version = m.params['api_version']
        if m.params['tenant']:
            self.tenant = m.params['tenant']
        if m.params['tenant_uuid']:
            self.tenant_uuid = m.params['tenant_uuid']
        if m.params.get('session_id'):
            self.session_id = m.params['session_id']
        if m.params.get('csrftoken'):
            self.csrftoken = m.params['csrftoken']

    def __str__(self):
        return 'controller %s user %s api %s tenant %s' % (
            self.controller, self.username, self.api_version, self.tenant)


class ApiSession(Session):
    """
    Extends the Request library's session object to provide helper
    utilities to work with Avi Controller like authentication, api massaging
    etc.
    """

    # This keeps track of the process which created the cache.
    # At anytime the pid of the process changes then it would create
    # a new cache for that process.
    AVI_SLUG = 'Slug'
    SESSION_CACHE_EXPIRY = 20 * 60
    SHARED_USER_HDRS = ['X-CSRFToken', 'Session-Id', 'Referer', 'Content-Type']
    MAX_API_RETRIES = 3

    def __init__(self, controller_ip=None, username=None, password=None,
                 token=None, tenant=None, tenant_uuid=None, verify=False,
                 port=None, timeout=60, api_version=None,
                 retry_conxn_errors=True, data_log=False,
                 avi_credentials=None, session_id=None, csrftoken=None,
                 lazy_authentication=False, max_api_retries=None):
        """
         ApiSession takes ownership of avi_credentials and may update the
         information inside it.

        Initialize new session object with authenticated token from login api.
        It also keeps a cache of user sessions that are cleaned up if inactive
        for more than 20 mins.

        Notes:
        01. If mode is https and port is none or 443, we don't embed the
            port in the prefix. The prefix would be 'https://ip'. If port
            is a non-default value then we concatenate https://ip:port
            in the prefix.
        02. If mode is http and the port is none or 80, we don't embed the
            port in the prefix. The prefix would be 'http://ip'. If port is
            a non-default value, then we concatenate http://ip:port in
            the prefix.
        """
        super(ApiSession, self).__init__()
        if not avi_credentials:
            tenant = tenant if tenant else "admin"
            self.avi_credentials = AviCredentials(
                controller=controller_ip, username=username, password=password,
                api_version=api_version, tenant=tenant, tenant_uuid=tenant_uuid,
                token=token, port=port, timeout=timeout,
                session_id=session_id, csrftoken=csrftoken)
        else:
            self.avi_credentials = avi_credentials
        self.headers = {}
        self.verify = verify
        self.retry_conxn_errors = retry_conxn_errors
        self.remote_api_version = {}
        self.session_cookie_name = ''
        self.user_hdrs = {}
        self.data_log = data_log
        self.num_session_retries = 0
        self.retry_wait_time = 0
        self.max_session_retries = (
            self.MAX_API_RETRIES if max_api_retries is None
            else int(max_api_retries))
        # Refer Notes 01 and 02
        k_port = port if port else 443
        if self.avi_credentials.controller.startswith('http'):
            k_port = 80 if not self.avi_credentials.port else k_port
            if self.avi_credentials.port is None or self.avi_credentials.port\
                    == 80:
                self.prefix = self.avi_credentials.controller
            else:
                self.prefix = '{x}:{y}'.format(
                    x=self.avi_credentials.controller,
                    y=self.avi_credentials.port)
        else:
            if port is None or port == 443:
                self.prefix = 'https://{x}'.format(
                    x=self.avi_credentials.controller)
            else:
                self.prefix = 'https://{x}:{y}'.format(
                    x=self.avi_credentials.controller,
                    y=self.avi_credentials.port)
        self.timeout = timeout
        self.key = '%s:%s:%s' % (self.avi_credentials.controller,
                                 self.avi_credentials.username, k_port)
        # Added api token and session id to sessionDict for handle single
        # session
        if self.avi_credentials.csrftoken:
            sessionDict[self.key] = {
                'api': self,
                "csrftoken": self.avi_credentials.csrftoken,
                "session_id": self.avi_credentials.session_id,
                "last_used": datetime.utcnow()
            }
        elif lazy_authentication:
            sessionDict.get(self.key, {}).update(
                {'api': self, "last_used": datetime.utcnow()})
        else:
            self.authenticate_session()

        self.num_session_retries = 0
        self.pid = os.getpid()
        ApiSession._clean_inactive_sessions()
        return

    @property
    def controller_ip(self):
        return self.avi_credentials.controller

    @controller_ip.setter
    def controller_ip(self, controller_ip):
        self.avi_credentials.controller = controller_ip

    @property
    def username(self):
        return self.avi_credentials.username

    @property
    def connected(self):
        return sessionDict.get(self.key, {}).get('connected', False)

    @username.setter
    def username(self, username):
        self.avi_credentials.username = username

    @property
    def password(self):
        return self.avi_credentials.password

    @password.setter
    def password(self, password):
        self.avi_credentials.password = password

    @property
    def keystone_token(self):
        return sessionDict.get(self.key, {}).get('csrftoken', None)

    @keystone_token.setter
    def keystone_token(self, token):
        sessionDict[self.key]['csrftoken'] = token

    @property
    def tenant_uuid(self):
        self.avi_credentials.tenant_uuid

    @tenant_uuid.setter
    def tenant_uuid(self, tenant_uuid):
        self.avi_credentials.tenant_uuid = tenant_uuid

    @property
    def tenant(self):
        return self.avi_credentials.tenant

    @tenant.setter
    def tenant(self, tenant):
        if tenant:
            self.avi_credentials.tenant = tenant
        else:
            self.avi_credentials.tenant = 'admin'

    @property
    def port(self):
        self.avi_credentials.port

    @port.setter
    def port(self, port):
        self.avi_credentials.port = port

    @property
    def api_version(self):
        return self.avi_credentials.api_version

    @api_version.setter
    def api_version(self, api_version):
        self.avi_credentials.api_version = api_version

    @property
    def session_id(self):
        return sessionDict[self.key]['session_id']

    def get_context(self):
        return {
            'session_id': sessionDict[self.key]['session_id'],
            'csrftoken': sessionDict[self.key]['csrftoken']
        }

    @staticmethod
    def clear_cached_sessions():
        global sessionDict
        sessionDict = {}

    @staticmethod
    def get_session(
            controller_ip=None, username=None, password=None, token=None, tenant=None,
            tenant_uuid=None, verify=False, port=None, timeout=60,
            retry_conxn_errors=True, api_version=None, data_log=False,
            avi_credentials=None, session_id=None, csrftoken=None,
            lazy_authentication=False, max_api_retries=None):
        """
        returns the session object for same user and tenant
        calls init if session dose not exist and adds it to session cache
        :param controller_ip: controller IP address
        :param username:
        :param password:
        :param token: Token to use; example, a valid keystone token
        :param tenant: Name of the tenant on Avi Controller
        :param tenant_uuid: Don't specify tenant when using tenant_id
        :param port: Rest-API may use a different port other than 443
        :param timeout: timeout for API calls; Default value is 60 seconds
        :param retry_conxn_errors: retry on connection errors
        :param api_version: Controller API version
        """
        if not avi_credentials:
            tenant = tenant if tenant else "admin"
            avi_credentials = AviCredentials(
                controller=controller_ip, username=username, password=password,
                api_version=api_version, tenant=tenant, tenant_uuid=tenant_uuid,
                token=token, port=port, timeout=timeout,
                session_id=session_id, csrftoken=csrftoken)

        k_port = avi_credentials.port if avi_credentials.port else 443
        if avi_credentials.controller.startswith('http'):
            k_port = 80 if not avi_credentials.port else k_port
        key = '%s:%s:%s' % (avi_credentials.controller,
                            avi_credentials.username, k_port)
        cached_session = sessionDict.get(key)
        if cached_session:
            user_session = cached_session['api']
            if not (user_session.avi_credentials.csrftoken or
                    lazy_authentication):
                user_session.authenticate_session()
        else:
            user_session = ApiSession(
                controller_ip, username, password, token=token, tenant=tenant,
                tenant_uuid=tenant_uuid, verify=verify, port=port,
                timeout=timeout, retry_conxn_errors=retry_conxn_errors,
                api_version=api_version, data_log=data_log,
                avi_credentials=avi_credentials,
                lazy_authentication=lazy_authentication,
                max_api_retries=max_api_retries)
            ApiSession._clean_inactive_sessions()
        return user_session

    def reset_session(self):
        """
        resets and re-authenticates the current session.
        """
        sessionDict[self.key]['connected'] = False
        logger.info('resetting session for %s', self.key)
        self.user_hdrs = {}
        for k, v in self.headers.items():
            if k not in self.SHARED_USER_HDRS:
                self.user_hdrs[k] = v
        self.headers = {}
        self.authenticate_session()

    def authenticate_session(self):
        """
        Performs session authentication with Avi controller and stores
        session cookies and sets header options like tenant.
        """
        body = {"username": self.avi_credentials.username}
        if self.avi_credentials.password:
            body["password"] = self.avi_credentials.password
        elif self.avi_credentials.token:
            body["token"] = self.avi_credentials.token
        else:
            raise APIError("Neither user password or token provided")
        logger.debug('authenticating user %s prefix %s',
                     self.avi_credentials.username, self.prefix)
        self.cookies.clear()
        err = None
        try:
            rsp = super(ApiSession, self).post(
                self.prefix + "/login", body, timeout=self.timeout, verify=self.verify)

            if rsp.status_code == 200:
                self.num_session_retries = 0
                self.remote_api_version = rsp.json().get('version', {})
                self.session_cookie_name = rsp.json().get('session_cookie_name', 'sessionid')
                self.headers.update(self.user_hdrs)
                if rsp.cookies and 'csrftoken' in rsp.cookies:
                    csrftoken = rsp.cookies['csrftoken']
                    sessionDict[self.key] = {
                        'csrftoken': csrftoken,
                        'session_id': rsp.cookies[self.session_cookie_name],
                        'last_used': datetime.utcnow(),
                        'api': self,
                        'connected': True
                    }
                logger.debug("authentication success for user %s",
                             self.avi_credentials.username)
                return
            # Check for bad request and invalid credentials response code
            elif rsp.status_code in [401, 403]:
                logger.error('Status Code %s msg %s', rsp.status_code, rsp.text)
                err = APIError('Status Code %s msg %s' % (
                    rsp.status_code, rsp.text), rsp)
                raise err
            else:
                logger.error("Error status code %s msg %s", rsp.status_code,
                             rsp.text)
                err = APIError('Status Code %s msg %s' % (
                    rsp.status_code, rsp.text), rsp)
        except (RequestsConnectionError, SSLError) as e:
            if not self.retry_conxn_errors:
                raise
            logger.warning('Connection error retrying %s', e)
            err = e
        # comes here only if there was either exception or login was not
        # successful
        if self.retry_wait_time:
            time.sleep(self.retry_wait_time)
        self.num_session_retries += 1
        if self.num_session_retries > self.max_session_retries:
            self.num_session_retries = 0
            logger.error("giving up after %d retries connection failure %s",
                         self.max_session_retries, True)
            ret_err = (
                err if err else APIError("giving up after %d retries connection failure %s" %
                                         (self.max_session_retries, True)))
            raise ret_err
        self.authenticate_session()
        return

    def _get_api_headers(self, tenant, tenant_uuid, timeout, headers,
                         api_version):
        """
        returns the headers that are passed to the requests.Session api calls.
        """
        api_hdrs = copy.deepcopy(self.headers)
        api_hdrs.update({
            "Referer": self.prefix,
            "Content-Type": "application/json"
        })
        api_hdrs['timeout'] = str(timeout)
        if self.key in sessionDict and 'csrftoken' in sessionDict.get(self.key):
            api_hdrs['X-CSRFToken'] = sessionDict.get(self.key)['csrftoken']
        else:
            self.authenticate_session()
            api_hdrs['X-CSRFToken'] = sessionDict.get(self.key)['csrftoken']
        if api_version:
            api_hdrs['X-Avi-Version'] = api_version
        elif self.avi_credentials.api_version:
            api_hdrs['X-Avi-Version'] = self.avi_credentials.api_version
        if tenant:
            tenant_uuid = None
        elif tenant_uuid:
            tenant = None
        else:
            tenant = self.avi_credentials.tenant
            tenant_uuid = self.avi_credentials.tenant_uuid
        if tenant_uuid:
            api_hdrs.update({"X-Avi-Tenant-UUID": "%s" % tenant_uuid})
            api_hdrs.pop("X-Avi-Tenant", None)
        elif tenant:
            api_hdrs.update({"X-Avi-Tenant": "%s" % tenant})
            api_hdrs.pop("X-Avi-Tenant-UUID", None)
        # Override any user headers that were passed by users. We don't know
        # when the user had updated the user_hdrs
        if self.user_hdrs:
            api_hdrs.update(self.user_hdrs)
        if headers:
            # overwrite the headers passed via the API calls.
            api_hdrs.update(headers)
        return api_hdrs

    def _api(self, api_name, path, tenant, tenant_uuid, data=None,
             headers=None, timeout=None, api_version=None, **kwargs):
        """
        It calls the requests.Session APIs and handles session expiry
        and other situations where session needs to be reset.
        returns ApiResponse object
        :param path: takes relative path to the AVI api.
        :param tenant: overrides the tenant used during session creation
        :param tenant_uuid: overrides the tenant or tenant_uuid during session
            creation
        :param timeout: timeout for API calls; Default value is 60 seconds
        :param headers: dictionary of headers that override the session
            headers.
        """
        if self.pid != os.getpid():
            logger.info('pid %d change detected new %d. Closing session',
                        self.pid, os.getpid())
            self.close()
            self.pid = os.getpid()
        if timeout is None:
            timeout = self.timeout
        fullpath = self._get_api_path(path)
        fn = getattr(super(ApiSession, self), api_name)
        api_hdrs = self._get_api_headers(tenant, tenant_uuid, timeout, headers,
                                         api_version)
        connection_error = False
        err = None
        cookies = {
            'csrftoken': api_hdrs['X-CSRFToken'],
        }
        try:
            if self.session_cookie_name:
                cookies[self.session_cookie_name] = sessionDict[self.key]['session_id']
        except KeyError:
            pass
        try:
            if (data is not None) and (type(data) == dict):
                resp = fn(fullpath, data=json.dumps(data), headers=api_hdrs,
                          timeout=timeout, cookies=cookies, **kwargs)
            else:
                resp = fn(fullpath, data=data, headers=api_hdrs,
                          timeout=timeout, cookies=cookies, **kwargs)
        except (RequestsConnectionError, SSLError) as e:
            logger.warning('Connection error retrying %s', e)
            if not self.retry_conxn_errors:
                raise
            connection_error = True
            err = e
        except Exception as e:
            logger.error('Error in Requests library %s', e)
            raise
        if not connection_error:
            logger.debug('path: %s http_method: %s hdrs: %s params: '
                         '%s data: %s rsp: %s', fullpath, api_name.upper(),
                         api_hdrs, kwargs, data,
                         (resp.text if self.data_log else 'None'))
        if connection_error or resp.status_code in (401, 419):
            if connection_error:
                try:
                    self.close()
                except Exception:
                    # ignoring exception in cleanup path
                    pass
                logger.warning('Connection failed, retrying.')
                # Adding sleep before retrying
                if self.retry_wait_time:
                    time.sleep(self.retry_wait_time)
            else:
                logger.info('received error %d %s so resetting connection',
                            resp.status_code, resp.text)
            ApiSession.reset_session(self)
            self.num_session_retries += 1
            if self.num_session_retries > self.max_session_retries:
                # Added this such that any code which re-tries can succeed
                # eventually.
                self.num_session_retries = 0
                if not connection_error:
                    err = APIError('Status Code %s msg %s' % (
                        resp.status_code, resp.text), resp)
                logger.error(
                    "giving up after %d retries conn failure %s err %s",
                    self.max_session_retries, connection_error, err)
                ret_err = (
                    err if err else APIError("giving up after %d retries connection failure %s" %
                                             (self.max_session_retries, True)))
                raise ret_err
            # should restore the updated_hdrs to one passed down
            resp = self._api(api_name, path, tenant, tenant_uuid, data,
                             headers=headers, api_version=api_version,
                             timeout=timeout, **kwargs)
            self.num_session_retries = 0

        if resp.cookies and 'csrftoken' in resp.cookies:
            csrftoken = resp.cookies['csrftoken']
            self.headers.update({"X-CSRFToken": csrftoken})
        self._update_session_last_used()
        return ApiResponse.to_avi_response(resp)

    def get_controller_details(self):
        result = {
            "controller_ip": self.controller_ip,
            "controller_api_version": self.remote_api_version
        }
        return result

    def get(self, path, tenant='', tenant_uuid='', timeout=None, params=None,
            api_version=None, **kwargs):
        """
        It extends the Session Library interface to add AVI API prefixes,
        handle session exceptions related to authentication and update
        the global user session cache.
        :param path: takes relative path to the AVI api.
        :param tenant: overrides the tenant used during session creation
        :param tenant_uuid: overrides the tenant or tenant_uuid during session
            creation
        :param timeout: timeout for API calls; Default value is 60 seconds
        :param params: dictionary of key value pairs to be sent as query
            parameters
        :param api_version: overrides x-avi-header in request header during
            session creation
        get method takes relative path to service and kwargs as per Session
            class get method
        returns session's response object
        """
        return self._api('get', path, tenant, tenant_uuid, timeout=timeout,
                         params=params, api_version=api_version, **kwargs)

    def get_object_by_name(self, path, name, tenant='', tenant_uuid='',
                           timeout=None, params=None, api_version=None,
                           **kwargs):
        """
        Helper function to access Avi REST Objects using object
        type and name. It behaves like python dictionary interface where it
        returns None when the object is not present in the AviController.
        Internally, it transforms the request to api/path?name=<name>...
        :param path: relative path to service
        :param name: name of the object
        :param tenant: overrides the tenant used during session creation
        :param tenant_uuid: overrides the tenant or tenant_uuid during session
            creation
        :param timeout: timeout for API calls; Default value is 60 seconds
        :param params: dictionary of key value pairs to be sent as query
            parameters
        :param api_version: overrides x-avi-header in request header during
            session creation
        returns dictionary object if successful else None
        """
        obj = None
        if not params:
            params = {}
        params['name'] = name
        resp = self.get(path, tenant=tenant, tenant_uuid=tenant_uuid,
                        timeout=timeout,
                        params=params, api_version=api_version, **kwargs)
        if resp.status_code in (401, 419):
            ApiSession.reset_session(self)
            resp = self.get_object_by_name(
                path, name, tenant, tenant_uuid, timeout=timeout,
                params=params, **kwargs)
        if resp.status_code > 499 or 'Invalid version' in resp.text:
            logger.error('Error in get object by name for %s named %s. '
                         'Error: %s', path, name, resp.text)
            raise AviServerError(resp.text, rsp=resp)
        elif resp.status_code > 299:
            return obj
        try:
            if 'results' in resp.json():
                obj = resp.json()['results'][0]
            else:
                # For apis returning single object eg. api/cluster
                obj = resp.json()
        except IndexError:
            logger.warning('Warning: Object Not found for %s named %s',
                           path, name)
            obj = None
        self._update_session_last_used()
        return obj

    def post(self, path, data=None, tenant='', tenant_uuid='', timeout=None,
             force_uuid=None, params=None, api_version=None, **kwargs):
        """
        It extends the Session Library interface to add AVI API prefixes,
        handle session exceptions related to authentication and update
        the global user session cache.
        :param path: takes relative path to the AVI api.It is modified by
        the library to conform to AVI Controller's REST API interface
        :param data: dictionary of the data. Support for json string
            is deprecated
        :param tenant: overrides the tenant used during session creation
        :param tenant_uuid: overrides the tenant or tenant_uuid during session
            creation
        :param timeout: timeout for API calls; Default value is 60 seconds
        :param params: dictionary of key value pairs to be sent as query
            parameters
        :param api_version: overrides x-avi-header in request header during
            session creation
        returns session's response object
        """
        if force_uuid is not None:
            headers = kwargs.get('headers', {})
            headers[self.AVI_SLUG] = force_uuid
            kwargs['headers'] = headers
        return self._api('post', path, tenant, tenant_uuid, data=data,
                         timeout=timeout, params=params,
                         api_version=api_version, **kwargs)

    def put(self, path, data=None, tenant='', tenant_uuid='',
            timeout=None, params=None, api_version=None, **kwargs):
        """
        It extends the Session Library interface to add AVI API prefixes,
        handle session exceptions related to authentication and update
        the global user session cache.
        :param path: takes relative path to the AVI api.It is modified by
            the library to conform to AVI Controller's REST API interface
        :param data: dictionary of the data. Support for json string
            is deprecated
        :param tenant: overrides the tenant used during session creation
        :param tenant_uuid: overrides the tenant or tenant_uuid during session
            creation
        :param timeout: timeout for API calls; Default value is 60 seconds
        :param params: dictionary of key value pairs to be sent as query
            parameters
        :param api_version: overrides x-avi-header in request header during
            session creation
        returns session's response object
        """
        return self._api('put', path, tenant, tenant_uuid, data=data,
                         timeout=timeout, params=params,
                         api_version=api_version, **kwargs)

    def patch(self, path, data=None, tenant='', tenant_uuid='',
              timeout=None, params=None, api_version=None, **kwargs):
        """
        It extends the Session Library interface to add AVI API prefixes,
        handle session exceptions related to authentication and update
        the global user session cache.
        :param path: takes relative path to the AVI api.It is modified by
            the library to conform to AVI Controller's REST API interface
        :param data: dictionary of the data. Support for json string
            is deprecated
        :param tenant: overrides the tenant used during session creation
        :param tenant_uuid: overrides the tenant or tenant_uuid during session
            creation
        :param timeout: timeout for API calls; Default value is 60 seconds
        :param params: dictionary of key value pairs to be sent as query
            parameters
        :param api_version: overrides x-avi-header in request header during
            session creation
        returns session's response object
        """
        return self._api('patch', path, tenant, tenant_uuid, data=data,
                         timeout=timeout, params=params,
                         api_version=api_version, **kwargs)

    def put_by_name(self, path, name, data=None, tenant='',
                    tenant_uuid='', timeout=None, params=None,
                    api_version=None, **kwargs):
        """
        Helper function to perform HTTP PUT on Avi REST Objects using object
        type and name.
        Internally, it transforms the request to api/path?name=<name>...
        :param path: relative path to service
        :param name: name of the object
        :param data: dictionary of the data. Support for json string
            is deprecated
        :param tenant: overrides the tenant used during session creation
        :param tenant_uuid: overrides the tenant or tenant_uuid during session
            creation
        :param timeout: timeout for API calls; Default value is 60 seconds
        :param params: dictionary of key value pairs to be sent as query
            parameters
        :param api_version: overrides x-avi-header in request header during
            session creation
        returns session's response object
        """
        uuid = self._get_uuid_by_name(
            path, name, tenant, tenant_uuid, api_version=api_version)
        path = '%s/%s' % (path, uuid)
        return self.put(path, data, tenant, tenant_uuid, timeout=timeout,
                        params=params, api_version=api_version, **kwargs)

    def delete(self, path, tenant='', tenant_uuid='', timeout=None, params=None,
               data=None, api_version=None, **kwargs):
        """
        It extends the Session Library interface to add AVI API prefixes,
        handle session exceptions related to authentication and update
        the global user session cache.
        :param path: takes relative path to the AVI api.It is modified by
        the library to conform to AVI Controller's REST API interface
        :param tenant: overrides the tenant used during session creation
        :param tenant_uuid: overrides the tenant or tenant_uuid during session
            creation
        :param timeout: timeout for API calls; Default value is 60 seconds
        :param params: dictionary of key value pairs to be sent as query
            parameters
        :param data: dictionary of the data. Support for json string
            is deprecated
        :param api_version: overrides x-avi-header in request header during
            session creation
        returns session's response object
        """
        return self._api('delete', path, tenant, tenant_uuid, data=data,
                         timeout=timeout, params=params,
                         api_version=api_version, **kwargs)

    def delete_by_name(self, path, name, tenant='', tenant_uuid='',
                       timeout=None, params=None, api_version=None, **kwargs):
        """
        Helper function to perform HTTP DELETE on Avi REST Objects using object
        type and name.Internally, it transforms the request to
        api/path?name=<name>...
        :param path: relative path to service
        :param name: name of the object
        :param tenant: overrides the tenant used during session creation
        :param tenant_uuid: overrides the tenant or tenant_uuid during session
            creation
        :param timeout: timeout for API calls; Default value is 60 seconds
        :param params: dictionary of key value pairs to be sent as query
            parameters
        :param api_version: overrides x-avi-header in request header during
            session creation
        returns session's response object
        """
        uuid = self._get_uuid_by_name(path, name, tenant, tenant_uuid,
                                      api_version=api_version)
        if not uuid:
            raise ObjectNotFound("%s/?name=%s" % (path, name))
        path = '%s/%s' % (path, uuid)
        return self.delete(path, tenant, tenant_uuid, timeout=timeout,
                           params=params, api_version=api_version, **kwargs)

    def get_obj_ref(self, obj):
        """returns reference url from dict object"""
        if not obj:
            return None
        if isinstance(obj, Response):
            obj = json.loads(obj.text)
        if obj.get(0, None):
            return obj[0]['url']
        elif obj.get('url', None):
            return obj['url']
        elif obj.get('results', None):
            return obj['results'][0]['url']
        else:
            return None

    def get_obj_uuid(self, obj):
        """returns uuid from dict object"""
        if not obj:
            raise ObjectNotFound('Object %s Not found' % (obj))
        if isinstance(obj, Response):
            obj = json.loads(obj.text)
        if obj.get(0, None):
            return obj[0]['uuid']
        elif obj.get('uuid', None):
            return obj['uuid']
        elif obj.get('results', None):
            return obj['results'][0]['uuid']
        else:
            return None

    def _get_api_path(self, path, uuid=None):
        """
        This function returns the full url from relative path and uuid.
        """
        if path == 'logout':
            return self.prefix + '/' + path
        elif uuid:
            return self.prefix + '/api/' + path + '/' + uuid
        else:
            return self.prefix + '/api/' + path

    def _get_uuid_by_name(self, path, name, tenant='admin',
                          tenant_uuid='', api_version=None):
        """gets object by name and service path and returns uuid"""
        resp = self.get_object_by_name(
            path, name, tenant, tenant_uuid, api_version=api_version)
        if not resp:
            raise ObjectNotFound("%s/%s" % (path, name))
        return self.get_obj_uuid(resp)

    def _update_session_last_used(self):
        if self.key in sessionDict:
            sessionDict[self.key]["last_used"] = datetime.utcnow()

    @staticmethod
    def _clean_inactive_sessions():
        """Removes sessions which are inactive more than 20 min"""
        session_cache = sessionDict
        logger.debug("cleaning inactive sessions in pid %d num elem %d",
                     os.getpid(), len(session_cache))
        keys_to_delete = []
        for key, session in list(session_cache.items()):
            tdiff = avi_timedelta(datetime.utcnow() - session["last_used"])
            if tdiff < ApiSession.SESSION_CACHE_EXPIRY:
                continue
            keys_to_delete.append(key)
        for key in keys_to_delete:
            del session_cache[key]
            logger.debug("Removed session for : %s", key)

    def delete_session(self):
        """ Removes the session for cleanup"""
        logger.debug("Removed session for : %s", self.key)
        sessionDict.pop(self.key, None)
        return
# End of file
