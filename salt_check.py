#!/usr/bin/env python
'''This program allows for unit-test like testing of salt state logic
   Author: William Cannon  william period cannon at gmail dot com'''
import argparse
import json
import salt.client
import salt.config
import yaml

class Tester(object):
    '''
    This class implements the salt_check
    '''

    def __init__(self):
        self.salt_lc = salt.client.LocalClient()
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
        if not isinstance(t_args, list):
            t_args = t_args.split()
        t_kwargs = test_dict[test_name].get('kwargs', None)
        #pillar_data = test_dict[test_name].get('pillar-data', None)
        assertion = test_dict[test_name].get('assertion', None)
        expected_return = test_dict[test_name].get('expected-return', None)
        values = self.call_salt_command(tgt=minion_list,
                                        fun=m_f,
                                        arg=t_args,
                                        kwarg=t_kwargs,
                                        expr_form='list')
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
            else:
                value = "???"
        return [test_name, results_dict]


    def call_salt_command(self,
                          tgt,
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
            value = self.salt_lc.cmd(tgt, fun, arg, timeout,
                                     expr_form, ret, jid, kwarg, **kwargs)
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
            for ley, wal in self.results_dict[key].items(): # print test and result
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
            for ley, wal in self.results_dict[key].items(): # print test and result
                if wal != True:
                    print "Test: {0}".format(ley).ljust(40),
                    print "Result: False --> {0}".format(wal[1]).ljust(40)

    # broken
    def print_results_as_yaml(self):
        '''
        print results dict as yaml
        '''
        myyaml = yaml.dump(self.results_dict)
        print myyaml

    # broken - have to get rid of tuples in AssertionError output?
    def print_results_as_json(self):
        '''
        print results dict as json
        '''
        myjson = json.dumps(self.results_dict)
        print myjson


class TestLoader(object):
    '''
    Class loads in test files
    '''

    def __init__(self, filename):
        self.filepath = filename
        self.contents_yaml = None

    def load_file(self):
        '''
        loads in one test file
        '''
        try:
            myfile = open(self.filepath, 'r')
            self.contents_yaml = yaml.load(myfile)
            #print "YAML as dict:  {0}".format( self.contents_yaml)
        except:
            raise
        return

    def check_file_is_valid(self):
        '''
        ensure file is valid
        '''
        is_valid = True
        for k in self.contents_yaml.keys():
            is_ok = self.check_test_is_valid(self.contents_yaml[k])
            if not is_ok:
                is_valid = False
        return is_valid

    @staticmethod
    def check_test_is_valid(test):
        '''
        checks that a test is valid
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
        retrieve a test as a dict
        '''
        try:
            self.load_file()
            self.check_file_is_valid()
        except:
            raise
        return self.contents_yaml


def main(minion_list, test_dict, verbose):
    '''
    main entry point
    '''
    tester = Tester()
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


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(add_help=True)
    PARSER.add_argument('-L', '--list', action="store", dest="L")
    PARSER.add_argument('testfile', action="store")
    PARSER.add_argument('-v', '--verbose', action="store", dest="verbose", default='low')
    ARGS = PARSER.parse_args()
    #print "list: {0}".format(args.L)
    #print "verbose: {0}".format(args.verbose)
    #print "testfile: {0}".format(args.testfile)

    TESTER = TestLoader(ARGS.testfile)
    MYDICT = TESTER.get_test_as_dict()
    #print "mydict contains: {0}".format(MYDICT)
    MINION_LIST_STR = ARGS.L
    MY_MINION_LIST = MINION_LIST_STR.split(",")
    #print "minion_list: {0}".format(minion_list)
    main(minion_list=MY_MINION_LIST, test_dict=MYDICT, verbose=ARGS.verbose)
