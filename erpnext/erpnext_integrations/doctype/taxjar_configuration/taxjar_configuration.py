# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.erpnext_integrations.taxjar_integration import get_client
import taxjar

class TaxJarConfiguration(Document):
	def validate_api_key(self):
		client = get_client(self)
		try:
			categories = client.categories()
		except taxjar.exceptions.TaxJarResponseError as error:
			return {"error": error}
		else:
			return categories

	def update_nexus_list(self):
		client = get_client(self)
		nexus = client.nexus_regions()

		new_nexus_list = [frappe._dict(address) for address in nexus]

		self.set('nexus', [])
		self.set('nexus', new_nexus_list)
		self.save()
		return len(new_nexus_list)

	def sync_product_tax_code(self):
		client = get_client(self)
		try:
			categories = client.categories()
		except taxjar.exceptions.TaxJarResponseError as error:
			return {"error": error}
		else:
			categories_list = [frappe._dict(category) for category in categories]
			frappe.enqueue('erpnext.erpnext_integrations.doctype.taxjar_configuration.taxjar_configuration.create_product_tax_code', categories_list=categories_list, now=True if len(categories_list) < 200 else False)

def create_product_tax_code(categories_list):
	"""
		Try to sync and update existing product tax categories and insert new if any
	"""
	count = 1
	for d in categories_list:
		frappe.publish_realtime('creating_product_tax_code', dict(
					progress = count, heading="Getting tasks", label = 'Fetching Product Tax Categories...', total=len(categories_list)))

		if not frappe.db.exists("Product Tax Categories", d.get("product_tax_code")):
			tax_category = frappe.get_doc({
				"doctype": "Product Tax Categories",
				"category_name": d.get("name"),
				"product_tax_code": d.get("product_tax_code"),
				"description": d.get("description")
			})
			tax_category.insert(ignore_permissions=True)
		else:
			tax_category = frappe.get_doc('Product Tax Categories', d.get("product_tax_code"))
			tax_category.description = d.get("description")
			tax_category.category_name = d.get("name")

			try:
				tax_category.save(ignore_permissions=True)
			except frappe.DuplicateEntryError:
				pass
		count += 1