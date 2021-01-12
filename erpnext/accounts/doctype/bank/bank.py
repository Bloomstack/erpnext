# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Bank(Document):

	def validate(self):
		credit_column = None
		debit_column = None

		for mapping in self.bank_transaction_mapping:
			if mapping.bank_transaction_field == "debit":
				debit_column = mapping.file_field
			elif mapping.bank_transaction_field == "credit":
				credit_column = mapping.file_field

		self.is_single_column_import = True if credit_column == debit_column else False
