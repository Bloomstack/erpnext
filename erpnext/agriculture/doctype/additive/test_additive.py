# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

class TestAdditive(unittest.TestCase):
	def test_Additive_creation(self):
		self.assertEqual(frappe.db.exists('Additive', 'Urea'), 'Urea')