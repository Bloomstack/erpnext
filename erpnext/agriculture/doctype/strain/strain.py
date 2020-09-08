# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint


class Strain(Document):
	def validate(self):
		self.validate_strain_tasks()

	def validate_strain_tasks(self):
		for task in self.cultivation_task:
			if task.start_day > task.end_day:
				frappe.throw(_("Start day is greater than end day in task '{0}'").format(task.task_name))

		# Verify that the strain period is correct
		max_strain_period = max([task.end_day for task in self.cultivation_task], default=0)
		self.period = max(cint(self.period), max_strain_period)

		# Sort the strain tasks based on start days,
		# maintaining the order for same-day tasks
		self.cultivation_task.sort(key=lambda task: task.start_day)


@frappe.whitelist()
def get_item_details(item_code):
	item = frappe.get_doc('Item', item_code)
	return {"uom": item.stock_uom, "rate": item.valuation_rate}


@frappe.whitelist()
def make_plant_batch(source_name, target_doc=None):
	target_doc = get_mapped_doc("Strain", source_name,
		{"Strain": {
			"doctype": "Plant Batch",
			"field_map": {
				"default_location": "location"
			}
		}}, target_doc)

	return target_doc
