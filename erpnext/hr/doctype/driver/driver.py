# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import add_days, getdate, nowdate
from erpnext.stock.doctype.delivery_trip.delivery_trip import get_address_display_for_trip

API_VERSION = "v1.0"


class Driver(Document):
	def validate(self):
		self.get_employee_from_user()

	def get_employee_from_user(self):
		if self.user_id:
			employee = frappe.db.get_value("Employee", {"user_id": self.user_id})
			if employee:
				self.employee = employee


@frappe.whitelist()
def trips(driver_email):
	"""
	Get all trips assigned to the given driver.

	Args:
		driver_email (str): The email address of the driver

	Returns:
		dict: The Delivery Trips assigned to the driver, along with customer and item data
	"""

	trips_data = []
	driver_trips = frappe.get_all("Delivery Trip", filters=get_filters(driver_email), fields=["name"])

	for trip in driver_trips:
		trip_doc = frappe.get_doc("Delivery Trip", trip.name)
		trip_data = build_trip_data(trip_doc)
		trips_data.append(trip_data)

	return {
		"version": API_VERSION,
		"trips": trips_data
	}


def get_filters(email):
	return {
		"docstatus": 1,
		"driver": frappe.db.get_value("Driver", {"user_id": email}, "name"),
		"departure_time": ["BETWEEN", [add_days(getdate(nowdate()), -60), getdate(nowdate())]]
	}


def build_item_data(stop):
	if not stop.delivery_note:
		return []
	items_data = []
	dn_doc = frappe.get_doc("Delivery Note", stop.delivery_note)
	for item in dn_doc.items:
		items_data.append({
			"name": item.item_code,
			"qty": item.qty,
			"unitPrice": item.rate
		})
	return items_data


def build_stop_data(trip):
	stops_data = []
	for stop in trip.delivery_stops:
		stops_data.append({
			"name": stop.name,
			"visited": bool(stop.visited),
			"address": get_address_display_for_trip(stop.address),
			"customer": stop.customer,
			"amountToCollect": stop.grand_total,
			"deliveryNote": stop.delivery_note,
			"salesInvoice": stop.sales_invoice,
			"items": build_item_data(stop),
			"distance": stop.distance,
			"distanceUnit": stop.uom,
			"earliestDeliveryTime": stop.delivery_start_time,
			"latestDeliveryTime": stop.delivery_end_time,
			"estimatedArrival": stop.estimated_arrival,
			"customerPhoneNumber": frappe.db.get_value("Address", stop.address, "phone"),
		})
	return stops_data


def build_trip_data(trip):
	return {
		"name": trip.name,
		"status": trip.status,
		"vehicle": trip.vehicle,
		"company": trip.company,
		"stops": build_stop_data(trip)
	}