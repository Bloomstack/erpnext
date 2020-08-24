import frappe
def execute():
	frappe.reload_doc("stock", "doctype", "pick_list")
	pick_lists= frappe.get_all("Pick List",filters= {
		"purpose": "Delivery"
	}, fields= ["name","customer"])
	for pick_list in pick_lists:
		order_delivery_date = []
		sales_orders = frappe.get_all("Pick List Item", filters={"parent": pick_list.name}, fields=["sales_order"], distinct=True)
		for sales_order in sales_orders:
			if sales_order.sales_order:
				delivery_dates = frappe.get_all("Sales Order Item", {"parent": sales_order.sales_order}, "delivery_date")
				for delivery in delivery_dates:
					order_delivery_date.append(delivery.delivery_date)
		if order_delivery_date:
			frappe.db.set_value("Pick List", pick_list.name, "delivery_date", min(order_delivery_date), update_modified=False)
		frappe.db.set_value("Pick List", pick_list.name, "customer_name", pick_list.customer, update_modified=False)