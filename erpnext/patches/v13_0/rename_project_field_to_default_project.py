from __future__ import unicode_literals
import frappe
from frappe.model.utils.rename_field import rename_field

def execute():
	frappe.reload_doctype("Task")
	rename_field("Task", "project", "default_project")