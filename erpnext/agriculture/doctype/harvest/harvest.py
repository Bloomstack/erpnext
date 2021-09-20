# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.compliance.utils import make_integration_request, get_bloomtrace_client

class Harvest(Document):
	def on_submit(self):
		self.create_integration_request()

	def on_update_after_submit(self):
		self.create_integration_request()

	def create_integration_request(self):
		make_integration_request(self.doctype, self.name, "Harvest")

@frappe.whitelist()
def create_stock_entry(harvest):
	harvest = frappe.get_doc("Harvest", harvest)
	if stock_entry_exists(harvest.get('name')):
		stock_entry_name = frappe.db.get_value("Stock Entry", {"harvest": harvest.get('name')}, fieldname = ['name'])
		return frappe.msgprint(_('Stock Entry {0} has been already created against this harvest.').format(frappe.utils.get_link_to_form("Stock Entry", stock_entry_name)))
	stock_entry = frappe.new_doc('Stock Entry')
	stock_entry.harvest = harvest.get('name')
	stock_entry.stock_entry_type = 'Harvest'

	if harvest.get('plants'):
		stock_entry = update_stock_entry_based_on_strain(harvest, stock_entry)

	if stock_entry.get("items"):
		stock_entry.set_incoming_rate()
		stock_entry.set_actual_qty()
		stock_entry.calculate_rate_and_amount(update_finished_item_rate=False)

	return stock_entry.as_dict()


def stock_entry_exists(harvest_name):
	return frappe.db.exists('Stock Entry', {
		'harvest': harvest_name
	})


def update_stock_entry_based_on_strain(harvest, stock_entry):
	for plant_item in harvest.get('plants'):
		strain = frappe.get_doc("Strain", plant_item.strain)

		for strain_item in strain.produced_items + strain.byproducts:
			item = frappe._dict()
			item.item_code = strain_item.item_code
			item.uom = frappe.db.get_value("Item", item.item_code, "stock_uom")
			item.stock_uom = item.uom
			item.t_warehouse = strain.target_warehouse
			stock_entry.append('items', item)

	return stock_entry

def execute_bloomtrace_integration_request():
	frappe_client = get_bloomtrace_client()
	if not frappe_client:
		return

	pending_requests = frappe.get_all("Integration Request",
		filters={"status": ["IN", ["Queued", "Failed"]], "reference_doctype": "Harvest", "integration_request_service": "BloomTrace"},
		order_by="creation ASC",
		limit=50)

	for request in pending_requests:
		integration_request = frappe.get_doc("Integration Request", request.name)
		harvest = frappe.get_doc("Harvest", integration_request.reference_docname)
		bloomtrace_harvest = frappe_client.get_doc("Harvest", filters={"harvest" : integration_request.reference_docname})
		try:
			if not bloomtrace_harvest:
				insert_harvest(harvest, frappe_client)
			else:
				update_harvest(harvest, frappe_client)
			integration_request.error = ""
			integration_request.status = "Completed"
			integration_request.save(ignore_permissions=True)
		except Exception as e:
			integration_request.error = cstr(frappe.get_traceback())
			integration_request.status = "Failed"
			integration_request.save(ignore_permissions=True)

def insert_harvest(harvest, frappe_client):
	bloomtrace_harvest = make_harvest(harvest)
	frappe_client.insert(bloomtrace_harvest)

def update_harvest(harvest, frappe_client):
	bloomtrace_harvest = make_harvest(harvest)
	bloomtrace_harvest.update({
		"name": harvest.name
	})
	frappe_client.update(bloomtrace_harvest)

def make_harvest(harvest):
	bloomtrace_harvest_dict = {
		"doctype": "Harvest",
		"bloomstack_company": harvest.company,
		"harvest":harvest.name,
		"harvest_type": harvest.harvest_type,
		"harvest_location":harvest.harvest_location,
		"drying_location": harvest.drying_location,
		"current_weight": harvest.harvest_weight,
		"unit_of_weight_name": harvest.harvest_uom,
		"is_finished": harvest.is_finished
	}
	return bloomtrace_harvest_dict
