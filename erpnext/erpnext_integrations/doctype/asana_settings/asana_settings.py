# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import asana
from datetime import datetime
from frappe.model.document import Document
from frappe import _
from frappe.utils.password import get_decrypted_password

class AsanaSettings(Document):
	def validate(self):
		self.authorize()

	def authorize(self):
		"""Authenticate the token and return asana_settings client"""
		if self.enable and not self.personal_access_token:
			frappe.throw(_("Personal Access Token is mandatory if Asana Integration is enabled."))
		try:
			client = asana.Client.access_token(get_decrypted_password("Asana Settings", "Asana Settings", "personal_access_token"))
			return client
		except Exception as e:
			frappe.throw(_("Error while connecting to Asana Client."))

	def get_workspaces(self):
		client = self.authorize()
		asana_workspaces = client.workspaces.find_all()
		return asana_workspaces
		
