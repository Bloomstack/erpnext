# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import unittest

import frappe

test_dependencies = ["Strain", "Additive", "Location", "Disease"]


class TestPlantBatch(unittest.TestCase):
	def test_plant_batch_creation(self):
		cycle = frappe.get_doc('Plant Batch', 'Basil from seed 2017')
		self.assertTrue(frappe.db.exists('Plant Batch', 'Basil from seed 2017'))
