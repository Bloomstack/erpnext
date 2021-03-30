# -*- coding: utf-8 -*-
# Copyright (c) 2020, Bloom Stack, Inc and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class ComplianceSettings(Document):

	def on_update(self):
		frappe.clear_document_cache(self.doctype, self.name)
