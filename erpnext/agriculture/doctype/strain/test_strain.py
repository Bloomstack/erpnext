# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
import unittest

test_dependencies = ["Additive"]


class TestStrain(unittest.TestCase):
	def test_strain_period(self):
		basil = frappe.get_doc('Strain', 'Basil')
		self.assertEqual(basil.period, 15)
