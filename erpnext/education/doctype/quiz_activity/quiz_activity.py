# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class QuizActivity(Document):
	def on_submit(self):
		if self.status=="Pass":
			activity = frappe.get_doc({
				"doctype": "Course Activity",
				"enrollment": self.enrollment,
				"content_type": "Quiz",
				"content": self.quiz,
				"activity_date": frappe.utils.now_datetime()
			})
			activity.insert(ignore_permissions=True)
