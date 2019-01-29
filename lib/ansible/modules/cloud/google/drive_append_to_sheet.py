#!/usr/bin/python

# Copyright: (c) 2018, Chris Blum <chris.n.blum@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: drive_append_to_sheet

short_description: Append columns in a Google Sheet

version_added: "2.8"

description:
    - Using this module it is possible to write columns into a Google Sheet.
    - This is especially interesting if you are trying to gather facts across lots of servers and
      you will want to do some statistical analysis on that data later on.
    - You must have the Google Sheets API activated and valid credentials for this handy
seealso:
    - name: Activate Google OAuth for Sheets
      description: Quickstart guide describing how to activate the Google OAuth API for Sheets
      link: https://developers.google.com/sheets/api/quickstart/python#step_1_turn_on_the

options:
    columns:
        description:
            - This is a list of columns that should be appended to the GSheet
        required: true
        aliases: [ 'name' ]
    sheetID:
        description:
            - The ID of sheet to append columns to.
        required: true
    client_id:
        description:
            - This is the Google OAuth client_id
            - It ends with C(.apps.googleusercontent.com)
        required: true
    client_secret:
        description:
            - This is the Google OAuth client_secret
        required: true
    sheetName:
        description:
            - This is the Sheet inside of the GSheet that we will add information
        required: false
    range:
        description:
            - This is the range
        default: 'A1:A1'
        required: false

requirements:
    - "google-api-python-client"
    - "google-auth-httplib2"
    - "google-auth-oauthlib"

author:
    - Chris Blum (@mulbc)
'''

EXAMPLES = '''
- name: Append one row with three columns
  drive_append_to_sheet:
    name: ["column A", "column B", "column C"]
    sheetID: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
    client_id: teststestst.apps.googleusercontent.com
    client_secret: S3CR3T

- name: Append one row with three variables
  drive_append_to_sheet:
    columns: ["{{ ansible_fqdn }}", "{{ ansible_kernel }}", "{{ ansible_lsb.release }}"]
    sheetID: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
    client_id: teststestst.apps.googleusercontent.com
    client_secret: S3CR3T
'''

RETURN = '''
new_columns:
    description: The columns that were appended
    returned: success
    type: list
msg:
    description: The response we got from the Google API
    returned: success
    type: dict
'''
try:
    import pickle
    import os.path
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import_ok = True
except ImportError:
    import_ok = False

from ansible.module_utils.basic import AnsibleModule
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """

    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        columns=dict(type='list', required=True, aliases=['name']),
        sheetID=dict(type='str', required=True),
        client_id=dict(type='str', required=True),
        client_secret=dict(type='str', no_log=True, required=True),
        sheetName=dict(type='str', ),
        range=dict(type='str', default='A1:A1'))

    module = AnsibleModule(argument_spec=module_args, bypass_checks=True)

    if not import_ok:
        module.fail_json(msg='Please install the google client libraries:\n \
        pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib ')

    columns = module.params.get('columns')
    result = dict(changed=False, columns=columns, msg='')

    if not isinstance(columns, (list, )):
        module.fail_json(msg='The name needs to be a list containing the values for columns')
    sheetID = module.params.get('sheetID')
    sheetRange = ''
    if module.params.get('sheetName'):
        sheetRange = '%s!' % module.params.get('sheetName')
    sheetRange += module.params.get('range')
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not module.params.get('client_id') \
                    or '.apps.googleusercontent.com' \
                    not in module.params.get('client_id'):
                module.fail_json(msg='Supply a valid Google OAuth client_id')
            if not module.params.get('client_secret'):
                module.fail_json(msg='Supply a valid Google OAuth client_secret')
            credentials = {
                "installed": {
                    "client_id": module.params.get('client_id'),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_secret": module.params.get('client_secret'),
                }
            }
            # flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            try:
                flow = InstalledAppFlow.from_client_config(credentials, SCOPES)
                creds = flow.run_local_server()
            except Exception as err:
                module.fail_json(msg='Failed to Acquire Google OAuth Token: \n%s' % err)

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    try:
        # Call the Sheets API
        request = service.spreadsheets().values().append(
            spreadsheetId=sheetID,
            range=sheetRange,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={
                "majorDimension": "ROWS",
                "range": sheetRange,
                "values": [columns]
            })
        response = request.execute()
    except Exception as err:
        module.fail_json(msg='Failed to update the GSheet: %s' % err)

    if not response:
        module.fail_json(msg='Did not get response after append:')

    result['changed'] = True
    result['msg'] = response
    module.exit_json(**result)
    # TODO: Handle response properly


if __name__ == '__main__':
    main()
