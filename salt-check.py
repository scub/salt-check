#!/usr/bin/env python
'''This program allows for unit-test like testing of salt state logic
   Author: William Cannon  william period cannon at gmail dot com'''
import yaml
import salt.client
import salt.config
import argparse

class Tester(object):

    def __init__(self):
        self.salt_lc = salt.client.LocalClient()
    
    def load_test_plan(self, path):
        pass

    def run_one_test(self, minion_list, test_dict):
        #print "\n\ntest_dict contains: {}\n\n".format(test_dict)
        results_dict = {}
        test_name = test_dict.keys()[0]
        #test_name = test_dict.keys()
        #print "\n\ntest_name: {}".format(test_name)
        m_f = test_dict[test_name].get('module_and_function', None)
        #print "module_and_function: {}".format(m_f)
        t_args = test_dict[test_name].get('args', None)
        t_args = t_args.split()
        #t_args = [t_args]
        #print "args: {}".format(t_args)
        t_kwargs = test_dict[test_name].get('kwargs', None)
        #print "kwargs: {}".format(t_kwargs)
        pillar_data = test_dict[test_name].get('pillar_data', None)
        #print "pillar_data: {}".format(pillar_data)
        assertion = test_dict[test_name].get('assertion', None)
        #print "assertion: {}".format(assertion)
        expected_return = test_dict[test_name].get('expected-return', None)
        #print "expected_return: {}".format(expected_return)
        val = self.call_salt_command(tgt=minion_list,
                fun = m_f,
                arg = t_args,
                kwarg = t_kwargs,
                expr_form = 'list')
        for k,v in val.items():
            if assertion == "assertEqual":
                value = self.assertEqual(expected_return, v)
                results_dict[k] = value
            elif assertion == "assertNotEqual":
                value = self.assertNotEqual(expected_return, v)
                results_dict[k] = value
            elif assertion == "assertTrue":
                value = self.assertTrue(expected_return, v)
                results_dict[k] = value
            elif assertion == "assertFalse":
                value = self.assertFalse(expected_return, v)
                results_dict[k] = value
            else:
                value = "???"
        return (test_name, results_dict)


    def call_salt_command(self, tgt, fun, arg=(), timeout=None,
                          expr_form='compound', ret='', jid='',
                          kwarg=None, **kwargs):
        '''Generic call of salt command'''
        value = True
        try:
            value = self.salt_lc.cmd(tgt, fun, arg, timeout,
                                     expr_form, ret, jid, kwarg, **kwargs)
            #print "value = {}".format(value)
        except Exception, error:
            print error
            value = False
        return value

    def assertEqual(self, expected, returned):
        result = True
        try:
            assert (expected == returned),"Expected: {}, Returned: {}".format(expected, returned)
        except AssertionError as err:
            result = (False, err)
        return result

    def assertNotEqual(self, expected, returned):
        result = True
        try:
            assert (expected != returned),"Expected: {}, Returned: {}".format(expected, returned)
        except AssertionError:
            result = (False, err)
        return result

    def assertTrue(self, expected, returned):
        # may need to cast returned to string
        result = True
        try:
            assert (returned == True),"Expected: {}, Returned: {}".format(True, returned)
        except AssertionError:
            result = (False, err)
        return result

    def assertFalse(self, expected, returned):
        # may need to cast returned to string
        result = True
        try:
            assert (returned == False),"Expected: {}, Returned: {}".format(False, returned)
        except AssertionError:
            result = (False, err)
        return result


class TestLoader(object):

    def __init__(self, filename):
        self.filepath = filename
        self.contents_yaml = None

    def load_file(self):
        try:
            f = open(self.filepath, 'r')
            self.contents_yaml = yaml.load(f)
            #print "YAML as dict:  {}".format( self.contents_yaml)
        except:
            raise
        return

    def check_file_is_valid(self):
        is_valid = True
        for k in self.contents_yaml.keys():
            ok = self.check_test_is_valid(self.contents_yaml[k])
            if not ok:
                is_valid = False
        return is_valid
       
    def check_test_is_valid(self, test):
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
        try:
            self.load_file()
            self.check_file_is_valid()
        except:
            raise
        return self.contents_yaml


def main(minion_list, test_dict):
    t = Tester()
    for k,v in test_dict.items():
        result = t.run_one_test(minion_list, {k:v})
        test_name = result[0]
        k_v = result[1]
        print "\nTest Name:  {}".format(test_name)
        print "Minion      Test-Result"
        for k,v in k_v.items():
            print "{}         {}".format(k, v)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('-L', '--list', action="store", dest="L")
    parser.add_argument('testfile', action="store")
    args = parser.parse_args()
    print "list: {}".format(args.L)
    print "testfile: {}".format(args.testfile)

    t = TestLoader(args.testfile)
    mydict = t.get_test_as_dict() 
    #print "mydict contains: {}".format(mydict)
    minion_list_str = args.L
    minion_list = minion_list_str.split(",")
    print "minion_list: {}".format(minion_list)
    main(minion_list=minion_list, test_dict=mydict)
