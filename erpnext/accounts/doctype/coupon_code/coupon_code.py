# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json

from frappe import _
from frappe.model.document import Document
from frappe.utils import (strip)

class CouponCode(Document):
	def autoname(self):
		self.coupon_name = strip(self.coupon_name)
		self.name = self.coupon_name

		if not self.coupon_code:
			if self.coupon_type == "Promotional":
				self.coupon_code =''.join([i for i in self.coupon_name if not i.isdigit()])[0:8].upper()
			elif self.coupon_type == "Gift Card":
				self.coupon_code = frappe.generate_hash()[:10].upper()

	def validate(self):
		if self.coupon_type == "Gift Card":
			self.maximum_use = 1
			if not self.customer:
				frappe.throw(_("Please select the customer."))

	def get_brackets_meta(self):
		"""Returns bloom bracket's variable and command metadata for the loaded coupon"""

		from erpnext.bloombrackets.coupon_commands import build_coupon_meta, build_coupon_var_meta
		ctx = {
			"#META": {}
		}

		build_coupon_meta(ctx, "Quotation")
		build_coupon_var_meta(ctx, "Quotation")
		return ctx

def apply_coupon(doc):
	"""Applies coupon code to document. The passed document must be of type Quotation,
	Sales Order or Sales Invoice.
	"""
	# Run undo script if coupon_code was removed and automation script exists
	# Run undo script before setting coupon code else the calculated discount is added to the existing value
	if hasattr(doc, "automation_data"):
		run_coupon_undo_script(doc)

	if not doc.coupon_code:
		return

	coupon = frappe.get_doc("Coupon Code", doc.coupon_code)
	if coupon.brackets_code:
		ctx = run_brackets_script(coupon.brackets_code, doc, coupon)

		if len(ctx.get("#VARS").get("undo_script", [])) > 0:
			doc_automation = get_automation_data(doc)

			doc_automation.update({
				"linked_coupon": doc.coupon_code,
				"coupon_undo_script": ctx.get("#VARS").get("undo_script", [])
			})

			doc.automation_data = json.dumps(doc_automation)

def run_coupon_undo_script(doc):
	"""Runs a stored undo script generated during coupon apply on the provided document.
	The document must be of type Quotation, Sales Order or Sales Invoice
	"""
	if doc.automation_data:
		doc_automation = get_automation_data(doc)
		coupon_code_before_change = frappe.get_value(doc.doctype, doc.name, "coupon_code")

		if doc.coupon_code != coupon_code_before_change:
			script = doc_automation.get("coupon_undo_script", [])
			ctx = run_brackets_script(script, doc, None)

			# remove coupon link and undo script references from automation scripts
			if "linked_coupon" in doc_automation:
				del doc_automation["linked_coupon"]
			if "coupon_undo_script" in doc_automation:
				del doc_automation["coupon_undo_script"]

			doc.automation_data = json.dumps(doc_automation)

			if doc.meta.has_field('taxes'):

				# remove any tax items if they are linked to the previous coupon code
				taxes = []
				for item in doc.taxes:
					item_automation = get_automation_data(item)
					if item_automation.get("linked_coupon", None) != coupon_code_before_change:
						taxes.append(item)

			doc.taxes = taxes

def get_automation_data(doc):
	"""Parses automation data object where undo and coupon scripts references are stored"""
	try:
		return json.loads(doc.automation_data)
	except:
		return {}

def run_brackets_script(script, doc, coupon):
	"""Runs a bloombracket script on the provided document

	Params:
		script - The script to run. Can be string or list block
		doc - The document to run script against.
		coupon - The coupon document being applied.
	"""
	from erpnext.bloombrackets import run_script
	from erpnext.bloombrackets.coupon_commands import build_context

	# Prime script context with the document, coupon and undo_script vars.
	ctx = {
		"#VARS": {
			"doc": doc,
			"coupon": coupon,
			"undo_script": []
		}
	}

	# parse script if a string is passed.
	if isinstance(script, str):
		try:
			script = json.loads(script)
		except Exception as ex:
			print(ex)
			return

	# build the runtime context for the script but don't build metadata info.
	build_context(ctx, doc.doctype, skip_meta=True)
	run_script(script, ctx)

	return ctx
