#!/usr/bin/env python

import os
import shutil
from tempfile import mkstemp
from tempfile import mkdtemp
from ansible.playbook.play import Play
import ansible

import unittest
from nose.plugins.skip import SkipTest


class FakeCallBacks(object):
    def __init__(self):
        pass
    def on_vars_prompt(self):
        pass
    def on_import_for_host(self, host, filename):
        pass

class FakeInventory(object):
    def __init__(self):
        self.hosts = {}
    def basedir(self):
        return "."        
    def src(self):
        return "fakeinventory"
    def get_variables(self, host, vault_password=None):
        if host in self.hosts:
            return self.hosts[host]        
        else:
            return {}            

class FakePlayBook(object):
    def __init__(self):
        self.extra_vars = {}
        self.remote_user = None
        self.remote_port = None
        self.sudo = None
        self.sudo_user = None
        self.su = None
        self.su_user = None
        self.transport = None
        self.only_tags = None
        self.skip_tags = None
        self.VARS_CACHE = {}
        self.SETUP_CACHE = {}
        self.inventory = FakeInventory()
        self.callbacks = FakeCallBacks()

        self.VARS_CACHE['localhost'] = {}


class TestMe(unittest.TestCase):

    ########################################
    # BASIC FILE LOADING BEHAVIOR TESTS
    ########################################

    def test_play_constructor(self):
        # __init__(self, playbook, ds, basedir, vault_password=None)
        playbook = FakePlayBook()
        ds = { "hosts": "localhost"}
        basedir = "."
        play = Play(playbook, ds, basedir)

    def test_vars_file(self):

        # make a vars file
        fd, temp_path = mkstemp()
        f = open(temp_path, "wb")
        f.write("foo: bar\n")
        f.close()

        # create a play with a vars_file
        playbook = FakePlayBook()
        ds = { "hosts": "localhost",
               "vars_files": [temp_path]}
        basedir = "."
        play = Play(playbook, ds, basedir)
        os.remove(temp_path)

        # make sure the variable was loaded
        assert 'foo' in play.vars, "vars_file was not loaded into play.vars"
        assert play.vars['foo'] == 'bar', "foo was not set to bar in play.vars"

    def test_vars_file_nonlist_error(self):

        # make a vars file
        fd, temp_path = mkstemp()
        f = open(temp_path, "wb")
        f.write("foo: bar\n")
        f.close()

        # create a play with a string for vars_files
        playbook = FakePlayBook()
        ds = { "hosts": "localhost",
               "vars_files": temp_path}
        basedir = "."
        error_hit = False
        try:
            play = Play(playbook, ds, basedir)
        except:
            error_hit = True
        os.remove(temp_path)

        assert error_hit == True, "no error was thrown when vars_files was not a list"


    def test_multiple_vars_files(self):

        # make a vars file
        fd, temp_path = mkstemp()
        f = open(temp_path, "wb")
        f.write("foo: bar\n")
        f.close()

        # make a second vars file
        fd, temp_path2 = mkstemp()
        f = open(temp_path2, "wb")
        f.write("baz: bang\n")
        f.close()


        # create a play with two vars_files
        playbook = FakePlayBook()
        ds = { "hosts": "localhost",
               "vars_files": [temp_path, temp_path2]}
        basedir = "."
        play = Play(playbook, ds, basedir)
        os.remove(temp_path)
        os.remove(temp_path2)

        # make sure the variables were loaded
        assert 'foo' in play.vars, "vars_file was not loaded into play.vars"
        assert play.vars['foo'] == 'bar', "foo was not set to bar in play.vars"
        assert 'baz' in play.vars, "vars_file2 was not loaded into play.vars"
        assert play.vars['baz'] == 'bang', "baz was not set to bang in play.vars"

    def test_vars_files_first_found(self):

        # make a vars file
        fd, temp_path = mkstemp()
        f = open(temp_path, "wb")
        f.write("foo: bar\n")
        f.close()

        # get a random file path        
        fd, temp_path2 = mkstemp()
        # make sure this file doesn't exist
        os.remove(temp_path2)

        # create a play
        playbook = FakePlayBook()
        ds = { "hosts": "localhost",
               "vars_files": [[temp_path2, temp_path]]}
        basedir = "."
        play = Play(playbook, ds, basedir)
        os.remove(temp_path)

        # make sure the variable was loaded
        assert 'foo' in play.vars, "vars_file was not loaded into play.vars"
        assert play.vars['foo'] == 'bar', "foo was not set to bar in play.vars"

    def test_vars_files_multiple_found(self):

        # make a vars file
        fd, temp_path = mkstemp()
        f = open(temp_path, "wb")
        f.write("foo: bar\n")
        f.close()

        # make a second vars file
        fd, temp_path2 = mkstemp()
        f = open(temp_path2, "wb")
        f.write("baz: bang\n")
        f.close()

        # create a play
        playbook = FakePlayBook()
        ds = { "hosts": "localhost",
               "vars_files": [[temp_path, temp_path2]]}
        basedir = "."
        play = Play(playbook, ds, basedir)
        os.remove(temp_path)
        os.remove(temp_path2)

        # make sure the variables were loaded
        assert 'foo' in play.vars, "vars_file was not loaded into play.vars"
        assert play.vars['foo'] == 'bar', "foo was not set to bar in play.vars"
        assert 'baz' not in play.vars, "vars_file2 was loaded after vars_file1 was loaded"

    def test_vars_files_assert_all_found(self):

        # make a vars file
        fd, temp_path = mkstemp()
        f = open(temp_path, "wb")
        f.write("foo: bar\n")
        f.close()

        # make a second vars file
        fd, temp_path2 = mkstemp()
        # make sure it doesn't exist
        os.remove(temp_path2)

        # create a play
        playbook = FakePlayBook()
        ds = { "hosts": "localhost",
               "vars_files": [temp_path, temp_path2]}
        basedir = "."

        error_hit = False
        error_msg = None

        try:
            play = Play(playbook, ds, basedir)
        except ansible.errors.AnsibleError, e:
            error_hit = True
            error_msg = e

        os.remove(temp_path)
        assert error_hit == True, "no error was thrown for missing vars_file"


    ########################################
    # VARIABLE PRECEDENCE TESTS
    ########################################

    # On the first run vars_files are loaded into play.vars by host == None
    #   * only files with vars from host==None will work here
    # On the secondary run(s), a host is given and the vars_files are loaded into VARS_CACHE
    #   * this only occurs if host is not None, filename2 has vars in the name, and filename3 does not

    # filename  -- the original string
    # filename2 -- filename templated with play vars
    # filename3 -- filename2 template with inject (hostvars + setup_cache + vars_cache)
    # filename4 -- path_dwim(filename3)

    def test_vars_files_for_host(self):

        # host != None
        # vars in filename2
        # no vars in filename3

        # make a vars file
        fd, temp_path = mkstemp()
        f = open(temp_path, "wb")
        f.write("foo: bar\n")
        f.close()

        # build play attributes
        playbook = FakePlayBook()
        ds = { "hosts": "localhost",
               "vars_files": ["{{ temp_path }}"]}
        basedir = "."
        playbook.VARS_CACHE['localhost']['temp_path'] = temp_path

        # create play and do first run        
        play = Play(playbook, ds, basedir)

        # the second run is started by calling update_vars_files        
        play.update_vars_files(['localhost'])
        os.remove(temp_path)

        assert 'foo' in play.playbook.VARS_CACHE['localhost'], "vars_file vars were not loaded into vars_cache"
        assert play.playbook.VARS_CACHE['localhost']['foo'] == 'bar', "foo does not equal bar"

    def test_vars_files_for_host_with_extra_vars(self):

        # host != None
        # vars in filename2
        # no vars in filename3

        # make a vars file
        fd, temp_path = mkstemp()
        f = open(temp_path, "wb")
        f.write("foo: bar\n")
        f.close()

        # build play attributes
        playbook = FakePlayBook()
        ds = { "hosts": "localhost",
               "vars_files": ["{{ temp_path }}"]}
        basedir = "."
        playbook.VARS_CACHE['localhost']['temp_path'] = temp_path
        playbook.extra_vars = {"foo": "extra"}

        # create play and do first run        
        play = Play(playbook, ds, basedir)

        # the second run is started by calling update_vars_files        
        play.update_vars_files(['localhost'])
        os.remove(temp_path)

        assert 'foo' in play.vars, "extra vars were not set in play.vars"
        assert 'foo' in play.playbook.VARS_CACHE['localhost'], "vars_file vars were not loaded into vars_cache"
        assert play.playbook.VARS_CACHE['localhost']['foo'] == 'extra', "extra vars did not overwrite vars_files vars"


    ########################################
    # COMPLEX FILENAME TEMPLATING TESTS
    ########################################

    def test_vars_files_two_vars_in_name(self):

        # self.vars = ds['vars']
        # self.vars += _get_vars() ... aka extra_vars

        # make a temp dir
        temp_dir = mkdtemp()

        # make a temp file
        fd, temp_file = mkstemp(dir=temp_dir)
        f = open(temp_file, "wb")
        f.write("foo: bar\n")
        f.close()

        # build play attributes
        playbook = FakePlayBook()
        ds = { "hosts": "localhost",
               "vars": { "temp_dir": os.path.dirname(temp_file),
                         "temp_file": os.path.basename(temp_file) },
               "vars_files": ["{{ temp_dir + '/' + temp_file }}"]}
        basedir = "."

        # create play and do first run        
        play = Play(playbook, ds, basedir)

        # cleanup
        shutil.rmtree(temp_dir)

        assert 'foo' in play.vars, "double var templated vars_files filename not loaded"
    
    def test_vars_files_two_vars_different_scope(self):

        #
        # Use a play var and an inventory var to create the filename
        #

        # self.playbook.inventory.get_variables(host)
        #   {'group_names': ['ungrouped'], 'inventory_hostname': 'localhost', 
        #   'ansible_ssh_user': 'root', 'inventory_hostname_short': 'localhost'}

        # make a temp dir
        temp_dir = mkdtemp()

        # make a temp file
        fd, temp_file = mkstemp(dir=temp_dir)
        f = open(temp_file, "wb")
        f.write("foo: bar\n")
        f.close()

        # build play attributes
        playbook = FakePlayBook()
        playbook.inventory.hosts['localhost'] = {'inventory_hostname': os.path.basename(temp_file)}
        ds = { "hosts": "localhost",
               "vars": { "temp_dir": os.path.dirname(temp_file)},
               "vars_files": ["{{ temp_dir + '/' + inventory_hostname }}"]}
        basedir = "."

        # create play and do first run        
        play = Play(playbook, ds, basedir)

        # do the host run        
        play.update_vars_files(['localhost'])

        # cleanup
        shutil.rmtree(temp_dir)

        assert 'foo' not in play.vars, \
            "mixed scope vars_file loaded into play vars"
        assert 'foo' in play.playbook.VARS_CACHE['localhost'], \
            "differently scoped templated vars_files filename not loaded"
        assert play.playbook.VARS_CACHE['localhost']['foo'] == 'bar', \
            "foo is not bar"    

    def test_vars_files_two_vars_different_scope_first_found(self):

        #
        # Use a play var and an inventory var to create the filename
        #

        # make a temp dir
        temp_dir = mkdtemp()

        # make a temp file
        fd, temp_file = mkstemp(dir=temp_dir)
        f = open(temp_file, "wb")
        f.write("foo: bar\n")
        f.close()

        # build play attributes
        playbook = FakePlayBook()
        playbook.inventory.hosts['localhost'] = {'inventory_hostname': os.path.basename(temp_file)}
        ds = { "hosts": "localhost",
               "vars": { "temp_dir": os.path.dirname(temp_file)},
               "vars_files": [["{{ temp_dir + '/' + inventory_hostname }}"]]}
        basedir = "."

        # create play and do first run        
        play = Play(playbook, ds, basedir)

        # do the host run        
        play.update_vars_files(['localhost'])

        # cleanup
        shutil.rmtree(temp_dir)

        assert 'foo' not in play.vars, \
            "mixed scope vars_file loaded into play vars"
        assert 'foo' in play.playbook.VARS_CACHE['localhost'], \
            "differently scoped templated vars_files filename not loaded"
        assert play.playbook.VARS_CACHE['localhost']['foo'] == 'bar', \
            "foo is not bar"    
    

