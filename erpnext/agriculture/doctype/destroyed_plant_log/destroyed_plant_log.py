# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class DestroyedPlantLog(Document):
	def on_submit(self):
		doc = frappe.get_doc('Plant Batch',self.plant_batch)
		if doc.untracked_count == 0:
			frappe.throw(_("The plant batch must have an untracked count"))
		elif int(self.destroy_count) <= 0:
			frappe.throw(_("Destroy count cannot be less than 0"))
		elif doc.untracked_count < int(self.destroy_count):
			frappe.throw(_("The destroyed plant count ({0}) should be less than or equal to the untracked count ({1})").format(self.destroy_count, doc.untracked_count))
		else:
			doc.untracked_count = doc.untracked_count - int(self.destroy_count)
			doc.destroyed_count = doc.destroyed_count + int(self.destroy_count)
			doc.save()