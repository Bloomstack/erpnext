# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
import frappe.defaults
from erpnext.shopping_cart.doctype.shopping_cart_settings.shopping_cart_settings import is_cart_enabled
from frappe.utils import cint

def show_cart_count():
	if (is_cart_enabled() and
		frappe.db.get_value("User", frappe.session.user, "user_type") == "Website User"):
		return True

	return False

def set_cart_count(login_manager):
	role, parties = check_customer_or_supplier()
	if role == 'Supplier': return
	if show_cart_count():
		from erpnext.shopping_cart.cart import set_cart_count
		set_cart_count()

def clear_cart_count(login_manager):
	if show_cart_count() and hasattr(frappe.local, "cookie_manager"):
		frappe.local.cookie_manager.delete_cookie("cart_count")

def update_website_context(context):
	cart_enabled = is_cart_enabled()
	shopping_cart_count = 0
	if hasattr(frappe.local, "cookie_manager"):
		shopping_cart_count = cint(frappe.local.cookie_manager.cookies.get("cart_count", 0))

	context.update({
		"shopping_cart_enabled": cart_enabled,
		"shopping_cart_show_count": show_cart_count(),
		"shopping_cart_count": shopping_cart_count
	})

	# Order for feature:
	if "order_for" in frappe.session.data:

		#create a global context variable which is a bool flag for the order_for feature
		context.update({
			"order_for": frappe.session.data.order_for.get('enabled', False)
		})
		customer_name = frappe.session.data.order_for.get("customer_name")
	
		if customer_name:
			customer = frappe.get_doc("Customer", customer_name)
			primary_contact = frappe.session.data.order_for.get("customer_primary_contact_name")

			context.update({
				"session_customer": customer, 
				"customer_name": customer_name
			})

			if primary_contact and frappe.db.exists("Contact", primary_contact):
				contact = frappe.get_doc("Contact", primary_contact)
				context.update({"session_customer_primary_contact": contact})
					
def check_customer_or_supplier():
	if frappe.session.user:
		contact_name = frappe.get_value("Contact", {"email_id": frappe.session.user})
		if contact_name:
			contact = frappe.get_doc('Contact', contact_name)
			for link in contact.links:
				if link.link_doctype in ('Customer', 'Supplier'):
					return link.link_doctype, link.link_name

		return 'Customer', None