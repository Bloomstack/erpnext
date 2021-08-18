# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document

class QuotingSheet(Document):
	def validate(self):
		self.calculate_single_raw_material_cost()
		self.calculate_total_raw_material_cost()
		self.calculate_totals()

	def calculate_totals(self):
		"""
			Calculates total price and price per unit of item
		"""
		self.total_price = 0
		self.price_per_unit = 0
		total_charges = self.rm_cost + self.packaging_charges + self.shipping_cost
		if not self.bulk_discount:
			try:
				self.total_price = total_charges + (self.profit_margin/100 * total_charges)
				self.price_per_unit = flt(self.total_price) / flt(self.qty)
			except ZeroDivisionError:
				frappe.throw(_("Quantity can not be zero"))
		else:
			for discount in self.bulk_discount:
				if self.qty in range(discount.minimum_qty, discount.maximum_qty+1):
					if discount.discount_type == "Percentage":
						try:
							self.total_price = (flt(total_charges) + flt(self.profit_margin/100 * total_charges)) * flt(1 - (discount.discount_percentage/100))
							self.price_per_unit = flt(self.total_price) / flt(self.qty)
						except ZeroDivisionError:
							frappe.throw(_("Quantity can not be zero"))
					elif discount.discount_type == "Amount":
						try:
							self.total_price = flt(total_charges) + flt(self.profit_margin/100 * total_charges) - flt(discount.discount_amount)
							self.price_per_unit = flt(self.total_price) / flt(self.qty)
						except ZeroDivisionError:
							frappe.throw(_("Quantity can not be zero"))

	def calculate_total_raw_material_cost(self):
		"""
			Calculates total cost of raw materials
		"""
		self.rm_cost = 0
		for item in self.raw_material_items:
			self.rm_cost += item.amount
		return self.rm_cost

	def get_raw_materials(self):
		"""
			set raw materials items against to BOM Item given
		"""
		self.raw_material_items = []
		raw_materials = frappe.get_all("BOM Item", filters={"parent": self.bom})
		self.qty = frappe.db.get_value("BOM", self.bom, "quantity")
		for material in raw_materials:
			bom_item = frappe.db.get_value("BOM Item", material.name, ["item_code", "qty", "rate", "uom", "item_name"], as_dict = 1)
			if bom_item:
				self.append("raw_material_items", {
					"item_code": bom_item.get("item_code"),
					"qty": bom_item.get("qty"),
					"rate": bom_item.get("rate"),
					"uom": bom_item.get("uom"),
					"item_name": bom_item.get("item_name")
				})
		self.calculate_single_raw_material_cost()
		self.calculate_total_raw_material_cost() 

	def get_bulk_discount(self):
		"""
			set bulk disount against to bulk discount scheme given
		"""
		self.bulk_discount = []
		bulk_discounts = frappe.get_all("Bulk Discount", filters={"parent": self.bulk_discount_scheme})
		for discounts in bulk_discounts:
			discount_item = frappe.db.get_value("Bulk Discount", discounts.name, ["minimum_qty", "maximum_qty", "discount_type", "discount_percentage", "discount_amount"], as_dict = 1)
			if discount_item:
				self.append("bulk_discount", {
					"minimum_qty": discount_item.get("minimum_qty"),
					"maximum_qty": discount_item.get("maximum_qty"),
					"discount_type": discount_item.get("discount_type"),
					"discount_percentage": discount_item.get("discount_percentage"),
					"discount_amount": discount_item.get("discount_amount")
				})

	def calculate_single_raw_material_cost(self):
		"""
			calculate amount of single raw material cost
		"""
		for item in self.raw_material_items:
			item.amount = flt(item.qty) * flt(item.rate)

	def set_raw_materials_qty_against_quoting_qty(self,):
		"""
			set raw materials qty against quoting sheet qty
			formula = (qty of raw material in bom / qty of BOM Item) * new qty in quotation sheet
		"""
		#get item qty from bom
		backend_qty = frappe.db.get_value("BOM", self.bom, "quantity")
		for material in self.raw_material_items:
			bom_item = frappe.db.get_value("BOM Item", filters={"parent": self.bom, "item_code": material.item_code}, fieldname=["qty"], as_dict = 1)
			if bom_item:
				try:
					new_qty = (flt(bom_item.qty) / flt(backend_qty)) * flt(self.qty)
					# show new qty against item
					material.qty = new_qty
				except ZeroDivisionError:
					frappe.throw(_("Quantity can not be zero"))
			else:
				continue
		self.calculate_single_raw_material_cost()
		self.calculate_total_raw_material_cost()

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