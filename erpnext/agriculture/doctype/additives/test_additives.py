# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

class TestAdditives(unittest.TestCase):
	def test_Additives_creation(self):
		self.assertEqual(frappe.db.exists('Additives', 'Urea'), 'Urea')