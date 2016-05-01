#!/usr/bin/env python
import yaml
import unittest
from salt_check import Tester
#sys.path.append(os.path.abspath(sys.path[0]) + '/../')

# Note: the order tests are run is arbitrary!

class MyClass(unittest.TestCase):

    def setUp(self):
        mt = Tester()

    def tearDown(self):
        pass

    def test_1_assert_equal(self):
        val = Tester.assert_equal(True, True)
        self.assertEqual(True, val)

    def test_2_assert_equal(self):
        val = Tester.assert_equal(True, False)
        fin_val = val[0]
        self.assertEqual(False, fin_val)

    def test_3_assert_equal(self):
        val = Tester.assert_equal(False, False)
        self.assertEqual(True, val)

if __name__ == '__main__':
    unittest.main()
