# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from awesome_cart.compat.customer import get_current_customer
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, now_datetime


class Contract(Document):
	def validate(self):
		self.validate_dates()
		self.update_status()

	def on_update_after_submit(self):
		self.update_status()

	def validate_dates(self):
		if self.end_date < self.start_date:
			frappe.throw("End Date cannot be before Start Date!")

	def update_status(self):
		if self.is_signed:
			self.status = get_status(self.start_date, self.end_date)
		else:
			self.status = "Unsigned"

	def has_website_permission(self, doc, ptype, user, verbose=False):
		"""
		Returns `True` if the contract party name matches
		with the logged in user/customer
		"""

		customer = get_current_customer()

		if customer:
			return doc.party_name == customer.name


def get_status(start_date, end_date):
	if not end_date:
		return "Active"

	now_date = getdate(nowdate())
	status = "Active" if start_date < now_date < end_date else "Inactive"

	return status


def update_status_for_contracts():
	contracts = frappe.get_all("Contract", filters={"is_signed": True, "docstatus": 1}, fields=["name", "start_date", "end_date"])

	for contract in contracts:
		status = get_status(contract.get("start_date"),
							contract.get("end_date"))

		frappe.db.set_value("Contract", contract.get("name"), "status", status)


def get_list_context(context=None):
	from erpnext.controllers.website_list_for_contact import get_list_context

	list_context = get_list_context(context)
	list_context.update({
		'show_sidebar': True,
		'show_search': True,
		'no_breadcrumbs': True,
		"row_template": "templates/includes/contract_row.html",
		'get_list': get_contract_list,
		'title': _("Contracts")
	})

	return list_context


def get_contract_list(doctype, txt, filters, limit_start, limit_page_length=20, order_by=None):
	from frappe.www.list import get_list

	user = frappe.session.user
	ignore_permissions = False

	if not filters:
		filters = []

	if user != "Guest":
		customer = get_current_customer()

		if customer:
			filters.append(("Contract", "party_name", "=", customer.name))
			ignore_permissions = True

	return get_list(doctype, txt, filters, limit_start, limit_page_length, ignore_permissions=ignore_permissions)


# TODO: Placeholder for digitally signing contracts,
# when we make a corresponding workflow
@frappe.whitelist()
def accept_contract_terms(dn, signee):
	contract = frappe.get_doc("Contract", dn)
	contract.is_signed = True
	contract.signee = signee
	contract.signed_on = now_datetime()
	contract.flags.ignore_permissions = True
	contract.save()
	frappe.db.commit()
