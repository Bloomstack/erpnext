import frappe
from frappe import _


def get_context(context):
	context.no_cache = 1
	context.show_sidebar = True

	context.doc = frappe.get_doc(frappe.form_dict.doctype, frappe.form_dict.name)
	context.parents = frappe.form_dict.parents
	context.title = frappe.form_dict.name

	if not frappe.has_website_permission(context.doc):
		frappe.throw(_("Not Permitted"), frappe.PermissionError)
