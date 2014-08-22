#!/usr/bin/env python
import os

def get_nova_credentials_v2():
  d               = {}
  d['version']    = '2'
  d['username']   = os.environ['OS_USERNAME']
  d['api_key']    = os.environ['OS_PASSWORD']
  d['auth_url']   = os.environ['OS_AUTH_URL']
  d['project_id'] = os.environ['OS_TENANT_NAME']
  return d
