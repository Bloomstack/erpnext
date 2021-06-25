# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import pprint
from frappe.utils import add_days, cint, cstr, flt
import datetime
import requests
from frappe.model.document import Document
import base64
import hashlib
import hmac
from frappe import _
from six import text_type

class LeafLinkSettings(Document):
	pass

@frappe.whitelist()
def sync_customer_with_leaflink(customer_name):
	"""
	Sync a customer with leaflink by hitting Sync with Customer Button.
	"""
	leaflink_settings = frappe.get_cached_doc("LeafLink Settings")
	header = {
		leaflink_settings.get("api_key"): leaflink_settings.get("api_value")
	}

	#validate if leaflink is enabled
	if not leaflink_settings.get("enable_leaflink"):
		frappe.throw("Please enable LeafLink in LeafLink Settings.")

	#check if customer exists on leaflink
	try:
		customers_on_leaflink = requests.get(leaflink_settings.get("customers_url"), headers=header, params={"name": customer_name}).json()
	except Exception as e:
		frappe.throw(_("An Exception: {e} occured while trying to sync customer on LeafLink. Please try again.".format(e)))

	#create customer record on leaflink if it does not exist
	if not customers_on_leaflink.get("count"):

		#create new customer data
		new_customer = {
			"name": customer_name,
			"owner": leaflink_settings.get("leaflink_id")
	 	}

		#post request to create customer in leaflink
		try:
			post_response = requests.post(leaflink_settings.get("customers_url"), headers=header, data=new_customer)
			if post_response.status_code == 201:
				frappe.msgprint(_("Customer successfully created on LeafLink!"))
		except Exception as e:
			frappe.throw(_("An Exception: {e} occured while trying to sync customer on LeafLink. Please try again.".format(e)))

	else:
		frappe.msgprint(_("Customer already exists on LeafLink!"))


def authenticate_leaflink_request(leaflink_settings):
	"""
	Authenticate an incoming request from LeafLink before creating a sales order.

	Args:
		leaflink_settings (dict]): contains leaflink configurations stored in Bloomstack
		integration_request (dict]): contains details of the integration request for the sale order
	"""
	#ensure leaflink is enabled before proceeding further.
	if not leaflink_settings.get("enable_leaflink"):
		return

	#validate incoming keys
	key = bytes(leaflink_settings.get("incoming_api_authentication_key"), 'utf-8')
	incoming_signature = frappe.local.request.headers['LL-Signature'].encode("utf-8")
	request_body = frappe.local.request.data
	computed_signature = base64.b64encode(hmac.new(key, request_body, digestmod=hashlib.sha256).digest())
	success = computed_signature == incoming_signature
	if not success:
		return False
	return True


@frappe.whitelist(allow_guest=True)
def sales_order_from_leaflink(**args):
	"""
	Endpoint for integrating a sales order created on LeafLink with Bloomstack.
	"""

	leaflink_settings = frappe.get_cached_doc("LeafLink Settings")
	header = {
		leaflink_settings.get("api_key"): leaflink_settings.get("api_value")
	}
	#validate incoming keys
	if not authenticate_leaflink_request(leaflink_settings):
		return

	#create integration request
	integration_request = frappe.new_doc("Integration Request")
	integration_request.update({
		"integration_type": "Host",
		"integration_request_service": "LeafLink",
		"status": "Queued",
		"data":  json.dumps(args, default=json_handler),
		"reference_doctype": "Sales Order"
	})
	integration_request.save(ignore_permissions=True)

	#curate data from settings for post request
	legacy_header = {
		leaflink_settings.get("api_key"): leaflink_settings.get("legacy_api_key")
	}

	sales_order = args.get("data")
	#exit if the action is not to create a new sales order
	if args.get("action") != "create":
		return

	#extract customer and license data
	customer = sales_order.get("customer")
	customer_name = customer.get('name')
	license_no = customer.get('license_number')

	#retrieve customer_name if license_no is in record
	if not frappe.db.exists("Customer", customer_name):

		if frappe.db.exists("Compliance Info", license_no):

			#find customer using license info in case name does not match
			license_parent = frappe.get_all("Compliance License Detail",
				filters={"license": license_no},
				fields=['parent'])
			if license_parent:
				customer_name = license_parent[0].get("parent")
		else:
			#update integration request with message telling user that the customer needs to be created before proceeding further
			integration_request.update({
				"status": "Failed",
				"error": "Customer does not exist in Bloomstack. Please create the customer and try again."
			})
			integration_request.save(ignore_permissions=True)
			return

	#create a sales order document with an autoset expected delivery date
	expected_delivery_days = cint(frappe.get_value("Selling Settings", None, "expected_delivery_days"))
	sales_order_doc = frappe.get_doc({
		"doctype": "Sales Order",
		"transaction_date": datetime.datetime.now(),
		"customer": customer_name,
		"license": license_no,
		"delivery_date": add_days(datetime.datetime.now(), expected_delivery_days),
		"order_type": "Sales"
	})

	#visit all items in order from leaflink, match sku to item code and add to sales order
	for item in sales_order.get("orderedproduct_set"):

		try:
			#fetch line item details, retrieve batch_id, fetch batch name from leaflink, get request might fail
			item_details = requests.get(leaflink_settings.get("base_url")+"/line-items", headers=header,params={"id": item.get("id")}).json()
			batch_details = requests.get(leaflink_settings.get("base_url")+"/batches/", headers=legacy_header,params={"id": item_details.get("batch")}).json()
			batch_name = batch_details.get("results")[0].get("production_batch_number")

			#adjust rate or quantity when item is sold by case vs item is sold by gram
			quantity = flt(item.get("quantity"))/flt(item.get("unit_multiplier")) if item_details.get("sold_by_case") else flt(item.get("quantity"))
			rate = flt(item.get("sale_price")) if item_details.get("sold_by_case") else flt(item.get("sale_price"))/flt(item.get("unit_multiplier"))

			#appending items to sales order document, might fail if item or batch_no is missing from bloomstack
			sales_order_doc.append("items",{
				"item_code": item.get("product").get("sku"),
				"rate": rate,
				"qty": quantity,
				"batch_no": batch_name,
				"actual_qty": item.get("quantity"),
				"delivery_date": add_days(datetime.datetime.now(), expected_delivery_days)
			})
		except Exception as e:
			integration_request.update({
				"status": "Failed",
				"error": cstr(e)
			})
			integration_request.save(ignore_permissions=True)
			return

	#insert the sales order as a draft, update integration request to Success
	sales_order_doc.save(ignore_permissions=True)
	integration_request.update({
		"status": "Completed",
		"reference_docname": sales_order_doc.name
	})
	integration_request.save(ignore_permissions=True)

def json_handler(obj):
	if isinstance(obj, (datetime.date, datetime.timedelta, datetime.datetime)):
		return text_type(obj)
