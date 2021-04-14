# -*- coding: utf-8 -*-
# Copyright (c) 2019, Bloom Stack, Inc and contributors
# For license information, please see license.txt

import frappe
import json
from erpnext.compliance.utils import get_default_license
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_link_to_form, getdate, nowdate, today, formatdate


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
		get_entity_license(doc, "Customer", doc.customer)
	elif doc.doctype in ("Supplier Quotation", "Purchase Order", "Purchase Invoice", "Purchase Receipt"):
		get_entity_license(doc, "Supplier", doc.supplier)
	elif doc.doctype == "Quotation" and doc.quotation_to == "Customer":
		get_entity_license(doc, "Customer", doc.party_name)


@frappe.whitelist()
def get_entity_license(doc, party_type, party_name):
	# get the default license for the given party
	license_record = get_default_license(party_type, party_name)
	if not license_record:
		return

	# show a warning if a license exists and is expired, and only if compliance items are present
	is_compliance = validate_doc_compliance(doc)
	if is_compliance:
		license_expiry_date, license_number = frappe.db.get_value(
			"Compliance Info", license_record, ["license_expiry_date", "license_number"])

		if not license_expiry_date:
			frappe.msgprint(_("We could not verify the status of license number {0}. Proceed with caution.").format(
				frappe.bold(license_number)))
		elif getdate(license_expiry_date) < getdate(nowdate()):
			frappe.msgprint(_("Our records indicate that the license number {0} has expired on {1}. Proceed with caution.").format(
				frappe.bold(license_number), frappe.bold(formatdate(license_expiry_date))))

	return license_record


def validate_doc_compliance(doc):
	"""Check if any compliance item available in the items table."""
	if isinstance(doc, str):
		doc = frappe._dict(json.loads(doc))

	is_compliance_item = False
	compliance_items = frappe.get_all('Item', filters={'is_compliance_item': True}, fields=['item_code'])
	if not compliance_items:
		return

	for item in (doc.get("items") or []):
		compliance_item = next((data for data in compliance_items if data.get("item_code") == item.get("item_code")), None)
		if compliance_item:
			is_compliance_item = True
	return is_compliance_item


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
