# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, getdate
from erpnext.agriculture.doctype.plant_batch.plant_batch import validate_quantities

class DestroyedPlantLog(Document):
	def on_submit(self):
		if self.category_type == "Plant Batch":
			doc = frappe.get_doc('Plant Batch', self.category)
			validate_quantities(doc, self.destroy_count)
		elif self.category_type == "Plant":
			doc = frappe.get_doc('Plant', self.category)
			validate_quantities(doc, self.destroy_count)
		if not self.actual_date:
			self.actual_date = getdate(nowdate())
		doc.untracked_count -= int(self.destroy_count)
		doc.destroyed_count += int(self.destroy_count)
		doc.save()