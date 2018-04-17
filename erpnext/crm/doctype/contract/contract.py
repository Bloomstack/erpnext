# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from frappe.model.document import Document
from frappe.utils import get_datetime, nowdate


class Contract(Document):
	def validate(self):
		self.update_status()

	def on_update_after_submit(self):
		self.update_status()

	def update_status(self):
		now_date = get_datetime(nowdate())
		start_date = get_datetime(self.start_date)
		end_date = get_datetime(self.end_date)

		if self.is_signed:
			status = "Active" if start_date < now_date < end_date else "Inactive"
		else:
			status = "Unsigned"

		self.status = status
