# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import getdate, nowdate, today
from erpnext.agriculture.doctype.plant_batch.plant_batch import validate_quantities


class Plant(Document):
	def before_insert(self):
		if not self.title:
			self.title = self.strain + " - " + self.plant_tag

	def validate_plant_quantities(self, destroy_count):
		validate_quantities(self, destroy_count)

	def destroy_plant(self, destroy_count, reason):
		self.validate_plant_quantities(destroy_count)
		destroyed_plant_log = frappe.get_doc(
			dict(
				doctype = 'Destroyed Plant Log',
				category = "Plant",
				plant = self.name,
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
