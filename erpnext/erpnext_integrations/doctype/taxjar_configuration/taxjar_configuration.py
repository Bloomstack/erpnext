# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.erpnext_integrations.taxjar_integration import get_client
import taxjar
from frappe.integrations.utils import create_request_log

class TaxJarConfiguration(Document):
	def validate_api_key(self):
		data = {
			"reference_doctype": self.doctype,
			"reference_docname": self.name
		}
		client = get_client(self)
		try:
			self.integration_request = create_request_log(data, 'Host', 'TaxJar')
			self.integration_request.endpoint = "validate_api_key"
			categories = client.categories()
		except taxjar.exceptions.TaxJarResponseError as error:
			self.integration_request.error = str(error)
			self.integration_request.update_status(data, "Failed")
			return {"error": error}
		else:
			self.integration_request.output = str(categories)
			self.integration_request.update_status(data, "Completed")
			return categories

	def update_nexus_list(self):
		data = {
			"reference_doctype": self.doctype,
			"reference_docname": self.name
		}
		client = get_client(self)
		
		try:
			self.integration_request = create_request_log(data, 'Host', 'TaxJar')
			self.integration_request.endpoint = "update_nexus_list"
			nexus = client.nexus_regions()
		except taxjar.exceptions.TaxJarResponseError as error:
			self.integration_request.error = str(error)
			self.integration_request.update_status(data, "Failed")
		else:
			self.integration_request.output = str(nexus)
			self.integration_request.update_status(data, "Completed")

		new_nexus_list = [frappe._dict(address) for address in nexus]

		self.set('nexus', [])
		self.set('nexus', new_nexus_list)
		self.save()
		return len(new_nexus_list)