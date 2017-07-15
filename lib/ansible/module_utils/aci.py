#!/usr/bin/python


import socket
import json
import requests

class aci(object):

    def __init__(self,host,protocol,username,password, **kwargs):
        self.host = host
        self.protocol = protocol
        self.username = username
        self.password = password
        
    
    def login(host,protocol,username,password):
        host = socket.gethostbyname(host)
        apic = '{0}://{1}/'.format(protocol, host)

        auth = dict(aaaUser=dict(attributes=dict(name=username,
                    pwd=password)))
        url = apic + 'api/aaaLogin.json'

        authenticate = requests.post(url, data=json.dumps(auth), timeout=2,
                                 verify=False)
   
        auth_status = authenticate.status_code
        auth_cookie = authenticate.cookie
    
        if auth_status != 200:
           module.fail_json(msg='could not authenticate to apic',
                         status=authenticate.status_code,
                         response=authenticate.text)
        return auth_status, auth_cookie;

    def post_request(post_uri,action,cookie):
         post_uri = str(post_uri) 
         if post_uri.startswith('/'):
           post_uri = post_uri[1:]
         post_url = apic + post_uri

         post_request = requests.post(post_url, cookies = cookie, verify=False)

         response = post_request.text
         status = post_request.status_code

         changed = validate(status,action)
  
         return response, status, changed;

    def get_request(get_uri,action,cookie):
         get_uri = str(get_uri)
         if get_uri.startswith('/'):
            get_uri = get_uri[1:]
         get_url = apic + get_uri
 
         get_request = requests.get(get_url, cookies = cookie, verify=Fales)
    
         response = get_request.text
         status = get_request.status_code

         changed = validate(status,action)
         return response,status,changed;

    def validate(status, action):
        changed = False
        if status == 200:
           if action == 'post':
              changed = True
           else:
              changed = False
        else:
           module.fail_json(msg='error issuing api request',
                         response=response, status=status)

        return changed;
