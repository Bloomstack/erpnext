# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.contacts.address_and_contact import load_address_and_contact
from erpnext.accounts.party import validate_party_accounts, get_dashboard_info, get_timeline_data  # keep this


class Investor(Document):
	def onload(self):
		"""Load address and contacts in `__onload`"""
		load_address_and_contact(self)

	def after_insert(self):
		self.update_lead_status()

	def on_update(self):
		if self.flags.old_lead != self.party_name:
			self.update_lead_status()
		if self.investor_from == "Lead" and self.party_name:
			self.create_lead_address()
			self.create_lead_contact()
		if self.investor_from == "Opportunity" and self.party_name:
			self.create_opportunity_address()
			self.create_opportunity_contact()

	def update_lead_status(self):
		'''If Investor created from Lead, update lead status to "Investor"'''
		if self.investor_from == "Lead" and self.party_name:
			frappe.db.set_value('Lead', self.party_name, 'status', 'Investor', update_modified=False)

	def create_lead_address(self):
		# assign lead address to investor (if already not set)
		address_names = frappe.get_all('Dynamic Link', filters={
			"parenttype": "Address",
			"link_doctype": "Lead",
			"link_name": self.party_name
		}, fields=["parent as name"])

		for address_name in address_names:
			address = frappe.get_doc('Address', address_name.get('name'))
			if not address.has_link('Investor', self.name):
				address.append('links', dict(link_doctype='Investor', link_name=self.name))
				address.save()

	def create_lead_contact(self):
		# assign lead contact to investor (if already not set)
		contact_names = frappe.get_all('Dynamic Link', filters={
			"parenttype": "Contact",
			"link_doctype": "Lead",
			"link_name": self.party_name
		}, fields=["parent as name"])

		for contact_name in contact_names:
			contact = frappe.get_doc('Contact', contact_name.get('name'))
			if not contact.has_link('Investor', self.name):
				contact.append('links', dict(link_doctype='Investor', link_name=self.name))
				contact.save()

	def create_opportunity_address(self):
		customer_address = frappe.db.get_value("Opportunity", self.party_name, "customer_address")

		if customer_address:
			address = frappe.get_doc('Address', customer_address)
			if not address.has_link('Investor', self.name):
				address.append('links', dict(link_doctype='Investor', link_name=self.name))
				address.save()

	def create_opportunity_contact(self):
		contact_person = frappe.db.get_value("Opportunity", self.party_name, "contact_person")

		if contact_person:
			contact = frappe.get_doc('Contact', contact_person)
			if not contact.has_link('Investor', self.name):
				contact.append('links', dict(link_doctype='Investor', link_name=self.name))
				contact.save()
