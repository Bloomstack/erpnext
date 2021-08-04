# Copyright (c) 2017, Frappe and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

def execute():
	frappe.reload_doc('projects', 'doctype', 'task')

	frappe.db.sql(
		"""
		UPDATE `tabTask`
			SET status = CASE
				WHEN status = 'Cancelled' or status = 'Canceled' THEN 'Closed'
			END
		"""
	)
