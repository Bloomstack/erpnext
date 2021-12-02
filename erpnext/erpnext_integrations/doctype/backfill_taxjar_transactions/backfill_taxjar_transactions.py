# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import traceback
import frappe
import taxjar
import pycountry
import json
from frappe import _
from frappe.model.document import Document
from erpnext.erpnext_integrations.taxjar_integration import create_transaction, get_tax_data
from frappe.integrations.utils import make_integration_request, update_integration_request

class BackfillTaxJarTransactions(Document):
	def push_transaction(self):
		print("--------------------hit")
		client = get_client(self)

		if not client:
			return
		orders = client.list_orders({
			'from_transaction_date': frappe.utils.formatdate(self.from_date, 'yyyy/mm/dd'),
			'to_transaction_date': frappe.utils.formatdate(self.to_date, 'yyyy/mm/dd')
		})
		print("---orderssssssssss---------------------------", self.from_date, frappe.utils.formatdate(self.from_date, 'yyyy/mm/yy'), frappe.utils.formatdate(self.to_date, 'yyyy/mm/yy'), orders)
		TAX_ACCOUNT_HEAD = frappe.db.get_value("TaxJar Configuration", self.company,  "tax_account_head")
		SHIP_ACCOUNT_HEAD = frappe.db.get_value("TaxJar Configuration", self.company, "shipping_account_head")
		for doc in frappe.get_all('Sales Invoice',
			filters={"posting_date": ('between', [self.from_date, self.to_date]), "docstatus": "1", "exempt_from_sales_tax": 0, "company": self.company}, 
			fields=[
				'name',
				'creation',
				'docstatus',
				'is_return',
				'company',
				'customer',
				'tax_id',
				'customer_address',
				'address_display',
				'shipping_address',
				'company_address',
				'exempt_from_sales_tax',
				'total_qty',
				'total',
				'shipping_address_name',
				'net_total',
				'shipping_rule'
			]):
			print("-------------------doc----------name---------", doc.name)
			sales_taxes = frappe.get_all('Sales Taxes and Charges',
				filters={'parenttype': 'Sales Invoice',
				'parent': doc.name, 'account_head': TAX_ACCOUNT_HEAD},
				fields=['tax_amount'])
			
			shipping_amount = frappe.get_all('Sales Taxes and Charges',
				filters={'parenttype': 'Sales Invoice',
				'parent': doc.name, 'account_head': SHIP_ACCOUNT_HEAD},
				fields=['tax_amount'])
			if shipping_amount and shipping_amount[0].tax_amount > 0:
				shipping_amount = shipping_amount[0].tax_amount
			else:
				shipping_amount = 0

			if sales_taxes and sales_taxes[0].tax_amount > 0:
				create_transaction(doc, sales_taxes[0].tax_amount, shipping_amount, orders, force=self.force)



def create_transaction(doc, sales_tax, shipping_amount, orders, force=None):
	"""Create an order transaction in TaxJar"""
	client = get_client(doc)

	if not client:
		return

	doc_data = frappe.get_doc("Sales Invoice", doc.name)
	tax_dict = get_tax_data(doc_data)

	if not tax_dict:
		return

	tax_dict['transaction_id'] = doc.name
	tax_dict['transaction_date'] = frappe.utils.formatdate(doc.creation)
	tax_dict['sales_tax'] = sales_tax
	tax_dict['amount'] = doc.total + tax_dict['shipping']

	integration_request = make_integration_request('Sales Invoice', doc.name, service="TaxJar")
	try:
		if force:
			print("orders------------------------", doc.name, type(orders))
			if doc.name in orders.data:
				print("--------force-update")
				if doc.is_return:
					update_integration_request(integration_request, endpoint="client.update_refund")
					tax_dict['transaction_reference_id'] = doc.return_against
					response = client.update_refund(doc.name, tax_dict)
				else:
					update_integration_request(integration_request, endpoint="client.update_order")
					response = client.update_order(doc.name, tax_dict)
			else:
				print("--------force-create")
				if doc.is_return:
					update_integration_request(integration_request, endpoint="client.create_refund")
					tax_dict['transaction_reference_id'] = doc.return_against
					response = client.create_refund(tax_dict)
				else:
					update_integration_request(integration_request, endpoint="client.create_order")
					response = client.create_order(tax_dict)
		else:
			if doc.name not in orders.data:
				print("--------else-create")
				if doc.is_return:
					update_integration_request(integration_request, endpoint="client.create_refund")
					tax_dict['transaction_reference_id'] = doc.return_against
					response = client.create_refund(tax_dict)
				else:
					update_integration_request(integration_request, endpoint="client.create_order")
					response = client.create_order(tax_dict)

	except taxjar.exceptions.TaxJarResponseError as err:
		update_integration_request(integration_request, status="Failed", error=str(err))
	else:
		update_integration_request(integration_request, status="Completed")


# def get_tax_data(doc):
# 	SHIP_ACCOUNT_HEAD = frappe.db.get_value("TaxJar Configuration", doc.company, "shipping_account_head")
# 	from_address = frappe.get_doc('Address', doc.company_address)
# 	from_shipping_state = from_address.get('state')
# 	from_country_code = frappe.db.get_value('Country',
# 			from_address.country, 'code')
# 	from_country_code = from_country_code.upper()

# 	to_address = get_shipping_address_details(doc)
# 	to_shipping_state = to_address.get('state')
# 	to_country_code = frappe.db.get_value('Country',
# 			to_address.country, 'code')
# 	to_country_code = to_country_code.upper()


# 	shipping_amount = frappe.get_all('Sales Taxes and Charges',
# 			filters={'parenttype': 'Sales Invoice',
# 			'parent': doc.name, 'account_head': SHIP_ACCOUNT_HEAD},
# 			fields=['tax_amount'])
# 	if shipping_amount and shipping_amount[0].tax_amount > 0:
# 	   shipping_amount = shipping_amount[0].tax_amount
# 	else:
# 		shipping_amount = 0

# 	if to_shipping_state is not None:
# 		to_shipping_state = get_iso_3166_2_state_code(to_address)

# 	tax_dict = {
# 		'from_country': from_country_code,
# 		'from_zip': from_address.pincode,
# 		'from_state': from_shipping_state,
# 		'from_city': from_address.city,
# 		'from_street': from_address.address_line1,
# 		'to_country': to_country_code,
# 		'to_zip': to_address.pincode,
# 		'to_city': to_address.city,
# 		'to_street': to_address.address_line1,
# 		'to_state': to_shipping_state,
# 		'shipping': shipping_amount,
# 		'amount': doc.net_total,
# 		'plugin': '[bloomstack]',
# 		}
# 	return tax_dict


# def get_shipping_address_details(doc):
# 	"""Return customer shipping address details"""

# 	if doc.shipping_address_name:
# 		shipping_address = frappe.get_doc('Address', doc.shipping_address_name)
# 	elif doc.customer_address:
# 		shipping_address = frappe.get_doc('Address', doc.customer_address)
# 	else:
# 		shipping_address = frappe.get_doc('Address', doc.company_address)

# 	return shipping_address

def get_client(doc):
	TAXJAR_ENABLED = frappe.db.get_value("TaxJar Configuration", doc.company, "enabled")

	if not TAXJAR_ENABLED:
		return

	taxjar_settings = frappe.get_doc("TaxJar Configuration", doc.company)

	if not taxjar_settings.is_sandbox:
		api_key = taxjar_settings.get_password("api_key")
		api_url = taxjar.DEFAULT_API_URL
	else:
		api_key = taxjar_settings.get_password("sandbox_api_key")
		api_url = taxjar.SANDBOX_API_URL

	if api_key and api_url:
		client = taxjar.Client(api_key=api_key, api_url=api_url)
		client.set_api_config('headers', {
			'x-api-version': '2020-08-07'
		})
		return client
	
# def get_iso_3166_2_state_code(address):
# 	if not address.get("state"):
# 		return ""

# 	country_code = frappe.db.get_value("Country", address.get("country"), "code")
# 	state = address.get("state").upper().strip()

# 	# The max length for ISO state codes is 3, excluding the country code
# 	if len(state) <= 3:
# 		# PyCountry returns state code as {country_code}-{state-code} (e.g. US-FL)
# 		address_state = (country_code + "-" + state).upper()

# 		states = pycountry.subdivisions.get(country_code=country_code.upper())
# 		states = [pystate.code for pystate in states]

# 		if address_state in states:
# 			return state

# 		frappe.throw(_(error_message))
# 	else:
# 		try:
# 			lookup_state = pycountry.subdivisions.lookup(state)
# 		except LookupError:
# 			frappe.throw(_(error_message))
# 		else:
# 			return lookup_state.code.split('-')[1]


# def sanitize_error_response(response):
# 	response = response.full_response.get("detail")
# 	response = response.replace("_", " ")

# 	sanitized_responses = {
# 		"to zip": "Zipcode",
# 		"to city": "City",
# 		"to state": "State",
# 		"to country": "Country"
# 	}

# 	for k, v in sanitized_responses.items():
# 		response = response.replace(k, v)

# 	return response