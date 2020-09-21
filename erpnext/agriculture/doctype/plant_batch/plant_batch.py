# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import ast

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, nowdate
from erpnext.agriculture.utils import create_project, create_tasks
from frappe.model.mapper import get_mapped_doc

class PlantBatch(Document):
	def validate(self):
		self.set_missing_values()

	def after_insert(self):
		self.create_plant_batch_project()

	def set_missing_values(self):
		strain = frappe.get_doc('Strain', self.strain)

		if not self.plant_spacing_uom:
			self.plant_spacing_uom = strain.plant_spacing_uom

	def create_plant_batch_project(self):
		strain = frappe.get_doc('Strain', self.strain)
		if strain.cultivation_task:
			self.project = create_project(self.title, self.start_date, strain.period)
			create_tasks(strain.cultivation_task, self.project, self.start_date)

	def reload_linked_analysis(self):
		linked_doctypes = ['Soil Texture', 'Soil Analysis', 'Plant Analysis']
		required_fields = ['location', 'name', 'collection_datetime']
		output = {}

		for doctype in linked_doctypes:
			output[doctype] = frappe.get_all(doctype, fields=required_fields)

		output['Location'] = frappe.get_doc('Location', self.location)

		frappe.publish_realtime("List of Linked Docs",
								output, user=frappe.session.user)

	def append_to_child(self, obj_to_append):
		for doctype in obj_to_append:
			for doc_name in set(obj_to_append[doctype]):
				self.append(doctype, {doctype: doc_name})

		self.save()

	def destroy_plant_batch(self, destroy_count, reason):
		if self.untracked_count == 0:
			frappe.throw(_("Cannot destroy Plant Batch as there is no untracked count."))

		if int(destroy_count) < 0 :
			frappe.throw(_("The Destroy Count ({0}) should be more than 0").format(destroy_count))

		if self.untracked_count < int(destroy_count):
			frappe.throw(_("The Destroy Count ({0}) should be less than or equal to the untracked count ({1})").format(destroy_count,self.untracked_count))

		destroyed_plant_log = frappe.get_doc(
			dict(
				doctype = 'Destroyed Plant Log',
				plant_batch = self.name,
				destroy_count = destroy_count,
				reason = reason,
				actual_date = getdate(nowdate())
			)
		).insert()
		destroyed_plant_log.submit()
		return destroyed_plant_log.name

def get_coordinates(doc):
	return ast.literal_eval(doc.location).get('features')[0].get('geometry').get('coordinates')


def get_geometry_type(doc):
	return ast.literal_eval(doc.location).get('features')[0].get('geometry').get('type')


def is_in_location(point, vs):
	x, y = point
	inside = False

	j = len(vs) - 1
	i = 0

	while i < len(vs):
		xi, yi = vs[i]
		xj, yj = vs[j]

		intersect = ((yi > y) != (yj > y)) and (
			x < (xj - xi) * (y - yi) / (yj - yi) + xi)

		if intersect:
			inside = not inside

		i = j
		j += 1

	return inside

@frappe.whitelist()
def make_plant(source_name, target_doc=None):
	target_doc = get_mapped_doc("Plant Batch", source_name,
		{"Plant Batch": {
			"doctype": "Plant",
			"field_map": {
				"name": "plant_batch"
			}
		}}, target_doc)

	return target_doc

@frappe.whitelist()
def make_additive_log(source_name, target_doc=None):
	target_doc = get_mapped_doc("Plant Batch", source_name,
		{"Plant Batch": {
			"doctype": "Plant Additive Log",
			"field_map": {
			}
		}}, target_doc)

	return target_doc

@frappe.whitelist()
def make_disease_diagnosis(source_name, target_doc=None):
	target_doc = get_mapped_doc("Plant Batch", source_name,
		{"Plant Batch": {
			"doctype": "Plant Disease Diagnosis",
			"field_map": {
			}
		}}, target_doc)

	return target_doc
