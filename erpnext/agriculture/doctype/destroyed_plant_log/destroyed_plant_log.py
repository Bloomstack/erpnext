# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class DestroyedPlantLog(Document):
	def on_submit(self):
		doc = frappe.get_doc('Plant Batch', self.plant_batch)
		doc.validate_plant_batch_quantities(self.destroy_count)
		doc.untracked_count -= int(self.destroy_count)
		doc.destroyed_count += int(self.destroy_count)
		doc.save()