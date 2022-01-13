import frappe
from frappe import _dict
from erpnext.shopping_cart.cart import get_party

def initialise_order_for():
	"""Initializes the "order for" feature which allows a backend user to use the
	shopping cart in behalf of another user"""

	cart_settings = frappe.get_single("Shopping Cart Settings")

	if not (cart_settings.enabled and cart_settings.allow_order_for):
		return

	# Initialize frappe.session.data.order_for
	frappe.session.data["order_for"] = _dict(frappe.session.data.get("order_for", {}))
	order_for = frappe.session.data.order_for

	if frappe.session.user in ("Guest", "Administrator"):
		return

	# Guard against customers set to order for which are removed after initializing
	if order_for.get("customer_name") and not frappe.db.exists("Customer", order_for.get("customer_name")):
		order_for.pop("customer_name", None)
		order_for.pop("customer_primary_contact_name", None)

	if not order_for.get("customer_name") and order_for.get("enabled"):
		order_for.pop("enabled", None)

	# Set default customer
	if not order_for.get("customer_name") and frappe.session.user not in ("Guest", "Administrator"):
		contact = frappe.get_doc("Contact", {"email_id": frappe.session.user})
		customer_links = []
		for link in contact.links:
			if link.link_doctype == "Customer" and frappe.db.exists(link.link_doctype, link.link_name):
				customer_links.append(link)

		if len(customer_links) == 1:
			order_for["customer_name"] = customer_links[0].link_name
			order_for["customer_primary_contact_name"] = contact.name

	# Keep customer info up to date on every session start
	customer = get_party(party_doctype="Customer", party=order_for.get("customer_name"))
	if customer and customer.doctype == "Customer":
		# no reason to set customer_name again as get_party expects
		# customer_name to exists to set user from the "order for" feature
		# otherwise vanilla path is executed and the true customer is returned.
		if order_for.get("customer_name"):
			order_for["customer_name"] = customer.name

		order_for["customer_group"] = customer.customer_group

