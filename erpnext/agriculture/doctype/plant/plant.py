# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import getdate, nowdate, today, cstr
from erpnext.agriculture.doctype.plant_batch.plant_batch import validate_quantities
from erpnext.compliance.utils import make_integration_request, get_bloomtrace_client


class Plant(Document):
	def before_insert(self):
		if not self.title:
			self.title = self.strain + " - " + self.plant_tag

	def on_update(self):
		self.create_integration_request()

	def create_integration_request(self):
		make_integration_request(self.doctype, self.name, "Plant")

	def destroy_plant(self, destroy_count, reason):
		validate_quantities(self, destroy_count)
		destroyed_plant_log = frappe.get_doc(
			dict(
				doctype = 'Destroyed Plant Log',
				category_type = "Plant",
				category = self.name,
				destroy_count = destroy_count,
				reason = reason,
				actual_date = getdate(nowdate())
			)
		).insert()
		destroyed_plant_log.submit()
		return destroyed_plant_log.name


@frappe.whitelist()
def make_harvest(source_name, target_doc=None):
	def update_plant(source, target):
		target.append("plants", {
			"plant": source.name,
			"plant_tag": source.plant_tag,
			"plant_batch": source.plant_batch,
			"strain": source.strain,
			"actual_date": today()
		})

	target_doc = get_mapped_doc("Plant", source_name,
		{"Plant": {
			"doctype": "Harvest",
			"field_map": {
				"location": "harvest_location"
			}
		}}, target_doc, update_plant)

	return target_doc

def execute_bloomtrace_integration_request():
	frappe_client = get_bloomtrace_client()
	if not frappe_client:
		return

	pending_requests = frappe.get_all("Integration Request",
		filters={"status": ["IN", ["Queued", "Failed"]], "reference_doctype": "Plant", "integration_request_service": "BloomTrace"},
		order_by="creation ASC",
		limit=50)

	for request in pending_requests:
		integration_request = frappe.get_doc("Integration Request", request.name)
		plant = frappe.get_doc("Plant", integration_request.reference_docname)
		bloomtrace_plant = frappe_client.get_doc("Plant", filters={"label" : integration_request.reference_docname})
		try:
			if not bloomtrace_plant:
				insert_plant(plant, frappe_client)
			else:
				update_plant(plant, frappe_client, bloomtrace_plant)
			integration_request.error = ""
			integration_request.status = "Completed"
			integration_request.save(ignore_permissions=True)
		except Exception as e:
			integration_request.error = cstr(frappe.get_traceback())
			integration_request.status = "Failed"
			integration_request.save(ignore_permissions=True)

def insert_plant(plant, frappe_client):
	bloomtrace_plant = make_plant(plant)
	frappe_client.insert(bloomtrace_plant)

def update_plant(plant, frappe_client, bloomtrace_plant):
	plant_payload = make_plant(plant)
	plant_payload.update({
		"name": bloomtrace_plant[0].get("name")
	})
	frappe_client.update(plant_payload)

def make_plant(plant):
	bloomtrace_plant_dict = {
		"doctype": "Plant",
		"bloomstack_company": plant.company,
		"label":plant.name,
		"plant_batch_name": plant.plant_batch,
		"strain_name": plant.strain,
		"location_name": plant.location,
		"growth_phase": plant.growth_phase,
		"harvest_count": plant.harvested_count
	}
	return bloomtrace_plant_dict