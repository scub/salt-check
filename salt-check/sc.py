#!/usr/bin/env python
'''This custom salt module makes it easy to test salt states and highstates.
   Author: William Cannon  william period cannon at gmail dot com'''
import os
import yaml
import os.path
import salt.client
import salt.minion
import salt.config

class SaltCheck(object):
    '''
    This class implements the salt_check
    '''

    def __init__(self):
        self.__opts__ = salt.config.minion_config('/etc/salt/minion')
        self.__opts__['file_client'] = 'local'
        self.salt_lc = salt.client.Caller(mopts=self.__opts__)
        self.results_dict = {}
        self.results_dict_summary = {}
        self.assertions_list = "assertEqual assertNotEqual".split()
        self.modules = self.populate_salt_modules_list()

    def populate_salt_modules_list(self):
        valid_modules = __salt__['sys.list_modules']()
        return valid_modules

    def sync_salt_states(self):
        '''Sync the salt states in order to get the salt-check-tests
           directory in a state folder from the master'''
        __salt__['saltutil.sync_states']
        return

    def is_valid_module(self, module_name):
        '''Determines if a module is valid on a minion'''
        if module_name not in self.modules: 
            val = False
        else:
            val = True
        return val

    def is_valid_function(self, module_name, function):
        '''Determine if a function is valid for a module'''
        functions = __salt__['sys.list_functions'](module_name)
        return "{}.{}".format(module_name, function) in functions

    def is_valid_test(self, test_dict):
        '''Determine if a test contains a test name, a valid module and function,
           a valid assertion, an expected return value'''
        tots = 0 # need 6 to pass test
        m_and_f = test_dict.get('module_and_function', None)
        assertion = test_dict.get('assertion', None)
        expected_return =  test_dict.get('expected-return', None)
        if m_and_f:
           tots += 1 
           module,function = m_and_f.split('.')
           if self.is_valid_module(module):
               tots += 1 
           if self.is_valid_function(module, function):
               tots += 1 
        if assertion:
           tots += 1 
           if assertion in self.assertions_list:
               tots += 1
        if expected_return:
           tots += 1 
        return tots >= 6


    def call_salt_command(self,
                          fun,
                          args=(),
                          **kwargs):
        '''Generic call of salt Caller command'''
        value = True
        try:
            value = self.salt_lc.cmd(fun, args, **kwargs)
        except Exception:
            value = False
        return value


def is_valid_module(module_name):
    sc = SaltCheck()
    return sc.is_valid_module(module_name)

def is_valid_function(module_name, function):
    sc = SaltCheck()
    return sc.is_valid_function(module_name, function)

def is_valid_test(test_dict):
    sc = SaltCheck()
    return sc.is_valid_test(test_dict)

def sync_salt_states():
    sc = SaltCheck()
    return sc.sync_salt_states()
