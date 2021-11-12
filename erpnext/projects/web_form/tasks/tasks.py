from __future__ import unicode_literals

import frappe

def get_context(context):
	if frappe.form_dict.default_project:
		context.parents = [{'title': frappe.form_dict.default_project, 'route': '/projects?project='+ frappe.form_dict.default_project}]
		context.success_url = "/projects?project=" + frappe.form_dict.default_project
		
	elif context.doc and context.doc.get('default_project'):
		context.parents = [{'title': context.doc.default_project, 'route': '/projects?project='+ context.doc.default_project}]
		context.success_url = "/projects?project=" + context.doc.default_project
