# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
from erpnext.hr.doctype.shift_type.test_shift_type import create_shift_type
from frappe.utils import nowdate

test_dependencies = ["Shift Type"]

class TestShiftAssignment(unittest.TestCase):

	def setUp(self):
		frappe.db.sql("delete from `tabShift Assignment`")

	def test_make_shift_assignment(self):
		shift = create_shift_type()
		shift_assignment = frappe.get_doc({
			"doctype": "Shift Assignment",
			"shift_type": shift,
			"company": "_Test Company",
			"employee": "_T-Employee-00001",
			"date": nowdate()
		}).insert()
		shift_assignment.submit()

		self.assertEqual(shift_assignment.docstatus, 1)
