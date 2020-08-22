import frappe
def execute():
	frappe.reload_doctype("Pick List")
	pick_lists= frappe.get_all("Pick List",filters= {
		"purpose": "Delivery"
	}, fields= ["name","customer"])
	for pick_list in pick_lists:
		order_delivery_date = []
		sales_order = frappe.get_value("Pick List Item",{"parent": pick_list.name}, "sales_order")
		if sales_order:
			delivery_dates = frappe.get_all("Sales Order Item", {"parent": sales_order}, "delivery_date")
			for delivery in delivery_dates:
				order_delivery_date.append(frappe.db.get_value("Sales Order Item", {"parent": sales_order}, "delivery_date"))
			frappe.db.set_value("Pick List", pick_list.name, "delivery_date", min(order_delivery_date), update_modified=False)
			frappe.db.set_value("Pick List", pick_list.name, "customer_name", pick_list.customer, update_modified=False)