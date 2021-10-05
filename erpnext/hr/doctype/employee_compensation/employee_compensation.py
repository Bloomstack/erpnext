# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import today
from frappe.model.document import Document

class EmployeeCompensation(Document):
	def validate(self):
		self.validate_dates()

	def validate_dates(self):
		today_date = today()
		if self.date_of_injury and self.date_of_injury > today_date:
			frappe.throw(_("You cannot select a future date for Date of Injury."))
		if self.first_aid_date and self.first_aid_date > today_date:
			frappe.throw(_("You cannot select a future date for First Aid Date."))
		if self.first_aid_date and self.date_of_injury and self.first_aid_date < self.date_of_injury:
			frappe.throw(_("The First Aid date cannot be before the Date of Injury."))
