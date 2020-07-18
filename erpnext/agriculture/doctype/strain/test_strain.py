# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

test_dependencies = ["Fertilizer"]

class TestStrain(unittest.TestCase):
	def test_strain_period(self):
		basil = frappe.get_doc('Strain', 'Basil from seed')
		self.assertEqual(basil.period, 15)