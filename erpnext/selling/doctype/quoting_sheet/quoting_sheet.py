# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class QuotingSheet(Document):
	def validate(self):
		self.calculate_raw_material_cost()
		self.calculate_totals()

	def calculate_totals(self):
		"""
			Calculates total cost and cost per unit of item
		"""
		total_charges = self.rm_cost + self.packaging_charges + self.shipping_cost
		self.total_price = total_charges + ((total_charges * int(self.profit_markup))/100)

		self.price_per_unit = self.total_price / self.qty

	def calculate_raw_material_cost(self):
		self.rm_cost = 0
		for item in self.raw_material_items:
			self.rm_cost += item.amount


@frappe.whitelist()
def get_item_details_quoting_sheet(item_code):
	"""
	Send valuation rate, stock UOM and default BOM name to quoting sheet

	Args:
		item_code (str): item code for sending details to raw materials table in quoting sheet

	Returns:
		dict: return valuation rate, stock UOM and default BOM
	"""	
	return frappe.db.get_values("Item", item_code, ["valuation_rate", "stock_uom", "default_bom"], as_dict=1)[0]

@frappe.whitelist()
def update_latest_rate(docname):
	"""
	get latest value of valuation_rate from db and update it in Quoting Sheet
	"""	
	doc = frappe.get_doc("Quoting Sheet", docname)
	for item in doc.raw_material_items:
		rate = frappe.db.get_value("Item", item.get("item_code"), "valuation_rate", as_dict=1)
		item.rate = rate.valuation_rate
		item.amount = rate.valuation_rate * item.qty
	doc.save()
	frappe.msgprint(_("Rate updated"))