#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import time
import smbc
import uuid
import ansible

import base64
import hashlib
import imp
import os
import re
import shlex
import traceback
import urlparse
from ansible import errors
from ansible import utils
from ansible.callbacks import vvv, vvvv, verbose
from ansible.runner.shell_plugins import powershell
from ansible.runner.return_data import ReturnData

class ActionModule(object):
  def __init__(self, runner):
    self.runner = runner

  def run(self, conn, tmp_path, module_name, module_args, inject, complex_args=None, **kwargs):
    ''' handler for file transfer operations '''

    # load up options
    options = {}
    if complex_args:
      options.update(complex_args)
    options.update(utils.parse_kv(module_args))
    src     = options.get('src', None)
    content = options.get('content', None)
    locdest = options.get('dest', None)
    host    = conn.host
    force   = utils.boolean(options.get('force', 'yes'))

    dest     = options.get('dest')
    share    = (dest.split(':')[0]+'$').lower()
    loc      = dest.split(':')[1].replace('\\','/')
    dest     = 'smb://' + host + '/' + share + loc

    if (src is None and content is None and not 'first_available_file' in inject) or dest is None:
      result=dict(failed=True, msg="src (or content) and dest are required")
      return ReturnData(conn=conn, result=result)
    elif (src is not None or 'first_available_file' in inject) and content is not None:
      result=dict(failed=True, msg="src and content are mutually exclusive")
      return ReturnData(conn=conn, result=result)

    if not (content is None):
        src = tempfile
        dfile = open(src, 'wb')
        dfile.write(content)
        dfile.flush()
        dfile.close()

    if not os.path.exists(src):
      result = dict(failed=True, msg="Source %s failed to transfer" % (src))
      return ReturnData(conn=conn, result=result)
    if not os.access(src, os.R_OK):
      result = dict(failed=True, msg="Source %s not readable" % (src))
      return ReturnData(conn=conn, result=result)
       
    md5sum_src = utils.md5(src)
    md5sum_dest = None

    changed = False
    tempfile = str(uuid.uuid4().get_hex()[0:32])

    if md5sum_src is None:
      result = dict(failed=True, msg="could not find src=%s" % (src))
      return ReturnData(conn=conn, result=result)

    if conn.shell.path_has_trailing_slash(dest):
      result = dict(failed=True, msg="can't transfer directories src=%s" % (src))
      return ReturnData(conn=conn, result=result)

    if (self.check_file(dest)):
      md5sum_dest = winrm._remote.md5(self, conn, tmp, locdest)
      
      if not ( not (md5sum_src == md5sum_dest) and not force):
        result = dict(msg="file already exists %s" % (src), src=src, dest=locdest, changed=False)
        return ReturnData(conn=conn, result=result)
    else:
      try:
        self.upload(src, ctx, dest)
        changed = True
      except:
        result = dict(failed=True, msg="Failed to copy file.")
        return ReturnData(conn=conn, result=result)

      if ( len(content) > 0 ):
        os.remove(src)

      if not self.validating(src, dest, content):
        result = dict(failed=True, msg="The validation has failed for the uploaded file.")
        return ReturnData(conn=conn, result=result)

    res_args = dict(
        dest = locdest, src = src, md5sum = md5sum_src, changed = changed
    )

    result = dict(dest=dest, src=source, changed=changed)
    return ReturnData(conn=conn, result=result)

  def setUp():
    global ctx
    ctx = smbc.Context()
    ctx.optionNoAutoAnonymousLogin = True
    ctx.functionAuthData = auth_fn

  def tearDown():
    global ctx
    del ctx

  def auth_fn(ansible_hostname, share, ansible_workgroup, ansible_ssh_user, ansible_ssh_pass):
    return (workgroup, ansible_ssh_user, ansible_ssh_pass)

  def upload(src, ctx, rfile):
    sfile = open(src, 'rb')
    dfile = ctx.open(rfile, os.O_CREAT | os.O_TRUNC | os.O_WRONLY)
    for buf in sfile:
      ret = dfile.write(buf)
      if ret < 0:
        raise IOError("smbc write error")
    sfile.close()
    dfile.close()
    return True

  def download(ctx, rfile, src):
    sfile = ctx.open(rfile, os.O_RDONLY)
    dfile = open(src, 'wb')
    for buf in sfile:
        dfile.write(buf)
    dfile.flush()
    sfile.close()
    dfile.close()
    return True

  def read_file(rfile):
    sfile=ctx.open(rfile)
    fcont = sfile.read()
    sfile.close()
    return fcont

  def check_file(rfile):
    try:
      read_file(rfile)
      return True
    except:
      return False

  def validating(src, rfile, content):
    tempfile = str(uuid.uuid4().get_hex()[0:32])
    download(ctx, rfile, tempfile)
    if (len(content) > 0):
      result = (read_file(rfile) == content)
    else:
      download(ctx, rfile, tempfile)
      result = (module.md5(src) == module.md5(tempfile))
      os.remove(tempfile)
    return result

