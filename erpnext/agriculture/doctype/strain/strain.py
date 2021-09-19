# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint, cstr
from erpnext.compliance.utils import make_integration_request, get_bloomtrace_client


class Strain(Document):
	def validate(self):
		self.validate_strain_tasks()

	def on_update(self):
		self.create_integration_request()

	def create_integration_request(self):
		make_integration_request(self.doctype, self.name, "Strain")

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

def execute_bloomtrace_integration_request():
	frappe_client = get_bloomtrace_client()
	if not frappe_client:
		return

	pending_requests = frappe.get_all("Integration Request",
		filters={"status": ["IN", ["Queued", "Failed"]], "reference_doctype": "Strain", "integration_request_service": "BloomTrace"},
		order_by="creation ASC",
		limit=50)

	for request in pending_requests:
		integration_request = frappe.get_doc("Integration Request", request.name)
		strain = frappe.get_doc("Strain", integration_request.reference_docname)
		bloomtrace_strain = frappe_client.get_doc("Strain", integration_request.reference_docname)
		try:
			if not bloomtrace_strain:
				insert_strain(strain, frappe_client)
			else:
				update_strain(strain, frappe_client)
			integration_request.error = ""
			integration_request.status = "Completed"
			integration_request.save(ignore_permissions=True)
		except Exception as e:
			integration_request.error = cstr(frappe.get_traceback())
			integration_request.status = "Failed"
			integration_request.save(ignore_permissions=True)

def insert_strain(strain, frappe_client):
	bloomtrace_strain = make_strain(strain)
	frappe_client.insert(bloomtrace_strain)

def update_strain(strain, frappe_client):
	bloomtrace_strain = make_strain(strain)
	bloomtrace_strain.update({
		"name": strain.name
	})
	frappe_client.update(bloomtrace_strain)

def make_strain(strain):
	bloomtrace_strain_dict = {
		"doctype": "Strain",
		"bloomstack_company": strain.company,
		"strain": strain.strain_name,
		"indica_percentage": strain.indica_percentage,
		"sativa_percentage": strain.sativa_percentage
	}
	return bloomtrace_strain_dict
