# -*- coding: utf-8 -*-
# Copyright (c) 2020, Bloom Stack, Inc and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class ComplianceSettings(Document):

	def validate(self):
		self.validate_companies()

	def validate_companies(self):
		companies = []

		for company in self.company:
			if company.company not in companies:
				companies.append(company.company)
			else:
				frappe.throw(_("Company {0} already added to sync.").format(frappe.bold(company.company)))

	def on_update(self):
		frappe.clear_document_cache(self.doctype, self.name)
