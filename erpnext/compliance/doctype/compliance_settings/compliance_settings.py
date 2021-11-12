# -*- coding: utf-8 -*-
# Copyright (c) 2020, Bloom Stack, Inc and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from erpnext.compliance.utils import get_bloomtrace_client

class ComplianceSettings(Document):
	def validate(self):
		self.validate_companies()
		self.sync_bloomtrace()

	def sync_bloomtrace(self):
		if not self.is_compliance_enabled:
			return

		frappe_client = get_bloomtrace_client()
		if not frappe_client:
			return

		site_url = frappe.utils.get_host_name()

		try:
			frappe_client.update({
				"doctype": "Bloomstack Site",
				"name": site_url,
				"metrc_user_key": self.get_password("metrc_user_key")
			})
		except Exception as e:
			frappe.log_error(e)

		for company in self.company:
			try:
				frappe_client.update({
					"doctype": "Bloomstack Company",
					"name": company.company,
					"push_item": company.push_item,
					"pull_item": company.pull_item,
					"push_package_tag": company.push_package_tag,
					"pull_package_tag": company.pull_package_tag,
					"pull_transfer": company.pull_transfer,
					"push_transfer": company.push_transfer,
					"pull_plant": company.pull_plant,
					"push_plant": company.push_plant,
					"pull_plant_batch": company.pull_plant_batch,
					"push_plant_batch": company.push_plant_batch,
					"pull_strain": company.pull_strain,
					"push_strain": company.push_strain,
					"pull_harvest": company.pull_harvest,
					"push_harvest": company.push_harvest,
					"pull_package": company.pull_package,
					"push_package": company.push_package
				})
			except Exception as e:
				frappe.log_error(e)

	def validate_companies(self):
		companies = []

		for company in self.company:
			if company.company not in companies:
				companies.append(company.company)
			else:
				frappe.throw(_("Company {0} already added to sync.").format(frappe.bold(company.company)))

	def on_update(self):
		frappe.clear_document_cache(self.doctype, self.name)
