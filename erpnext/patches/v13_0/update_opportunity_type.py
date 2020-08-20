from __future__ import unicode_literals
import frappe
def execute():
	names = frappe.db.get_list('Opportunity Type','name')
	for item in names:
		if item.get("name") == "Investor":
			return
	doc = frappe.new_doc("Opportunity Type")
	doc.update({
		"name": "Investor"
	})
	doc.save()
