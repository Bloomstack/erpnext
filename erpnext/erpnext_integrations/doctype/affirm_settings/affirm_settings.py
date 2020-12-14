# -*- coding: utf-8 -*-
# Copyright (c) 2018, Bloomstack and contributors
# For license information, please see license.txt

"""
# Integrating Affirm

### 1. Validate Currency Support

Example:

	from frappe.integrations.utils import get_payment_gateway_controller

	controller = get_payment_gateway_controller("Affirm")
	controller().validate_transaction_currency(currency)

### 2. Redirect for payment

Example:

	payment_details = {
		"amount": 600,
		"title": "Payment for bill : 111",
		"description": "payment via cart",
		"reference_doctype": "Payment Request",
		"reference_docname": "PR0001",
		"payer_email": "NuranVerkleij@example.com",
		"payer_name": "Nuran Verkleij",
		"order_id": "111",
		"currency": "USD",
		"payment_gateway": "Affirm"
	}

	# redirect the user to this url
	url = controller().get_payment_url(**payment_details)


### 3. On Completion of Payment

Write a method for `on_payment_authorized` in the reference doctype

Example:

	def on_payment_authorized(payment_status):
		# your code to handle callback
"""

from __future__ import unicode_literals
import frappe
from frappe import _
import requests
import json

from frappe.model.document import Document
from frappe.utils import get_url, call_hook_method, cint, getdate
from frappe.integrations.utils import create_payment_gateway, create_request_log
from six.moves.urllib.parse import urlencode

from requests.auth import HTTPBasicAuth
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

class AffirmSettings(Document):
	supported_currencies = [
		"USD"
	]

	service_name = "Affirm"
	is_embedable = True

	def validate(self):
		create_payment_gateway("Affirm")
		call_hook_method('payment_gateway_enabled', gateway=self.service_name)

	def get_payment_url(self, **kwargs):
		return get_url("./integrations/affirm_checkout?{0}".format(urlencode(kwargs)))


	def validate_transaction_currency(self, currency):
		if currency not in self.supported_currencies:
			frappe.throw(_("Please select another payment method. Affirm does not support transactions in currency '{0}'").format(currency))

def create_order(**kwargs):
	"""
		Read the checkout data and current checkout status for a specific checkout attempt.
	"""
	full_name = kwargs.get("payer_name")

	# Affirm needs Full Name to have atleast 2 words
	if len(full_name.split()) == 1:
		full_name = full_name + " ."

	ref_doc = frappe.get_doc(kwargs['reference_doctype'], kwargs['reference_docname'])

	# fetch the actual doctype use for this transaction. Could be Quotation, Sales Order or Invoice
	order_doc = frappe.get_doc(ref_doc.reference_doctype, ref_doc.reference_name)

	items = []
	discounts = {}
	billing_address = None
	shipping_address = None

	if order_doc.get("customer_address"):
		billing_address = frappe.get_doc("Address", order_doc.customer_address)

	if order_doc.get("shipping_address_name"):
		shipping_address = frappe.get_doc("Address", order_doc.shipping_address_name)

	if not shipping_address:
		shipping_address = frappe.get_doc("Address", order_doc.customer_address)

	# deduce shipping from taxes table
	shipping_fee = 0
	for tax in order_doc.taxes:
		if 'shipping ' in tax.description.lower():
			shipping_fee = tax.tax_amount

	for idx, item in enumerate(order_doc.items):
		item_discount = item.price_list_rate - item.rate

		if item_discount > 0:
			discount_percent = 100 - (item.rate * 100 / item.price_list_rate)
			discount_code = _("LINE {0} | {1} | {2}% DISCOUNT ($ -{3:,.2f})").format(idx, item.item_code, discount_percent, item_discount)
			discounts[discount_code] = {
				"discount_amount": convert_to_cents(item_discount),
				"discount_display_name": discount_code
			}

		items.append({
			"display_name": item.item_name,
			"sku": item.item_code,
			"unit_price": convert_to_cents(item.price_list_rate),
			"qty": item.qty,
			"item_image_url": get_url(item.get("image", "")),
			"item_url": get_url()
		})

	checkout_data = {
		"merchant": {
			"user_confirmation_url": get_url(
				(
					"/api/method/erpnext.erpnext_integrations"
					".doctype.affirm_settings.affirm_settings.process_payment_callback"
					"?reference_doctype={0}&reference_docname={1}"
				).format(ref_doc.doctype, ref_doc.name)
			),
			"user_cancel_url": get_url("/cart"),
			"user_confirmation_url_action": "GET",
			"name": frappe.defaults.get_user_default("company")
		},
		"items": items,
		"discounts": discounts,
		"order_id": order_doc.name,
		"shipping_amount": convert_to_cents(shipping_fee),
		"tax_amount": convert_to_cents(order_doc.total_taxes_and_charges - shipping_fee),
		"total": convert_to_cents(order_doc.grand_total)
	}

	if billing_address:
		checkout_data['billing'] = {
			"name": {
				"full": full_name
			},
			"address": {
				"line1": billing_address.get("address_line1"),
				"line2": billing_address.get("address_line2"),
				"city": billing_address.get("city"),
				"state": billing_address.get("state"),
				"zipcode": billing_address.get("pincode"),
				"country": billing_address.get("country")
			}
		}

	if shipping_address:
		checkout_data['shipping'] = {
			"name": {
				"full": full_name
			},
			"address": {
				"line1": shipping_address.get("address_line1"),
				"line2": shipping_address.get("address_line2"),
				"city": shipping_address.get("city"),
				"state": shipping_address.get("state"),
				"zipcode": shipping_address.get("pincode"),
				"country": shipping_address.get("country")
			}
		}

	create_request_log(checkout_data, "Host", "Affirm")
	return checkout_data

@frappe.whitelist(allow_guest=1)
def process_payment_callback(checkout_token, reference_doctype, reference_docname):
	"""'
		Charge authorization occurs after a user completes the Affirm checkout flow and returns to the merchant site.
		Authorizing the charge generates a charge ID that will be used to reference it moving forward.
		You must authorize a charge to fully create it. A charge is not visible in the Read charge response,
		nor in the merchant dashboard until you authorize it.
	"""
	data= {
		"checkout_token":checkout_token,
		"reference_doctype":reference_doctype,
		"reference_docname":reference_docname
	}
	integration_request = create_request_log(data, "Host", "Affirm")
	redirect_url = "/integrations/payment-failed"
	affirm_settings = get_api_config()
	authorization_response = requests.post(
		"{api_url}/charges".format(**affirm_settings),
		auth=HTTPBasicAuth(
			affirm_settings.get('public_api_key'),
			affirm_settings.get('private_api_key')),
		json={"checkout_token": checkout_token})

	affirm_data = authorization_response.json()
	integration_request = frappe.get_doc("Integration Request", integration_request.name)
	integration_request.update_status(affirm_data, "Authorized")
	# frappe.log("Response: {}".format(json.dumps(affirm_data)))

	if affirm_data:
		authorize_payment(affirm_data, reference_doctype, reference_docname, integration_request)

def authorize_payment(affirm_data, reference_doctype, reference_docname, integration_request):
	"""
		once callback return checkout token it will authroized payment status as failed or sucessful
	"""
	payment_request = frappe.get_doc(reference_doctype, reference_docname)
	redirect_url = "/integrations/payment-failed"

	#if the payment request generated from a quotation, we convert quotation to sale order
	if payment_request.reference_doctype == "Quotation" and not affirm_data.get("type") == "invalid_request":
		
		#we get the quotation document and submit it
		quotation = frappe.get_doc(payment_request.reference_doctype, payment_request.reference_name)
		quotation.save(ignore_permissions=True)
		quotation.submit()

		#convert the quotation to a sales order
		from erpnext.selling.doctype.quotation.quotation import _make_sales_order
		sales_order = frappe.get_doc(_make_sales_order(quotation.name, ignore_permissions=True))
		sales_order.payment_schedule = []
		sales_order.flags.ignore_permissions = True
		sales_order.insert()
		#payment entry is made for affirm when it is captured in the sales order document in frappe desk

	# check if callback already happened
	if affirm_data.get("status_code") == 400 and affirm_data.get("code") == "checkout-token-used":
		integration_request.update_status(affirm_data, "Completed")
		redirect_url = '/integrations/payment-success'
	elif affirm_data.get("status_code") == 400 and affirm_data.get("type") == "invalid_request":
		integration_request.update_status(affirm_data, "Failed")
		frappe.msgprint(affirm_data.get("message"))
		redirect_url = "/cart"
	else:
		payment_successful(affirm_data, sales_order)
		integration_request.update_status(affirm_data, "Completed")
		redirect_url = '/integrations/payment-success'

	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = get_url(redirect_url)
	return ""

def payment_successful(affirm_data, order_doc):
	"""
		on sucessful payment response it will create payment entry for reference docname and
		update Affirm ID and Affirm status in reference docname
	"""
	order_doc.affirm_id = affirm_data.get('id')
	order_doc.affirm_status = affirm_data.get('status')
	order_doc.save(ignore_permissions=True)
	order_doc.submit()
	frappe.db.commit()

@frappe.whitelist()
def capture_payment(affirm_id, sales_order):
	"""
		Capture the payment from affirm on a customer's sales order. Create a new integration request for 
		the capture. Update the status of the sales order to paid and the integration request to Completed
	"""
	affirm_data ={
		"affirm_id":affirm_id,
		"sales_order":sales_order
	}

	#create a new integration request for capturing the affirm payment
	integration_request = create_request_log(affirm_data, "Host", "Affirm")
	affirm_settings = get_api_config()
	authorization_response = requests.post(
		"{0}/charges/{1}/capture".format(affirm_settings.get("api_url"), affirm_id),
		auth=HTTPBasicAuth(
			affirm_settings.get('public_api_key'),
			affirm_settings.get('private_api_key')),
		)

	#if the payment capture is authorized, update status of affirm in the sales order and integration_req
	if authorization_response.status_code==200:
		affirm_data = authorization_response.json()
		integration_request.update_status(affirm_data, "Authorized")
		frappe.db.set_value("Sales Order", sales_order, 
			"affirm_status", authorization_response.json().get("status"))
		make_so_payment_entry(affirm_data, sales_order)
		integration_request.update_status(affirm_data, "Completed")
	
	else:
		#if payment capture fails
		integration_request.update_status(affirm_data, "Failed")
		integration_request.error = authorization_response.reason
		integration_request.save()
		frappe.throw("Something went wrong.")

	create_sales_invoice_for_affirm(sales_order)
	integration_request.save()
	return affirm_data

def make_so_payment_entry(affirm_data, sales_order):
	""" Make a payment entry for the sales order and update the integration request 
	status to Completed"""

	payment_entry = get_payment_entry(dt="Sales Order", dn=sales_order, 
											bank_amount=affirm_data.get("amount"))
	payment_entry.reference_no = affirm_data.get("transaction_id")
	payment_entry.reference_date = getdate(affirm_data.get("created"))
	payment_entry.submit()

def create_sales_invoice_for_affirm(sales_order_name): 
	from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
	si = make_sales_invoice(sales_order_name, ignore_permissions=True)
	si.allocate_advances_automatically = True
	si = si.insert(ignore_permissions=True)
	si.submit()

@frappe.whitelist(allow_guest=1)
def get_public_config():
	config = get_api_config()
	del config['private_api_key'];

	return config

def get_api_config():
	settings = frappe.get_doc("Affirm Settings", "Affirm Settings")

	if settings.is_sandbox:
		values = dict(
			public_api_key = settings.public_sandbox_api_key,
			private_api_key = settings.get_password("private_sandbox_api_key"),
			checkout_url = settings.sandbox_checkout_url,
			api_url = settings.sandbox_api_url
		)
		return values
	else:
		values = dict(
			public_api_key = settings.public_api_key,
			private_api_key = settings.get_password("private_api_key"),
			checkout_url = settings.live_checkout_url,
			api_url = settings.live_api_url
		)
		return values

def convert_to_cents(amount):
	return cint(amount * 100)
