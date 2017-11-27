# -*- coding: utf-8 -*-
'''
A module for testing the logic of states and highstates

Saltcheck provides unittest like functionality requiring only the knowledge of salt module execution and yaml.

In order to run state and highstate saltcheck tests a sub-folder of a state must be creaed and named "saltcheck-tests".

Tests for a state should be created in files ending in *.tst and placed in the saltcheck-tests folder.

Multiple tests can be created in a file.
Multiple *.tst files can be created in the saltcheck-tests folder.
Salt rendering is supported in test files e.g. yaml + jinja.
The "id" of a test works in the same manner as in salt state files.
They should be unique and descriptive.

Example file system layout:
/srv/salt/apache/
                 init.sls
                 config.sls
                 saltcheck-tests/
                                 pkg_and_mods.tst
                                 config.tst


Saltcheck Test Syntax:

Unique-ID:
  module_and_function:
  args:
  kwargs:
  assertion:
  expected-return:


Example test 1:

echo-test-hello:
  module_and_function: test.echo
  args:
    - "hello"
  kwargs:
  assertion: assertEqual
  expected-return:  'hello'


:codeauthor:    William Cannon <william.cannon@gmail.com>
:maturity:      new
'''
from __future__ import absolute_import
import logging
import os
import time
from json import loads, dumps
import yaml
try:
    import salt.utils
    import salt.client
    import salt.exceptions
except ImportError:
    pass

log = logging.getLogger(__name__)

__virtualname__ = 'saltcheck'


def __virtual__():
    '''
    Check dependencies - may be useful in future
    '''
    return __virtualname__


def update_master_cache():
    '''
    Updates the master cache onto the minion - transfers all salt-check-tests
    Should be done one time before running tests, and if tests are updated
    Can be automated by setting "auto_update_master_cache: True" in minion config

    CLI Example:
        salt '*' saltcheck.update_master_cache
    '''
    __salt__['cp.cache_master']()
    return True


def run_test(**kwargs):
    '''
    Execute one saltcheck test and return result

    :param keyword arg test:
    CLI Example::
        salt '*' saltcheck.run_test
            test='{"module_and_function": "test.echo",
                   "assertion": "assertEqual",
                   "expected-return": "This works!",
                   "args":["This works!"] }'
    '''
    # salt converts the string to a dictionary auto-magically
    scheck = SaltCheck()
    test = kwargs.get('test', None)
    if test and isinstance(test, dict):
        return scheck.run_test(test)
    else:
        return "Test must be a dictionary"


def run_state_tests(state):
    '''
    Execute all tests for a salt state and return results
    Nested states will also be tested

    :param str state: the name of a user defined state

    CLI Example::
      salt '*' saltcheck.run_state_tests postfix
    '''
    scheck = SaltCheck()
    paths = scheck.get_state_search_path_list()
    stl = StateTestLoader(search_paths=paths)
    results = {}
    sls_list = _get_state_sls(state)
    for state_name in sls_list:
        mypath = stl.convert_sls_to_path(state_name)
        stl.add_test_files_for_sls(mypath)
        stl.load_test_suite()
        results_dict = {}
        for key, value in stl.test_dict.items():
            result = scheck.run_test(value)
            results_dict[key] = result
        results[state_name] = results_dict
    passed = 0
    failed = 0
    missing_tests = 0
    for state in results:
        if len(results[state].items()) == 0:
            missing_tests = missing_tests + 1
        else:
            for dummy, val in results[state].items():
                log.info("dummy={}, val={}".format(dummy, val))
                if val.startswith('Pass'):
                    passed = passed + 1
                if val.startswith('Fail'):
                    failed = failed + 1
    out_list = []
    for key, value in results.items():
        out_list.append({key: value})
    out_list.sort()
    out_list.append({"TEST RESULTS": {'Passed': passed, 'Failed': failed, 'Missing Tests': missing_tests}})
    return out_list


def run_highstate_tests():
    '''
    Execute all tests for a salt highstate and return results

    CLI Example::
      salt '*' saltcheck.run_highstate_tests
    '''
    scheck = SaltCheck()
    paths = scheck.get_state_search_path_list()
    stl = StateTestLoader(search_paths=paths)
    results = {}
    sls_list = _get_top_states()
    all_states = []
    for top_state in sls_list:
        sls_list = _get_state_sls(top_state)
        for state in sls_list:
            if state not in all_states:
                all_states.append(state)

    for state_name in all_states:
        mypath = stl.convert_sls_to_path(state_name)
        stl.add_test_files_for_sls(mypath)
        stl.load_test_suite()
        results_dict = {}
        for key, value in stl.test_dict.items():
            result = scheck.run_test(value)
            results_dict[key] = result
        results[state_name] = results_dict
    passed = 0
    failed = 0
    missing_tests = 0
    for state in results:
        if len(results[state].items()) == 0:
            missing_tests = missing_tests + 1
        else:
            for dummy, val in results[state].items():
                log.info("dummy={}, val={}".format(dummy, val))
                if val.startswith('Pass'):
                    passed = passed + 1
                if val.startswith('Fail'):
                    failed = failed + 1
    out_list = []
    for key, value in results.items():
        out_list.append({key: value})
    out_list.sort()
    out_list.append({"TEST RESULTS": {'Passed': passed, 'Failed': failed, 'Missing Tests': missing_tests}})
    return out_list


def show_tests(state=None):
    '''
    Show all tests that will be executed in a state tree.
    If a state is provided, only tests for that state will
    be shown otherwise all tests are returned.

    :param str state: the name of a user defined state

    CLI Example::
      salt '*' saltcheck.show_tests
      salt '*' saltcheck.show_tests apache
    '''
    scheck = SaltCheck()
    results = {"Tests":dict()}

    # Generate StateTestLoaders for the provided state(s)
    for (stl, test_files) in _gen_StateTestLoader(scheck, state):
        results["Tests"].update(test_files)

    # Tag missing tests (unnecessary to present?)
    for state in _get_states(state):
        # If we don't have any tests for this state stamp
        # it with '[NO TESTS FOUND]' and move along.
        if (state not in results["Tests"].keys()) or \
            not len(results["Tests"][state]):
            results["Tests"][state] = ['[NO TESTS FOUND]']

    return results


def _gen_StateTestLoader(scheck,state=None):
    '''
    Generator creates StateTestLoader objects for a state
    tree once per iteration. If no state is provided
    StateTestLoaders are generated for the entire top state.

    :param SaltCheck scheck: single instance of a SaltCheck object
    :param str,list state: a list or single state to generate test loaders for.
    '''
    # Gather our search paths for our test loader
    paths      = scheck.get_state_search_path_list()
    # Normalize the list of states to generate loaders for
    all_states = _get_states(state)

    for state in all_states:
        # Catalog relative paths for test files
        test_relative_paths = { state : list() }
        # Initialize our StateTestLoader
        stl = StateTestLoader(search_paths=paths)
        # Convert the sls name to its path in the minion cache
        mypath = stl.convert_sls_to_path(state)
        # Gather all .tst files into "stl.test_files"
        stl.add_test_files_for_sls(mypath)

        # Iterate over gathered tst files
        for test_path in stl.test_files:
            # Strip the minion cache from the test's path
            test = test_path.split(os.sep+mypath+os.sep)[1]
            # Append the relative path of the test to our catalog
            test_relative_paths[state].append(test)

        # Soft-return our loader and list of tests
        yield (stl, test_relative_paths)

    # Return from our generator
    return


def _get_states(state=None):
    '''
    Generate and return a list of uniq __sls__ names
    from a given state or, if no state is provided, the
    entire state tree.

    :param str,list state: a list or single state to render into __sls__'s.
    '''
    # Normalize list of state(s) based on the
    # type of the state parameter.
    if state is None:
        sls_list = _get_top_states()
    elif isinstance(state, list):
        sls_list = state
    else:
        sls_list = [state,]

    # Seed nothing and use show_low_sls
    all_states = []

    # This behavior causes us to skip-over
    # some state layouts. Possibly intentionally.
    for top_state in sls_list:
        for state in _get_state_sls(top_state):
            if state not in all_states:
                all_states.append(state)

    return all_states


def _render_file(file_path):
    '''call the salt utility to render a file'''
    # salt-call slsutil.renderer /srv/salt/jinjatest/saltcheck-tests/test1.tst
    rendered = __salt__['slsutil.renderer'](file_path)
    log.info("rendered: {}".format(rendered))
    return rendered


def _is_valid_module(module):
    '''return a list of all modules available on minion'''
    modules = __salt__['sys.list_modules']()
    return bool(module in modules)


def _get_auto_update_cache_value():
    '''return the config value of auto_update_master_cache'''
    __salt__['config.get']('auto_update_master_cache')
    return True


def _is_valid_function(module_name, function):
    '''Determine if a function is valid for a module'''
    try:
        functions = __salt__['sys.list_functions'](module_name)
    except salt.exceptions.SaltException:
        functions = ["unable to look up functions"]
    return "{0}.{1}".format(module_name, function) in functions


def _get_top_states():
    ''' equivalent to a salt cli: salt web state.show_top'''
    alt_states = []
    try:
        returned = __salt__['state.show_top']()
        for i in returned['base']:
            alt_states.append(i)
    except Exception:
        raise
    # log.info("top states: {}".format(alt_states))
    return alt_states


def _get_state_sls(state):
    ''' equivalent to a salt cli: salt web state.show_low_sls STATE'''
    sls_list_state = []
    try:
        returned = __salt__['state.show_low_sls'](state)
        for i in returned:
            if i['__sls__'] not in sls_list_state:
                sls_list_state.append(i['__sls__'])
    except Exception:
        # raise
        pass
    return sls_list_state

def _refresh_saltcheck_tests_dir(dirpath):
    ''' equivalent to:
           rm -rf dest-dir
           salt cp.get_dir salt://STATE/saltcheck-tests dest-dir'''
    __salt__['file.remove'](dirpath)

    mypath_list = dirpath.split(os.sep)
    mypath_list = [i for i in mypath_list if i != '']  # removing empty chars

    state = mypath_list[6:]
    state = os.path.join(*state)

    source = "salt://" + state
    dest = os.sep + os.path.join(*mypath_list[:-1])
    __salt__['cp.get_dir'](source, dest)
    return


class SaltCheck(object):
    '''
    This class implements the saltcheck
    '''

    def __init__(self):
        # self.sls_list_top = []
        self.sls_list_state = []
        self.modules = []
        self.results_dict = {}
        self.results_dict_summary = {}
        self.assertions_list = '''assertEqual assertNotEqual
                                  assertTrue assertFalse
                                  assertIn assertNotIn
                                  assertGreater
                                  assertGreaterEqual
                                  assertLess assertLessEqual
                                  assertEmpty assertNotEmpty'''.split()
        self.auto_update_master_cache = _get_auto_update_cache_value
        # self.salt_lc = salt.client.Caller(mopts=__opts__)
        self.salt_lc = salt.client.Caller()
        if self.auto_update_master_cache:
            update_master_cache()

    def __is_valid_test(self, test_dict):
        '''Determine if a test contains:
             a test name,
             a valid module and function,
             a valid assertion,
             an expected return value - if assertion type requires it'''
        # 6 points needed for standard test
        # 4 points needed for test with assertion not requiring expected return
        tots = 0  
        m_and_f = test_dict.get('module_and_function', None)
        assertion = test_dict.get('assertion', None)
        exp_ret_key = 'expected-return' in test_dict.keys()
        exp_ret_val = test_dict.get('expected-return', None)
        log.info("__is_valid_test has test: {}".format(test_dict))
        if assertion in ["assertEmpty",
                         "assertNotEmpty",
                         "assertTrue",
                         "assertFalse"]:
            required_total = 4
        else:
            required_total = 6
 
        if m_and_f:
            tots += 1
            module, function = m_and_f.split('.')
            if _is_valid_module(module):
                tots += 1
            if _is_valid_function(module, function):
                tots += 1
            log.info("__is_valid_test has valid m_and_f")
        if assertion in self.assertions_list:
            log.info("__is_valid_test has valid_assertion")
            tots += 1

        if exp_ret_key:
            tots += 1
            
        if exp_ret_val != None:
                tots += 1

        # log the test score for debug purposes
        log.info("__test score: {}".format(tots))
        return tots >= required_total

    def call_salt_command(self,
                          fun,
                          args,
                          kwargs):
        '''Generic call of salt Caller command'''
        value = False
        try:
            if args and kwargs:
                value = self.salt_lc.cmd(fun, *args, **kwargs)
            elif args and not kwargs:
                value = self.salt_lc.cmd(fun, *args)
            elif not args and kwargs:
                value = self.salt_lc.cmd(fun, **kwargs)
            else:
                value = self.salt_lc.cmd(fun)
        except salt.exceptions.SaltException:
            raise
        except Exception:
            raise
        return value

    def run_test(self, test_dict):
        '''Run a single saltcheck test'''
        if self.__is_valid_test(test_dict):
            mod_and_func = test_dict['module_and_function']
            args = test_dict.get('args', None)
            kwargs = test_dict.get('kwargs', None)
            assertion = test_dict['assertion']
            expected_return = test_dict.get('expected-return', None)
            actual_return = self.call_salt_command(mod_and_func, args, kwargs)
            if assertion not in ["assertIn", "assertNotIn", "assertEmpty", "assertNotEmpty",
                                 "assertTrue", "assertFalse"]:
                expected_return = self.cast_expected_to_returned_type(expected_return, actual_return)
            if assertion == "assertEqual":
                value = self.__assert_equal(expected_return, actual_return)
            elif assertion == "assertNotEqual":
                value = self.__assert_not_equal(expected_return, actual_return)
            elif assertion == "assertTrue":
                value = self.__assert_true(actual_return)
            elif assertion == "assertFalse":
                value = self.__assert_false(actual_return)
            elif assertion == "assertIn":
                value = self.__assert_in(expected_return, actual_return)
            elif assertion == "assertNotIn":
                value = self.__assert_not_in(expected_return, actual_return)
            elif assertion == "assertGreater":
                value = self.__assert_greater(expected_return, actual_return)
            elif assertion == "assertGreaterEqual":
                value = self.__assert_greater_equal(expected_return, actual_return)
            elif assertion == "assertLess":
                value = self.__assert_less(expected_return, actual_return)
            elif assertion == "assertLessEqual":
                value = self.__assert_less_equal(expected_return, actual_return)
            elif assertion == "assertEmpty":
                value = self.__assert_empty(actual_return)
            elif assertion == "assertNotEmpty":
                value = self.__assert_not_empty(actual_return)
            else:
                value = "Fail - bas assertion"
        else:
            return "Fail - invalid test"
        return value

    @staticmethod
    def cast_expected_to_returned_type(expected, returned):
        '''
        Determine the type of variable returned
        Cast the expected to the type of variable returned
        '''
        ret_type = type(returned)
        new_expected = expected
        if expected == "False" and ret_type == bool:
            expected = False
        try:
            new_expected = ret_type(expected)
        except ValueError:
            log.info("Unable to cast expected into type of returned")
            log.info("returned = {}".format(returned))
            log.info("type of returned = {}".format(type(returned)))
            log.info("expected = {}".format(expected))
            log.info("type of expected = {}".format(type(expected)))
        return new_expected

    @staticmethod
    def __assert_equal(expected, returned):
        '''
        Test if two objects are equal
        '''
        result = "Pass"

        try:
            assert (expected == returned), "{0} is not equal to {1}".format(expected, returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_not_equal(expected, returned):
        '''
        Test if two objects are not equal
        '''
        result = "Pass"
        try:
            assert (expected != returned), "{0} is equal to {1}".format(expected, returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_true(returned):
        '''
        Test if an boolean is True
        '''
        result = "Pass"
        try:
            assert (returned is True), "{0} not True".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_false(returned):
        '''
        Test if an boolean is False
        '''
        result = "Pass"
        if isinstance(returned, str):
            try:
                returned = bool(returned)
            except ValueError:
                raise
        try:
            assert (returned is False), "{0} not False".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_in(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = "Pass"
        try:
            assert (expected in returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_not_in(expected, returned):
        '''
        Test if a value is not in the list of returned values
        '''
        result = "Pass"
        try:
            assert (expected not in returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_greater(expected, returned):
        '''
        Test if a value is greater than the returned value
        '''
        result = "Pass"
        try:
            assert (expected > returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_greater_equal(expected, returned):
        '''
        Test if a value is greater than or equal to the returned value
        '''
        result = "Pass"
        try:
            assert (expected >= returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_less(expected, returned):
        '''
        Test if a value is less than the returned value
        '''
        result = "Pass"
        try:
            assert (expected < returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_less_equal(expected, returned):
        '''
        Test if a value is less than or equal to the returned value
        '''
        result = "Pass"
        try:
            assert (expected <= returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_empty(returned):
        '''
        Test if a returned value is empty
        '''
        result = "Pass"
        try:
            assert (not returned), "{0} is not empty".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result

    @staticmethod
    def __assert_not_empty(returned):
        '''
        Test if a returned value is not empty
        '''
        result = "Pass"
        try:
            assert (returned), "{0} is empty".format(returned)
        except AssertionError as err:
            result = "Fail: " + str(err)
        return result


    @staticmethod
    def get_state_search_path_list():
        '''For the state file system, return a
           list of paths to search for states'''
        # state cache should be updated before running this method
        search_list = []
        cachedir = __opts__.get('cachedir', None)
        environment = __opts__['environment']
        if environment:
            path = cachedir + os.sep + "files" + os.sep + environment
            search_list.append(path)
        path = cachedir + os.sep + "files" + os.sep + "base"
        search_list.append(path)
        return search_list


class StateTestLoader(object):
    '''
    Class loads in test files for a state
    e.g.  state_dir/saltcheck-tests/[1.tst, 2.tst, 3.tst]
    '''

    def __init__(self, search_paths):
        self.search_paths = search_paths
        self.path_type = None
        self.test_files = []  # list of file paths
        self.test_dict = {}

    def load_test_suite(self):
        '''load tests either from one file, or a set of files'''
        self.test_dict = {}
        for myfile in self.test_files:
            # self.load_file(myfile)
            self.load_file_salt_rendered(myfile)
        self.test_files = []

    def load_file(self, filepath):
        '''
        loads in one test file
        '''
        try:
            with __utils__['files.fopen'](filepath, 'r') as myfile:
                # with salt.utils.files.fopen(filepath, 'r') as myfile:
                # with open(filepath, 'r') as myfile:
                contents_yaml = yaml.load(myfile)
                for key, value in contents_yaml.items():
                    self.test_dict[key] = value
        except:
            raise
        return

    def load_file_salt_rendered(self, filepath):
        '''
        loads in one test file
        '''
        # use the salt renderer module to interpret jinja and etc
        tests = _render_file(filepath)
        # use json as a convenient way to convert the OrderedDicts from salt renderer
        mydict = loads(dumps(tests))
        for key, value in mydict.items():
            self.test_dict[key] = value
        return

    def gather_files(self, filepath):
        '''gather files for a test suite'''
        self.test_files = []
        log.info("gather_files: {}".format(time.time()))
        filepath = filepath + os.sep + 'saltcheck-tests'

        # clear out, and repopulate the saltcheck-tests for a state
        _refresh_saltcheck_tests_dir(filepath)

        rootdir = filepath
        # for dirname, subdirlist, filelist in os.walk(rootdir):
        for dirname, dummy, filelist in os.walk(rootdir):
            for fname in filelist:
                if fname.endswith('.tst'):
                    start_path = dirname + os.sep + fname
                    full_path = os.path.abspath(start_path)
                    self.test_files.append(full_path)
        return

    @staticmethod
    def convert_sls_to_paths(sls_list):
        '''Converting sls to paths'''
        new_sls_list = []
        for sls in sls_list:
            sls = sls.replace(".", os.sep)
            new_sls_list.append(sls)
        return new_sls_list

    @staticmethod
    def convert_sls_to_path(sls):
        '''Converting sls to paths'''
        sls = sls.replace(".", os.sep)
        return sls

    def add_test_files_for_sls(self, sls_path):
        '''Adding test files'''
        for path in self.search_paths:
            full_path = path + os.sep + sls_path
            rootdir = full_path
            if os.path.isdir(full_path):
                log.info("searching path= {}".format(full_path))
                # for dirname, subdirlist, filelist in os.walk(rootdir, topdown=True):
                for dirname, subdirlist, dummy in os.walk(rootdir, topdown=True):
                    if "saltcheck-tests" in subdirlist:
                        self.gather_files(dirname)
                        log.info("test_files list: {}".format(self.test_files))
                        log.info("found subdir match in = {}".format(dirname))
                    else:
                        log.info("did not find subdir match in = {}".format(dirname))
                    del subdirlist[:]
            else:
                log.info("path is not a directory= {}".format(full_path))
        return
