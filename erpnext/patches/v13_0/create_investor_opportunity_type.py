from __future__ import unicode_literals
import frappe
def execute():
	if frappe.db.exists("Opportunity Type", "Investor"):
		return
	doc = frappe.new_doc("Opportunity Type")
	doc.update({
		"name": "Investor"
	})
	doc.save()
