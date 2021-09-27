# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.erpnext_integrations.taxjar_integration import get_client
import taxjar

class TaxJarSettings(Document):
	def validate_api_key(self):
		client = get_client(self)
		try:
			categories = client.categories()
		except taxjar.exceptions.TaxJarResponseError as error:
			return {"error": error}
		else:
			return categories
