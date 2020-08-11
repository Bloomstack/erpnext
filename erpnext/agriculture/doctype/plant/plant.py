# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class Plant(Document):
	def before_insert(self):
		if not self.title:
			self.title = self.strain + " - " + self.plant_tag

@frappe.whitelist()
def make_harvest(source_name, target_doc=None):
	target_doc = get_mapped_doc("Plant", source_name,
		{"Plant": {
			"doctype": "Harvest",
			"field_map": {
				"harvest_location": "location"
			}
		}}, target_doc)

	return target_doc

@frappe.whitelist()
def make_additive_log(source_name, target_doc=None):
	target_doc = get_mapped_doc("Plant", source_name,
		{"Plant": {
			"doctype": "Plant Additive Log",
			"field_map": {
			}
		}}, target_doc)

	return target_doc

@frappe.whitelist()
def make_disease_diagnosis(source_name, target_doc=None):
	target_doc = get_mapped_doc("Plant", source_name,
		{"Plant": {
			"doctype": "Plant Disease Diagnosis",
			"field_map": {
			}
		}}, target_doc)

	return target_doc