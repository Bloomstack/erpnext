import frappe
import unittest
from unittest.mock import Mock

from erpnext.utilities.utils import retry

class TestUtils(unittest.TestCase):
	def test_retry_success_first_call(self):
		mockFn = Mock(return_value=True)

		retry(lambda i: mockFn())

		mockFn.assert_called_once()

	def test_retry_fail_via_result_predicate(self):
		mockFn = Mock()

		retry(lambda i: mockFn(), 3, lambda r,i: False)

		self.assertTrue(mockFn.call_count == 3, "Retry 3 times")

	def test_retry_exception(self):
		mockFn = Mock(side_effect=Exception("Unknown Error"))

		retry(lambda i: mockFn(), 3)

		self.assertTrue(mockFn.call_count == 3, "Retries: {} != {}".format(mockFn.call_count, 3))

	def test_retry_exception_with_predicate(self):
		mockFn = Mock(side_effect=Exception("Unknown Error"))
		exceptionFn = Mock(return_value=False)

		retry(lambda i: mockFn(), 3, None, lambda ex,i: exceptionFn())

		self.assertTrue(mockFn.call_count == 3, "Retries: {} != {}".format(mockFn.call_count, 3))
		self.assertTrue(exceptionFn.call_count == 3, "Exception Runs: {} != {}".format(exceptionFn.call_count, 3))

	def test_retry_limit_via_result_predicate(self):
		mockFn = Mock()

		retry(mockFn, 3, lambda r,i: i==1)

		self.assertTrue(mockFn.call_count == 2, "Retries: {} != {}".format(mockFn.call_count, 2))

	def test_retry_limit_via_exception_predicate(self):
		mockFn = Mock(side_effect=Exception("Unknown Error"))

		retry(mockFn, 3, None, lambda ex, i: i==1)

		self.assertTrue(mockFn.call_count == 2, "Retries: {} != {}".format(mockFn.call_count, 2))

	def test_retry_result_value(self):
		mockFn = Mock(return_value=100)

		result = retry(mockFn)

		mockFn.assert_called_once()
		self.assertTrue(result == 100, "{} != 100".format(result))

	def test_retry_on_result_value(self):
		mockFn = Mock(return_value=100)

		result = retry(mockFn, on_result=lambda ex,i: 200)

		mockFn.assert_called_once()
		self.assertTrue(result == 200, "{} != 200".format(result))

	def test_retry_on_exception_value(self):
		mockFn = Mock(side_effect=Exception("Unknown Error"))

		result = retry(mockFn, on_exception=lambda ex,i: 200)

		mockFn.assert_called_once()
		self.assertTrue(result == 200, "{} != 200".format(result))

	def test_retry_on_exception_fail_value(self):
		mockFn = Mock(side_effect=Exception("Unknown Error"))

		result = retry(mockFn, on_exception=lambda ex,i: ex)

		mockFn.assert_called_once()
		self.assertTrue(isinstance(result, Exception), "Did not return expected exception")

