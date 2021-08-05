# Copyright (c) 2017, Frappe and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

def execute():
	frappe.reload_doc('projects', 'doctype', 'task', force=True)

	frappe.db.sql(
		"""
		UPDATE 
			`tabTask` 
		SET 
			status = "Closed" 
		WHERE
			status in ('Cancelled', 'Canceled')
		"""
	)
