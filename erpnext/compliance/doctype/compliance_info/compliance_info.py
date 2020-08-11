# -*- coding: utf-8 -*-
# Copyright (c) 2019, Bloom Stack, Inc and contributors
# For license information, please see license.txt

import frappe
from erpnext.compliance.utils import get_default_license
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_link_to_form, getdate, nowdate, today


class ComplianceInfo(Document):
	pass


@frappe.whitelist()
def create_customer(source_name, target_doc=None):
	existing_customers = get_existing_licensees(source_name, "Customer")
	if existing_customers:
		customer_link = get_link_to_form("Customer", existing_customers[0])
		frappe.throw("A Customer already exists for this license - {0}".format(customer_link))

	customer = frappe.new_doc("Customer")
	customer.customer_name = frappe.db.get_value("Compliance Info", source_name, "legal_name")
	customer.append("licenses", {
		"license": source_name,
		"is_default": 1
	})

	return customer


@frappe.whitelist()
def create_supplier(source_name, target_doc=None):
	existing_suppliers = get_existing_licensees(source_name, "Supplier")
	if existing_suppliers:
		supplier_link = get_link_to_form("Supplier", existing_suppliers[0])
		frappe.throw("A Supplier already exists for this license - {0}".format(supplier_link))

	supplier = frappe.new_doc("Supplier")
	supplier.supplier_name = frappe.db.get_value("Compliance Info", source_name, "legal_name")
	supplier.append("licenses", {
		"license": source_name,
		"is_default": 1
	})

	return supplier


def get_existing_licensees(license_number, party_type):
	existing_licensees = frappe.get_all("Compliance License Detail",
		filters={"license": license_number, "parenttype": party_type},
		fields=["parent"],
		distinct=True)

	existing_licensees = [l.parent for l in existing_licensees if l.parent]
	return existing_licensees


def validate_license_expiry(doc):
	if doc.doctype in ("Sales Order", "Sales Invoice", "Delivery Note"):
		validate_entity_license("Customer", doc.customer)
	elif doc.doctype in ("Supplier Quotation", "Purchase Order", "Purchase Invoice", "Purchase Receipt"):
		validate_entity_license("Supplier", doc.supplier)
	elif doc.doctype == "Quotation" and doc.quotation_to == "Customer":
		validate_entity_license("Customer", doc.party_name)


@frappe.whitelist()
def validate_entity_license(party_type, party_name):
	license_record = get_default_license(party_type, party_name)
	if not license_record:
		return

	license_expiry_date, license_number = frappe.db.get_value(
		"Compliance Info", license_record, ["license_expiry_date", "license_number"])

	if not license_expiry_date:
		frappe.msgprint(_("We could not verify the status of license number {0}, Proceed with Caution.").format(
			frappe.bold(license_number)))
	elif license_expiry_date < getdate(nowdate()):
		frappe.msgprint(_("Our records indicate {0}'s license number {1} has expired on {2}, Proceed with Caution.").format(
			frappe.bold(party_name), frappe.bold(license_number), frappe.bold(license_expiry_date)))

	return license_record


def get_active_licenses(doctype, txt, searchfield, start, page_len, filters):
	return frappe.get_all(doctype,
		filters=[
			[doctype, "status", "!=", "Expired"],
			[doctype, "name", "NOT IN", filters.get("set_licenses")],
			[doctype, "name", "like", "%{0}%".format(txt)]
		],
		or_filters=[
			{"license_expiry_date": ["is", "not set"]},
			{"license_expiry_date": [">=", today()]}
		],
		fields=["name", "legal_name", "license_number", "status", "license_issuer",
			"license_for", "license_expiry_date", "license_type"],
		as_list=True)
