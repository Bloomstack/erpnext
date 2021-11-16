# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.erpnext_integrations.taxjar_integration import get_client
import taxjar
import json
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import add_permission, update_permission_property
from frappe.integrations.utils import make_integration_request, update_integration_request

class TaxJarConfiguration(Document):
	def on_update(self):
		enabled = frappe.get_all("TaxJar Configuration", filters={"enabled": True})

		fields_already_exist = frappe.db.exists('Custom Field', {'dt': ('in', ['Item', 'Quotation Item', 'Sales Order Item', 'Sales Invoice Item']), 'fieldname':'product_tax_code'})
		if enabled:
			if not fields_already_exist:
				self.sync_product_tax_code()
				make_custom_fields()
				add_permissions()

			elif fields_already_exist:
				toggle_tax_category_fields(hidden='0')

		elif fields_already_exist:
			toggle_tax_category_fields(hidden='1')

	def validate(self):
		self.calculate_taxes_validation_for_create_transactions()

	def calculate_taxes_validation_for_create_transactions(self):
		if not self.taxjar_calculate_tax and (self.taxjar_create_transactions or self.is_sandbox):
			frappe.throw(frappe._('Before enabling <b>Create Transaction</b> or <b>Sandbox Mode</b>, you need to check the <b>Enable Tax Calculation</b> box'))

	def validate_api_key(self):
		client = get_client(self)

		if not client:
			return

		integration_request = make_integration_request(self.doctype, self.name, service="TaxJar", endpoint="client.categories")
		try:
			categories = client.categories()
		except taxjar.exceptions.TaxJarResponseError as error:
			update_integration_request(integration_request, status="Failed", error=str(error))
			return {"error": error}
		else:
			update_integration_request(integration_request, status="Completed", response=json.dumps([frappe._dict(category) for category in categories]))
			return categories

	def update_nexus_list(self):
		client = get_client(self)

		if not client:
			return

		integration_request = make_integration_request(self.doctype, self.name, service="TaxJar", endpoint="client.nexus_regions")
		try:
			nexus = client.nexus_regions()
		except taxjar.exceptions.TaxJarResponseError as error:
			update_integration_request(integration_request, status="Failed", error=str(error))
		else:
			new_nexus_list = [frappe._dict(address) for address in nexus]

			self.set('nexus', [])
			self.set('nexus', new_nexus_list)
			self.save()
			update_integration_request(integration_request, status="Completed", response=json.dumps(new_nexus_list))
			return len(new_nexus_list)

	def sync_product_tax_code(self):
		client = get_client(self)

		if not client:
			return

		integration_request = make_integration_request(self.doctype, self.name, service="TaxJar", endpoint="client.categories")
		try:
			categories = client.categories()
		except taxjar.exceptions.TaxJarResponseError as error:
			update_integration_request(integration_request, status="Failed", error=str(error))
			return {"error": error}
		else:
			categories_list = [frappe._dict(category) for category in categories]
			update_integration_request(integration_request, status="Completed", response=json.dumps(categories_list))
			frappe.enqueue('erpnext.erpnext_integrations.doctype.taxjar_configuration.taxjar_configuration.create_product_tax_code', categories_list=categories_list, now=True if len(categories_list) < 200 else False)

def toggle_tax_category_fields(hidden):
	doc_list = ['Item', 'Quotation Item', 'Sales Order Item', 'Sales Invoice Item']
	for doctype in doc_list:
		if doctype == 'Item':
			frappe.set_value('Custom Field', {'dt':doctype, 'fieldname':'product_tax_code'}, 'hidden', hidden)
		else:
			frappe.set_value('Custom Field', {'dt':doctype, 'fieldname':'product_tax_code'}, 'hidden', hidden)
			frappe.set_value('Custom Field', {'dt':doctype, 'fieldname':'tax_collectable'}, 'hidden', hidden)
			frappe.set_value('Custom Field', {'dt':doctype, 'fieldname':'product_tax_code'}, 'hidden', hidden)

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

def make_custom_fields(update=True):
	custom_fields = {
		'Quotation Item': [
			dict(fieldname='product_tax_code', fieldtype='Link', insert_after='description', options='Product Tax Categories',
				label='Product Tax Code', fetch_from='item_code.product_tax_category'),
			dict(fieldname='tax_collectable', fieldtype='Currency', insert_after='net_amount',
				label='Tax Collectable', read_only=1, options='currency'),
			dict(fieldname='taxable_amount', fieldtype='Currency', insert_after='tax_collectable',
				label='Taxable Amount', read_only=1, options='currency')
		],
		'Sales Order Item': [
			dict(fieldname='product_tax_code', fieldtype='Link', insert_after='description', options='Product Tax Categories',
				label='Product Tax Code', fetch_from='item_code.product_tax_category'),
			dict(fieldname='tax_collectable', fieldtype='Currency', insert_after='net_amount',
				label='Tax Collectable', read_only=1, options='currency'),
			dict(fieldname='taxable_amount', fieldtype='Currency', insert_after='tax_collectable',
				label='Taxable Amount', read_only=1, options='currency')
		],
		'Sales Invoice Item': [
			dict(fieldname='product_tax_code', fieldtype='Link', insert_after='description', options='Product Tax Categories',
				label='Product Tax Code', fetch_from='item_code.product_tax_category'),
			dict(fieldname='tax_collectable', fieldtype='Currency', insert_after='net_amount',
				label='Tax Collectable', read_only=1, options='currency'),
			dict(fieldname='taxable_amount', fieldtype='Currency', insert_after='tax_collectable',
				label='Taxable Amount', read_only=1, options='currency')
		],
		'Item': [
			dict(fieldname='product_tax_code', fieldtype='Link', insert_after='item_group', options='Product Tax Categories',
				label='Product Tax Code')
		]
	}

	create_custom_fields(custom_fields, update=update)

def add_permissions():
	doctype = "Product Tax Categories"
	for role in ('Accounts Manager', 'Accounts User', 'System Manager','Item Manager', 'Stock Manager'):
		add_permission(doctype, role, 0)
		update_permission_property(doctype, role, 0, 'write', 1)
		update_permission_property(doctype, role, 0, 'create', 1)