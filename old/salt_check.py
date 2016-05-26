#!/usr/bin/env python
'''This custom salt module makes it easy to test salt states and highstates.
   Author: William Cannon  william period cannon at gmail dot com'''
import json
import salt.client
import salt.config
import yaml
import os
import os.path

class Tester(object):
    '''
    This class implements the salt_check
    '''

    def __init__(self):
        self.salt_lc = salt.client.Caller()
        self.results_dict = {}
        self.results_dict_summary = {}

    def run_one_test(self, minion_list, test_dict):
        '''
        Run one salt_check test, return results
        '''
        results_dict = {}
        test_name = test_dict.keys()[0]
        m_f = test_dict[test_name].get('module_and_function', None)
        t_args = test_dict[test_name].get('args', None)
        if not t_args:
            t_args = []
        elif not isinstance(t_args, list):
            # e.g. args: x y z --> convert to ['x','y','z']
            t_args = t_args.split()
        t_kwargs = test_dict[test_name].get('kwargs', None)
        pillar_data = test_dict[test_name].get('pillar-data', None)
        if pillar_data:
            if not t_kwargs:
                t_kwargs = {}
            t_kwargs['pillar'] = pillar_data
        assertion = test_dict[test_name].get('assertion', None)
        expected_return = test_dict[test_name].get('expected-return', None)
        #print "\ntest name: {}".format(test_name)
        #print "module and function: {}".format(m_f)
        #print "args: {}".format(t_args)
        #print "kwargs---> {}".format(t_kwargs)
        #print "pillar---> {}".format(pillar_data)
        values = self.call_salt_command(tgt=minion_list,
                                        fun=m_f,
                                        arg=t_args,
                                        kwarg=t_kwargs,
                                        expr_form='list')
        #print "returned from client: {}".format(values)
        for key, val in values.items():
            if assertion == "assertEqual":
                value = self.assert_equal(expected_return, val)
                results_dict[key] = value
            elif assertion == "assertNotEqual":
                value = self.assert_not_equal(expected_return, val)
                results_dict[key] = value
            elif assertion == "assertTrue":
                value = self.assert_true(val)
                results_dict[key] = value
            elif assertion == "assertFalse":
                value = self.assert_false(val)
                results_dict[key] = value
            elif assertion == "assertIn":
                value = self.assert_in(expected_return, val)
                results_dict[key] = value
            elif assertion == "assertNotIn":
                value = self.assert_not_in(expected_return, val)
                results_dict[key] = value
            elif assertion == "assertGreater":
                value = self.assert_greater(expected_return, val)
                results_dict[key] = value
            elif assertion == "assertGreaterEqual":
                value = self.assert_greater_equal(expected_return, val)
                results_dict[key] = value
            elif assertion == "assertLess":
                value = self.assert_less(expected_return, val)
                results_dict[key] = value
            elif assertion == "assertLessEqual":
                value = self.assert_less_equal(expected_return, val)
                results_dict[key] = value
            else:
                value = "???"
        return [test_name, results_dict]


    def call_salt_command(self,
                          fun,
                          arg=(),
                          timeout=None,
                          expr_form='compound',
                          ret='',
                          jid='',
                          kwarg=None,
                          **kwargs):
        '''Generic call of salt command'''
        value = True
        try:
            if self.transport == 'salt':
                value = self.salt_lc.cmd(fun, arg, timeout,
                                     expr_form, ret, jid, kwarg, **kwargs)
            else:
                value = self.salt_lc.cmd(fun, arg, timeout,
                                     expr_form, kwarg, **kwargs)
             
            #print "value = {0}".format(value)
        except Exception, error:
            print error
            value = False
        return value

    @staticmethod
    def assert_equal(expected, returned):
        '''
        Test if two objects are equal
        '''
        result = True
        try:
            assert (expected == returned), "{0} is not equal to {1}".format(expected, returned)
        except AssertionError as err:
            result = [False, err]
        return result

    @staticmethod
    def assert_not_equal(expected, returned):
        '''
        Test if two objects are not equal
        '''
        result = True
        try:
            assert (expected != returned), "{0} is equal to {1}".format(expected, returned)
        except AssertionError as err:
            result = [False, err]
        return result

    @staticmethod
    def assert_true(returned):
        '''
        Test if an boolean is True
        '''
        # may need to cast returned to string
        result = True
        try:
            assert (returned is True), "{0} not True".format(returned)
        except AssertionError as err:
            result = [False, err]
        return result

    @staticmethod
    def assert_false(returned):
        '''
        Test if an boolean is False
        '''
        # may need to cast returned to string
        result = True
        try:
            assert (returned is False), "{0} not False".format(returned)
        except AssertionError as err:
            result = [False, err]
        return result

    @staticmethod
    def assert_in(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = True
        try:
            assert (expected in returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = [False, err]
        return result

    @staticmethod
    def assert_not_in(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = True
        try:
            assert (expected not in returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = [False, err]
        return result

    @staticmethod
    def assert_greater(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = True
        try:
            assert (expected > returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = [False, err]
        return result

    @staticmethod
    def assert_greater_equal(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = True
        try:
            assert (expected >= returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = [False, err]
        return result

    @staticmethod
    def assert_less(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = True
        try:
            assert (expected < returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = [False, err]
        return result

    @staticmethod
    def assert_less_equal(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = True
        try:
            assert (expected <= returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = [False, err]
        return result

    def summarize_results(self):
        # save this to another separate data structure for easy retrieval in "compact/regular" mode
        '''
        Walk through the results, and add a summary "passed/failed"
        count of tests to each minion
        '''
        for key in self.results_dict.keys(): # get minion, and set of tests
            #print "Minion id: {0}".format(key)
            summary = {'pass':0, 'fail':0}
            for ley, wal in self.results_dict[key].items(): # print test and result
                #print "Test: {0}".format(ley).ljust(40),
                if wal != True:
                    summary['fail'] = summary.get('fail', 0) + 1
                    #print "Result: False --> {0}".format(wal[1]).ljust(40)
                else:
                    summary['pass'] = summary.get('pass', 0) + 1
                    #print "Result: {0}".format(wal).ljust(40)
            self.results_dict_summary[key] = summary
        return

    def print_results_as_text(self):
        '''
        Print results verbosely
        '''
        print "\nRESULTS OF TESTS BY MINION ID:\n "
        for key in self.results_dict.keys(): # get minion, and set of tests
            print "Minion id: {0}".format(key)
            print "Summary: Passed: {0}, Failed: {1}".format(
                self.results_dict_summary[key].get('pass', 0),
                self.results_dict_summary[key].get('fail', 0))
            #for ley, wal in self.results_dict[key].items(): # print test and result
            for ley, wal in sorted(self.results_dict[key].items()): # print test and result
                print "Test: {0}".format(ley).ljust(40),
                if wal != True:
                    print "Result: False --> {0}".format(wal[1]).ljust(40)
                else:
                    print "Result: {0}".format(wal).ljust(40)
                #print "Test: {0}                           Result: {1}".format(l,w)
            print

    def print_results_verbose_low(self):
        '''
        Print results tersely
        '''
        print "\nRESULTS OF TESTS BY MINION ID:\n "
        for key in self.results_dict.keys(): # get minion, and set of tests
            print "\nMinion id: {0}".format(key)
            print "Summary: Passed: {0}, Failed: {1}".format(
                self.results_dict_summary[key].get('pass', 0),
                self.results_dict_summary[key].get('fail', 0))
            sorted(self.results_dict[key])
            for ley, wal in sorted(self.results_dict[key].items()): # print test and result
                if wal != True:
                    print "Test: {0}".format(ley).ljust(40),
                    print "Result: False --> {0}".format(wal[1]).ljust(40)


class TestLoader(object):
    '''
    Class loads in test files
    '''

    def __init__(self, file_or_dir):
        self.filepath = file_or_dir
        self.path_type = None
        self.test_files = [] # list of file paths
        self.test_dict = {}

    def is_file_or_dir(self):
        '''determine if the pathname is a file or dir'''
        if os.path.isdir(self.filepath):
            self.path_type = 'dir'
            #print "self.path_type: {0}".format(self.path_type)
        elif os.path.isfile(self.filepath):
            self.path_type = 'file'
            #print "self.path_type: {0}".format(self.path_type)
        else:
            self.path_type = "Unsupported path type"
            #print "self.path_type: {0}".format(self.path_type)

    def load_test_suite(self, path_type):
        '''load tests either from one file, or a set of files'''
        if self.path_type == 'file':
            self.load_file(self.filepath)
        elif self.path_type == 'dir':
            self.gather_files()
            for f in self.test_files:
                self.load_file(f)

    def gather_files(self ):
        rootDir = self.filepath
        for dirName, subdirList, fileList in os.walk(rootDir):
            #print('Found directory: %s' % dirName)
            for fname in fileList:
                #print('\t%s' % fname)
                if fname.endswith('.tst'):
                    start_path = dirName + os.sep + fname
                    #print "start_path: {0}".format(start_path)
                    full_path = os.path.abspath(start_path) 
                    #print "full_path: {0}".format(full_path)
                    self.test_files.append(full_path)
                
    def load_file(self, filepath):
        '''
        loads in one test file
        '''
        try:
            myfile = open(filepath, 'r')
            contents_yaml = yaml.load(myfile)
            #print "contents_yaml: {0}".format(contents_yaml)
            #if self.check_file_is_valid(contents_yaml):
            #    for k, v in contents_yaml.items():
            #        self.test_dict[k] = v
            for k, v in contents_yaml.items():
                self.test_dict[k] = v
        except:
            raise
        return

    def check_file_is_valid(self, test_dictionary):
        '''
        ensure file is valid
        '''
        is_valid = True
        if test_dictionary == None or len(test_dictionary.keys()) == 0:
            return False
        for k in test_dictionary.keys():
            is_ok = self.check_test_is_valid(test_dictionary[k])
            if not is_ok:
                is_valid = False
        return is_valid

    @staticmethod
    def check_test_is_valid(test):
        '''
        checks that all tests in a file are valid
        '''
        # check each test from file ensuring miniumum necessary params are met, no value check
        # must have module_and_function, assertion, expected-return
        is_valid = True
        reqs = ['module_and_function', 'assertion', 'expected-return']
        for k in test.keys():
            if k in reqs:
                reqs.remove(k)
        if reqs != None:
            is_valid = False
        return is_valid


    def get_test_as_dict(self):
        '''
        retrieve the tests as a dict
        '''
        file_dir_type = self.is_file_or_dir()
        self.load_test_suite(file_dir_type)
        return self.test_dict


def main(minion_list, client_type, test_dict, verbose):
    '''
    main entry point
    '''
    start_time = time.time()
    #print "minion_list: {}".format(minion_list)
    #print "client_type: {}".format(client_type)
    #print "test_dict: {}".format(test_dict)
    #print "verbosity: {}".format(verbose)
    print

    tester = Tester(client=client_type)
    tester.results_dict = {} # for holding results of all tests
    for key, val in test_dict.items():
        result = tester.run_one_test(minion_list, {key:val})
        test_name = result[0]
        k_v = result[1]
        #print "\nTest Name:  {0}".format(test_name)
        #print "Minion      Test-Result"
        for ley, wal in k_v.items():
            res = tester.results_dict.get(ley, None)
            if not res:
                tester.results_dict[ley] = {test_name : wal}
            else:
                res[test_name] = wal
                tester.results_dict[ley] = res
            #print "{0}         {1}".format(k, v)
    tester.summarize_results()
    if verbose == 'low':
        tester.print_results_verbose_low()
    else:
        tester.print_results_as_text()
    print
    end_time = time.time()
    total_time_sec = end_time - start_time
    print "Time to run tests: {} seconds".format(round(total_time_sec, 2))
