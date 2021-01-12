import frappe
from erpnext.shopping_cart.doctype.shopping_cart_settings.shopping_cart_settings import get_shopping_cart_settings

@frappe.whitelist(allow_guest=False)
def set_website_customer(customer_name, primary_contact=None):

	# Find primary contact of this customer if one is not passed
	if not primary_contact:
		primary_contact = find_customer_primary_contact(customer_name)

	# Avoid storing a missing contact name
	if not frappe.db.exists("Contact", primary_contact):
		primary_contact = None

	# make sure customer has at least a contact
	if not primary_contact:
		return "Customer does not have a primary contact. Please set one before starting an order."

	#flag for checking if the order_for feature is enabled
	frappe.session.data.order_for['enabled'] = True
	frappe.session.data.order_for["customer_name"] = customer_name
	frappe.session.data.order_for["customer_primary_contact_name"] = primary_contact

	return "Success"

@frappe.whitelist(allow_guest=True)
def reset_website_customer():
	settings = get_shopping_cart_settings()

	#flag order_for feature as disabled if stopped by the sales team user
	frappe.session.data.order_for['enabled'] = False

	customer_name = frappe.session.data.order_for.get("customer_name")	
	if frappe.session.data.order_for.get("customer_name"):
		del frappe.session.data.order_for["customer_name"]
	if frappe.session.data.order_for.get("customer_primary_contact_name"):
		del frappe.session.data.order_for["customer_primary_contact_name"]

	if settings.get("stop_order_for_behavior") == "Reload":
		url = "Reload"
	if settings.get("stop_order_for_behavior") == "Back to Customer Record" and customer_name:
		url = "/desk#Form/Customer/{}".format(customer_name)
	else:
		url = settings.get("stop_order_for_url", "") or "Reload"

	# Hook: Allows overriding the routing url after a user resets the website customer
	#
	# Signature:
	#       override_stop_order_for_url(url)
	#
	# Args:
	#		url: The current route
	#
	# Returns:
	#		Hook expects a string or None to override the route
	hooks = frappe.get_hooks("override_stop_order_for_url") or []
	for method in hooks:
		url = frappe.call(method, url=url) or url

	if not url:
		url = "Reload"

	return url

def find_customer_primary_contact(customer_name):
	primary_contact = frappe.get_value("Customer", customer_name, "customer_primary_contact")

	if not primary_contact:
		contacts = find_parent_dynamic_links("Contact", "links", "Customer", customer_name)
		for contact in contacts:
			is_primary = frappe.get_value("Contact", contact, "is_primary_contact")
			if is_primary:
				primary_contact = contact
				break
		
		if not primary_contact and len(contacts) > 0:
			primary_contact = contacts[0]

	return primary_contact

def find_parent_dynamic_links(parent_dt, parent_field, link_dt, link_dn):
	return [r[0] for r in frappe.get_all("Dynamic Link", filters={
		"parenttype": parent_dt, 
		"parentfield": parent_field,
		"link_doctype": link_dt, 
		"link_name": link_dn
	}, 
	fields=['parent'],
	as_list=1)]