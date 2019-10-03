# -*- coding: utf-8 -*-
#

"""
Python3 library to ease interaction with the Uptime Robot API.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import requests
import configparser
import os
import copy
import pathlib


class UptimeRobot(object):
    """Library to easily interact with the Uptime Robot API
    This library implements the methods available in the Uptime Robot
    documentation here: https://uptimerobot.com/api.
    """

    def __init__(self, endpoint='https://api.uptimerobot.com/v2/',
                 req_obj=None, api_key=None):
        """
        Init method
        Parameters
        -----------
        endpoint : str
            (Default value = 'https://api.uptimerobot.com/v2/')
            The Uptime Robot api endpoint.
        req_obj : requests.sessions.Session
            A requests session object for making requests to Uptime Robot API.
        api_key : str
            Api key to Uptime Robot API for authentication.
        """
        self.endpoint = endpoint
        self._api_key = api_key
        self._req_obj = req_obj
        self.payload = {'api_key': self.api_key}

    @property
    def request_session(self):
        """Gets our request object or defaults req_obj to requests.Session()
        This ensures that a user has a requests object to work with in order.
        If the user doesn't specify a request object, we provide one. Otherwise
        We allow the choice.
        Returns
        -------
        requests.sessions.Session
            This returns a requests sesssion object.
        """
        if not self._req_obj:
            self._req_obj = requests.Session()
        return self._req_obj

    @property
    def api_key(self):
        """Config alternative to specifying API key during instantiation
        This property provides the opportunity for a user to use a config file
        to store and retreive their API key instead of providing it upon
        instantiation.
        Returns
        -------
        str
            This returns a string representation of the API key.
        """
        if not self._api_key:
            config = configparser.ConfigParser()
            home_dir = pathlib.Path.home()
            config_file = os.path.join(home_dir, '.uptimerobot.ini')
            if pathlib.Path(config_file).is_file():
                config.read(config_file)
            else:
                key = input("Enter UptimeRobot API key: ")
                config['UPTIMEROBOT'] = {'API_KEY': key}
                with open(config_file, 'w') as configfile:
                    config.write(configfile)
            self._api_key = config['UPTIMEROBOT']['API_KEY']
        return self._api_key

    def _check_response(self, response):
        """Check our responses for a good response code.
        Parameters
        ----------
        response : str
            API call response
        Raises
        -------
        requests.HTTPError
            Raises this error if we get a response status code that is not in
            the 200 range.
        """
        if response.status_code // 100 == 2:
            return True
        else:
            raise requests.HTTPError('{0} ==> {1}'.format(response.status_code, response.text))

    def _make_request(self, method="POST", route="/", **kwargs):
        """Utilize our session object to make requests.
        Parameters
        ----------
        method : str
            (Default value = "POST")
            Our http verb. Defaults to POST, but can be passed any http verb.
        route : str
            (Default value = "/")
            The API route. Defaults to /, but is expected to be overwritten
        **kwargs : dict
            Arbitrary keyword arguments.
        Returns
        -------
        str
            Returns the json string from the invoked API method.
        """
        route = requests.compat.urljoin(self.endpoint, route)
        response = self.request_session.request(method, route, **kwargs)
        return response

    def _handle_routes(self, route, **kwargs):
        """Generic function for handling the passing of routes to _make_request.
        Parameters
        ----------
        route : str
            The API route to target for our API call.
        **kwargs : dict
            Arbitrary keyword arguments.
        Returns
        -------
        str
            Returns the json string from the invoked API method.
        """
        payload = {**kwargs, **self.payload}
        response = self._make_request('POST', route, json=payload)
        if self._check_response(response):
            return response.json()

    def _handle_payload(self, local_vars):
        """Handles the creation of post payloads.
        Parameters
        ----------
        local_vars : dict
            Dict of variables local to the calling method. Generated utilizing
            locals() in the calling method.
        Returns
        -------
        dict
            Returns a dict of parameters to be passed with the API call.
        """
        if 'kwargs' in local_vars:
            kwargs = local_vars['kwargs']
            del local_vars['kwargs']
            del local_vars['route']
            del local_vars['self']
            return {**local_vars, **kwargs}
        else:
            del local_vars['route']
            del local_vars['self']
            return {**local_vars}

    def _paginator(self, response, **kwargs):
        """Page through get_monitors output until all checks are returned.
        Parameters
        ----------
        response : str
            Json string response from method call.
        **kwargs : dict
            Arbitrary keyword arguments.
        Returns
        -------
        str
            Returns a json string. The structure of this string is unchanged,
            except that it will include all records after paginating up to the
            total indicated by the Uptime Robot API.
        """
        original_response = copy.deepcopy(response)
        total = response['pagination']['total']
        offset = response['pagination']['limit']
        while total > offset:
            new_response = self.get_monitors(**kwargs, offset=offset)
            try:
                offset += len(new_response['monitors'])
                orig_mon = original_response['monitors']
                new_mon = new_response['monitors']
                original_response['monitors'] = orig_mon + new_mon
            except KeyError:
                pass
        return original_response

    def get_account_details(self):
        """Get details about the Uptime Robot account identified by API key.
        This method maps specifically to the /getAccountDetails method of the
        Uptime Robot API. Calling this method will return account details about
        the specified Uptime Robot account.
        Returns
        -------
        str
            Returns a json string containing information about the targeted
            Uptime Robot account.
        """
        route = 'getAccountDetails'
        return self._handle_routes(route)

    def get_monitors(self, **kwargs):
        """Get monitors based on the specified keyword arguments.
        This method maps specifically to the /getMonitors method of the Uptime
        Robot API. Calling this method will return information on monitors in
        the targeted account.
        Parameters
        ----------
        **kwargs : dict
            Arbitrary keyword arguments. Used to map to any of the 'optional'
            parameters specified in the Uptime Robot documentation.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'getMonitors'
        return self._handle_routes(route, **kwargs)

    def get_all_monitors(self, **kwargs):
        """Get all monitors based on the specified keyword arguments.
        This method also maps to /getMonitors. Utilizing the get_monitors
        method and the _paginator method, this will return all monitors, beyond
        the maximum of 50 records returned by the Uptime Robot API. No change
        is made to the structure of the response. Monitors beyond the first 50
        are simply appended to the list identified by the 'monitors' key in the
        /getMonitors response.
        Parameters
        ----------
        **kwargs : dict
            Arbitrary keyword arguments. Can be used to specify any optional
            parameters indicated in the Uptime Robot API for the /getmonitors
            method.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        response = self.get_monitors(**kwargs)
        return self._paginator(response, **kwargs)

    def new_monitor(self, friendly_name, url, type, **kwargs):
        """Create a new monitor.
        This method maps to the /newMonitor method of the Uptime Robot API. It
        includes as parameters the required parameters for that method. It
        also accepts keyword args for any optional parameters specified in the
        Uptime Robot API documentation. Calling this method will create a
        monitor utilizing the parameters specified in the method call.
        Parameters
        ----------
        friendly_name : str
            This is the name displayed in the Uptime Robot dashboard. It should
            be a name that makes it easy to determine what the monitor is
            checking.
        url : str
            This is the actual URL to be checked by the monitor.
        type : str
            This is a string represntation of a numerical value. There are two
            discreet 'types' of checks made available by Uptime Robot. Specify
            1 for HTTP checks. Specify 2 for DNS checks.
        **kwargs : dict
            Arbitrary keyword arguments. Can be used to specify any optional
            parameters indicated in the Uptime Robot API for the /newMonitor
            method.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'newMonitor'
        payload = self._handle_payload(locals())
        return self._handle_routes(route, **payload)

    def edit_monitor(self, id, **kwargs):
        """Edit an existing monitor.
        This method maps to the /editMonitor method of the Uptime Robot API. It
        includes as parameters the required parameters for that method. It
        also accepts keyword args for any optional parameters specified in the
        Uptime Robot API documentation. Calling this method will edit the
        targeted monitor.
        Parameters
        ----------
        id : str
            This is a required parameter and is a string representation of the
            numerical value of the monitor to be edited.
        **kwargs : dict
            Arbitrary keyword arguments. Can be used to specify any optional
            parameters indicated in the Uptime Robot API for the /editMonitor
            method.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'editMonitor'
        payload = self._handle_payload(locals())
        return self._handle_routes(route, **payload)

    def delete_monitor(self, id):
        """Delete an extant monitor.
        This method maps to the /deletetMonitor method of the Uptime Robot API.
        It includes as parameters the required parameters for that method.
        Calling this method will delete the monitor with id, id.
        Parameters
        ----------
        id : str
            This is a required parameter and is a string representation of the
            numerical value of the monitor to be deleted.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'deleteMonitor'
        payload = self._handle_payload(locals())
        return self._handle_routes(route, **payload)

    def reset_monitor(self, id):
        """Reset monitor statistics.
        Calling this method deletes any stored data about a monitor, resetting
        it.
        Parameters
        ----------
        id : str
            This is a required parameter and is a string representation of the
            numerical value of the monitor to be reset.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'resetMonitor'
        payload = self._handle_payload(locals())
        return self._handle_routes(route, **payload)

    def get_alert_contacts(self, **kwargs):
        """
        Return information about alert contacts.
        Calling this method will return a list of alert contacts from the
        targeted Uptime Robot account.
        Parameters
        ----------
        **kwargs : dict
            Arbitrary keyword arguments. Can be used to specify any optional
            parameters indicated in the Uptime Robot API for the
            /getAlertContacts method.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'getAlertContacts'
        payload = self._handle_payload(locals())
        return self._handle_routes(route, **payload)

    def new_alert_contact(self, type, value, friendly_name, **kwargs):
        """
        Add a new alert contact.
        This method will add an alert contact with the values specified as
        parameters. This method maps to the /newAlertContact method of the
        Uptime Robot API.
        Parameters
        ----------
        type : str
            This is a string representation of the numerical value assigned to
            determine what kind of contact will be made. The possible values
            are as follows: 1 - SMS, 2 - E-mail, 3 - Twitter DM, 4 - Boxcar,
            5 - Web-Hook, 6 - Pushbullet, 9 - Pushover.
            Indicated in the API documentation the following are not yet
            implemented: 7 - Zapier, 10 - HipChat, 11 - Slack.
        value : str
            Alert contacts name or phone number.
        friendly_name : str
            Friendly name for the alert contact. Makes it easier to
            distinguish.
        **kwargs : dict
            Arbitrary keyword arguments. Can be used to specify any optional
            parameters indicated in the Uptime Robot API for the
            /newAlertContact method.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'newAlertContact'
        payload = self._handle_payload(locals())
        return self._handle_routes(route, **payload)

    def edit_alert_contact(self, id, **kwargs):
        """
        Edit an extant alert contact.
        This method maps to the /newAlertContact method of the
        Uptime Robot API. Calling this method will edit the specified Alert
        Contact utilizing the specified parameters.
        Parameters
        ----------
        id : str
            The ID of the alert contact.
        **kwargs : dict
            Arbitrary keyword arguments. Can be used to specify any optional
            parameters indicated in the Uptime Robot API for the
            /editAlertContact method.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'editAlertContact'
        payload = self._handle_payload(locals())
        return self._handle_routes(route, **payload)

    def delete_alert_contact(self, id):
        """
        Delete an extant alert contact.
        This method maps to the /editAlertContact method of the
        Uptime Robot API. Calling this method will delete the specified Alert
        Contact utilizing the specified parameters.
        Parameters
        ----------
        id : str
            The ID of the alert contact.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'deleteAlertContact'
        payload = self._handle_payload(locals())
        return self._handle_routes(route, **payload)

    def get_m_window(self, **kwargs):
        """
        Get a list of maintenance windows (MWindows)
        This method maps to the /getMWindows method of the
        Uptime Robot API. Calling this method will get information on the
        MWindows associated with the Uptime Robot account.
        Parameters
        ----------
        **kwargs : dict
            Arbitrary keyword arguments. Can be used to specify any optional
            parameters indicated in the Uptime Robot API for the /getMwindows
            method.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'getMWindows'
        payload = self._handle_payload(locals())
        return self._handle_routes(route, **payload)

    def new_m_window(self, friendly_name, type, value, start_time, duration):
        """
        Create a new maintenance window (MWindow).
        This method maps to the /getMWindows method of the
        Uptime Robot API. Calling this method will create the specified MWindow
        utilizing the specified parameters.
        Parameters
        ----------
        friendly_name : str
            Friendly maintenance window name, easy to distinguish.
        type : str
            String representation of the numerical value assigned to determine
            the type of maintenance window (frequency). The possible values
            are: '1' - Once, '2' - Daily, '3' - Weekly, '4' - Monthly.
        value : str
            Separated with '-' and used only for weekly and monthly maintenance
            windows.
        start_time : str
            Start time of the maintenance window. Unix time for type=1 and
            HH:MM for other types.
        duration : str
            Duration of the maintenance window.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'newMWindow'
        payload = self._handle_payload(locals())
        return self._handle_routes(route, **payload)

    def edit_m_window(self, id, friendly_name, value, start_time, duration):
        """
        Edit existing maintenance window (MWindow).
        This method maps to the /editMWindow method of the
        Uptime Robot API. Calling this method will edit the specified MWindow
        utilizing the specified parameters.
        Parameters
        ----------
        id : str
            ID of maintenance window.
        friendly_name : str
            Friendly maintenance window name, easy to distinguish.
        value : str
            Separated with '-' and used only for weekly and monthly maintenance
            windows.
        start_time : str
            Start time of the maintenance window. Unix time for type=1 and
            HH:MM for other types.
        duration : str
            Duration of the maintenance window.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'editMWindow'
        payload = self._handle_payload(locals())
        return self._handle_routes(route, **payload)

    def delete_m_window(self, id):
        """
        Parameters
        ----------
        id : str
            ID of maintenance window.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'deleteMWindow'
        payload = self._handle_payload(locals())
        return self._handle_routes(route, **payload)

    def get_psp(self, **kwargs):
        """
        Get a list of public status pages (PSP).
        This method maps to the /getPSPs method of the
        Uptime Robot API. Calling this method will get a list of PSP's
        associated with the Uptime Robot account.
        Parameters
        ----------
        **kwargs : dict
            Arbitrary keyword arguments. Can be used to specify any optional
            parameters indicated in the Uptime Robot API for the /getPSPs
            method.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'getPSPs'
        payload = self._handle_payload(locals())
        return self._handle_routes(route, **payload)

    def new_psp(self, type, friendly_name, monitors, **kwargs):
        """
        Create new public status page (PSP).
        This method maps to the /newPSP method of the
        Uptime Robot API. Calling this method will create the specified PSP
        utilizing the specified parameters.
        Parameters
        ----------
        type : str
            Type of PSP.
        friendly_name : str
            Friendly name of the status page.
        monitors : str
            The list of monitorID's to be displayed in the status page. '0' for
            all monitors or, ID's separated by '-'
        **kwargs : dict
            Arbitrary keyword arguments. Can be used to specify any optional
            parameters indicated in the Uptime Robot API for the /newPSP
            method.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'newPSP'
        payload = self._handle_payload(locals())
        return self._handle_routes(route, **payload)

    def edit_psp(self, id, **kwargs):
        """
        Edit an existing public status page (PSP).
        This method maps to the /editPSP method of the
        Uptime Robot API. Calling this method will edit the specified PSP
        utilizing the specified parameters.
        Parameters
        ----------
        id : str
            ID of the PSP.
        **kwargs : dict
            Arbitrary keyword arguments. Can be used to specify any optional
            parameters indicated in the Uptime Robot API for the /editPSP
            method.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'editPSP'
        payload = self._handle_payload(locals())
        return self._handle_routes(route, **payload)

    def delete_psp(self, id):
        """
        Delete a public status page (PSP).
        This method maps to the /deletePSP method of the
        Uptime Robot API. Calling this method will delete the specified PSP
        utilizing the specified parameters.
        Parameters
        ----------
        id : str
            ID of the PSP.
        Returns
        -------
        str
            Returns json string produced by calling the _handle_routes method.
        """
        route = 'deletePSP'
        payload = self._handle_payload(locals())
        return self._handle_routes(route, **payload)
