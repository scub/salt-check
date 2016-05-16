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
        self.assertions_list = "assertEqual assertNotEqual assertTrue assertFalse assertIn assertGreater assertGreaterEqual assertLess assertLessEqual".split()
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

    #def is_valid_test(self, test_dict):
        return True

    def call_salt_command(self,
                          fun,
                          args,
                          kwargs):
        '''Generic call of salt Caller command'''
        value = False
        try:
            if kwargs:
                value = self.salt_lc.function(fun, args, kwargs)
            elif args:
                value = self.salt_lc.function(fun, args)
            else:
                value = self.salt_lc.function(fun)
        except Exception as err:
            value = err
        return value
  
    #def run_test(self, test_dict):
    #    return type(test_dict)

    def run_test(self, test_dict):
        if is_valid_test(test_dict):
            mod_and_func = test_dict['module_and_function']
            args = test_dict.get('args', None)
            # handling the right number of args should be done elsewhere, here we just pass them on
            # need to handle lists nicely here...or at least fail nicely
            #if args and args not isinstance(args, list):
            #    args = list(args.split())
            assertion = test_dict['assertion']
            expected_return = test_dict['expected-return']
            kwargs = test_dict.get('kwargs', None)
            actual_return =  self.call_salt_command(mod_and_func, args, kwargs)
            if assertion == "assertEqual":
                value = self.assert_equal(expected_return, actual_return)
            elif assertion == "assertNotEqual":
                value = self.assert_not_equal(expected_return, actual_return)
            elif assertion == "assertTrue":
                value = self.assert_true(expected_return)
            elif assertion == "assertFalse":
                value = self.assert_false(expected_return)
            elif assertion == "assertIn":
                value = self.assert_in(expected_return, actual_return)
            elif assertion == "assertNotIn":
                value = self.assert_not_in(expected_return, actual_return)
            elif assertion == "assertGreater":
                value = self.assert_greater(expected_return, actual_return)
            elif assertion == "assertGreaterEqual":
                value = self.assert_greater_equal(expected_return, actual_return)
            elif assertion == "assertLess":
                value = self.assert_less(expected_return, actual_return)
            elif assertion == "assertLessEqual":
                value = self.assert_less_equal(expected_return, actual_return)
            else:
                value = (False, None)
        return value
        #return [mod_and_func, args, kwargs]


    @staticmethod
    def assert_equal(expected, returned):
        '''
        Test if two objects are equal
        '''
        result = True
        try:
            assert (expected == returned), "{0} is not equal to {1}".format(expected, returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_not_equal(expected, returned):
        '''
        Test if two objects are not equal
        '''
        result = (True, None)
        try:
            assert (expected != returned), "{0} is equal to {1}".format(expected, returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_true(returned):
        '''
        Test if an boolean is True
        '''
        # may need to cast returned to string
        result = (True, None)
        try:
            assert (returned is True), "{0} not True".format(returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_false(returned):
        '''
        Test if an boolean is False
        '''
        # may need to cast returned to string
        result = (True, None)
        try:
            assert (returned is False), "{0} not False".format(returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_in(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = (True, None)
        try:
            assert (expected in returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_not_in(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = (True, None)
        try:
            assert (expected not in returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_greater(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = (True, None)
        try:
            assert (expected > returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_greater_equal(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = (True, None)
        try:
            assert (expected >= returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_less(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = (True, None)
        try:
            assert (expected < returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_less_equal(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = (True, None)
        try:
            assert (expected <= returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    def show_minion_options(self):
        cachedir = self.__opts__['cachedir']
        root_dir = self.__opts__['root_dir']
        states_dirs = self.__opts__['states_dirs']
        environment = self.__opts__['environment']
        return {'cachedir':cachedir, 'root_dir':root_dir, 'states_dirs':states_dirs, 'environment':environment}
        #return self.__opts__

    def show_state_search_path(self):
        root_dir = self.__opts__.get('root_dir', None)
        cachedir = self.__opts__.get('cachedir', None)
        file_roots = self.__opts__.get('file_roots', None)
        return root_dir, cachedir, file_roots

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

def show_minion_options():
    sc = SaltCheck()
    return sc.show_minion_options()

def show_state_search_path():
    ''' Show the search paths used for states '''
    sc = SaltCheck()
    return sc.show_state_search_path()

def run_test(**kwargs):
    '''
    Enables running one salt_check test via cli
    CLI Example::
        salt '*' salt_check.run_test '{"module_and_function": "test.echo", "assertion": "assertEqual", "expected-return": "This works!", "args":"This works!" }'
    '''
    # salt converts the string to a dictionary auto-magically
    sc = SaltCheck()
    test = kwargs.get('test', None)
    #test = "'" + test + "'"
    #return "type of object is {}".format(type(test))
    #return "str given is {}".format(test)
    if test and isinstance(test, dict):
        return sc.run_test(test)
    else:
        return "test must be dictionary"
    #return test_dict_str
