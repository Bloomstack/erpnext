# -*- coding: utf-8 -*-
# Copyright (c) 2020, Bloom Stack, Inc and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class PackageTag(Document):
	def validate(self):
		if self.source_package_tag:
			self.validate_source_package_tag()
			self.update_coa_batch_no()
		self.calculate_package_tag_qty()
		self.set_coa_batch_in_batch_no()

	def validate_source_package_tag(self):
		source_package_tag = frappe.db.get_value("Package Tag", self.source_package_tag, "source_package_tag")
		if self.name == source_package_tag:
			frappe.throw(_("Invalid package tag. {0} is already the source package for {1}.".format(self.name, self.source_package_tag)))

	def update_coa_batch_no(self):
		self.coa_batch_no = frappe.db.get_value("Package Tag", self.source_package_tag, "coa_batch_no")

	def calculate_package_tag_qty(self):
		self.package_tag_qty = frappe.db.get_value("Stock Ledger Entry", {"docstatus": 1, "package_tag": self.package_tag}, "sum(actual_qty)")

	def set_coa_batch_in_batch_no(self):
		"""
		Assigns the coa_batch_no to the batch specified in the package tag.
		"""
		if self.batch_no and self.coa_batch_no:
			frappe.db.set_value("Batch", self.batch_no, "coa_batch", self.coa_batch_no)

@frappe.whitelist()
def get_package_tag_qty(package_tag=None):
	out = 0

	if package_tag:
		out = frappe.db.sql('''select warehouse, sum(actual_qty) as qty
			from `tabStock Ledger Entry`
			where package_tag=%s
			group by warehouse''', package_tag, as_dict=1)

	return out

@frappe.whitelist()
def make_stock_reconciliation(item_code, batch_no, package_tag, qty, warehouse, adjustment_reason):
	stock_reco = frappe.new_doc("Stock Reconciliation")
	stock_reco.purpose = "Stock Reconciliation"
	stock_reco.append("items", {
			"item_code": item_code,
			"qty": qty,
			"warehouse": warehouse,
			"package_tag": package_tag,
			"batch_no": batch_no,
			"adjustment_reason": adjustment_reason
		})
	stock_reco.submit()
	frappe.db.commit()
	return stock_reco

@frappe.whitelist()
def make_waste_disposal(source_name, target_doc=None):
	"""
	Create Waste Disposal from a Package tag
	Args:
		source_name: string -> name of Package tag through which Waste Disposal will be created
	Return:
		dictionary -> it contains the all the value assigned to the Waste Disposal.
	"""
	def set_missing_values(source, target):
		target.append("items", {
			"item_code": source.item_code,
			"item_name": source.item_name,
			"item_group": source.item_group,
			"batch_no": source.batch_no
		})

	doc = get_mapped_doc("Package Tag", source_name, {
		"Package Tag": {
			"doctype": "Waste Disposal",
		}
	}, target_doc, set_missing_values)
	return doc

@frappe.whitelist()
def make_package_tag_from_batch(source_name, target_doc=None):
	"""
	Creates Package Tag from Batch.

	Args:
		source_name (string): name of the doc from which package tag is to be created
		target_doc (list, optional): target document to be created. Defaults to None.

	Returns:
		target_doc: Created Package Tag Document
	"""

	target_doc = get_mapped_doc("Batch", source_name, {
		"Batch": {
			"doctype": "Package Tag",
			"field_map": {
				"item": "item_code",
				"name": "batch_no"
			}
		},
	}, target_doc)

	return target_doc