#!/usr/bin/env python

import salt.client
import salt.config

class Tester(object):

    def __init__(self):
        self.salt_lc = salt.client.LocalClient()
    
    def load_test_plan(self, path):
        pass

    def run_one_test(self, test_dict):
        test_name = test_dict.keys()[0]
        print "test_name: {}".format(test_name)
        m_f = test_dict[test_name].get('module_and_function', None)
        print "module_and_function: {}".format(m_f)
        t_args = test_dict[test_name].get('args', None)
        t_args = [t_args]
        print "args: {}".format(t_args)
        t_kwargs = test_dict[test_name].get('kwargs', None)
        print "kwargs: {}".format(t_kwargs)
        pillar_data = test_dict[test_name].get('pillar_data', None)
        print "pillar_data: {}".format(pillar_data)
        assertion = test_dict[test_name].get('assertion', None)
        print "assertion: {}".format(assertion)
        expected_return = test_dict[test_name].get('expected-return', None)
        print "expected_return: {}".format(expected_return)
        val = self.call_salt_command(tgt='*',
                fun = m_f,
                arg = t_args,
                kwarg = t_kwargs)
        return val


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

    def run_test_plan(self):
        for p in plan.keys():
            self.run_one_test(test)

    def print_results(self):
        pass


def main(test_dict):
    t = Tester()
    result = t.run_one_test(test_dict)
    for k,v in result.items():
        print k, v

if __name__ == "__main__":
    test_dict = {'example-test':
                     {'module_and_function': 'cmd.run',
                     'args': 'uptime',
                     'kwargs':'',
                     'pillar-data':'', 
                     'assertion': 'assertNotEqual',
                     'expected-return':  '12345'}
                }
    main(test_dict)
