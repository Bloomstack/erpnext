# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Driver(Document):
	def validate(self):
		self.get_employee_from_user()

	def get_employee_from_user(self):
		if self.user_id:
			employee = frappe.db.get_value("Employee", {"user_id": self.user_id})
			if employee:
				self.employee = employee
