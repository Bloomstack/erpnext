# -*- coding: utf-8 -*-
# Copyright (c) 2020, Bloomstack, Inc and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ComplianceItem(Document):
	def validate(self):
		self.validate_item_category()
		self.validate_existing_compliance_item()

	def validate_item_category(self):
		if self.enable_cultivation_tax and not self.item_category:
			frappe.throw(_("Please select an Item Category to enable cultivation tax"))

	def validate_existing_compliance_item(self):
		if self.is_new() and frappe.db.exists("Compliance Item", self.item_code):
			frappe.throw(_("A Compliance Item already exists for {}".format(self.item_code)))
