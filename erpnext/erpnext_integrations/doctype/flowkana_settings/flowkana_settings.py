# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
import requests
import json
from six import text_type
from frappe.model.document import Document

class FlowkanaSettings(Document):

	def validate(self):
		self.check_fulfillment_partner()
		self.toggle_status()

	def toggle_status(self):
		frappe.db.set_value("Fulfillment Partner", "Flowkana", "enable", self.enable_flowkana)

	def check_fulfillment_partner(self):
		"""
		Create a fulfillment partner in case they don't exist.
		"""
		if self.enable_flowkana and not frappe.db.exists("Fulfillment Partner", "Flowkana"):
			partner = frappe.get_doc({
				"doctype": "Fulfillment Partner",
				"partner_name": "Flowkana",
				"enable": 1
			}).save()

def send_delivery_request_to_flowkana(sales_order):
	"""
	Ping flowkana with sales order details and map response to an integration request.

	Args:
		sales_order_name (string): name of the sales order that needs to be sent to flowkana
	"""
	#create line items
	item_list = []
	for item in sales_order.items:
		ivt_id = frappe.get_value("Item", item.item_code, "ivt_id")
		line_item = {
			"attributes": {
			"ivt_id": ivt_id,
			"test_batch_id": item.batch_no,
			"external_item_code": item.item_code,
			"unit_quantity": item.qty,
			"unit_price": item.rate
			}
		}
		item_list.append(line_item)

	#prepare response json
	request_json = {
		"data": {
			"attributes": {
				"external_order_id": sales_order.name,
				"customer_name": sales_order.customer,
				"customer_license": sales_order.license,
				"delivery_date": str(sales_order.delivery_date),
				"note": "Test Note"
			},
			"relationships": {
				"order_line_items": item_list
			}
		}
	}

	#create integration request
	integration_request = frappe.new_doc("Integration Request")
	integration_request.update({
		"integration_type": "Host",
		"integration_request_service": "Flowkana",
		"status": "Queued",
		"data": json.dumps(request_json, default=json_handler),
		"reference_doctype": "Sales Order",
		"reference_docname": sales_order.name
	})
	integration_request.save(ignore_permissions=True)

	#fetch and prepare headers from flowkana settings, flag error if missing data
	flowkana_settings = frappe.get_cached_doc("Flowkana Settings")
	if not flowkana_settings.get("url_tab"):
		frappe.throw(_("Please provide an endpoint to send data to."))
	if not flowkana_settings.get("api_key", 0.0):
		frappe.throw(_("Please enter API Key in flowkana settings."))
	if not flowkana_settings.get("api_value", 0.0):
		frappe.throw(_("Please enter API Value in flowkana settings."))

	headers = {
		flowkana_settings.get("api_key"): flowkana_settings.get("api_value")
	}

	print("request_json: ", request_json)

	#ping flowkana with requisite headers and data
	response = requests.post(
		flowkana_settings.get("url_tab"),
		headers=headers,
		json=request_json)
	response_data = response.json()

	if response.status_code not in [200, 201, 202]:
		frappe.throw("The response has the following errors: {0}".format(response_data.get("errors"),""))
		return

	#mark integration request status as queued, update status to queued
	integration_request.output = json.dumps(response_data, default=json_handler)
	integration_request.save(ignore_permissions=True)

def json_handler(obj):
	if isinstance(obj, (datetime.date, datetime.timedelta, datetime.datetime)):
		return text_type(obj)
