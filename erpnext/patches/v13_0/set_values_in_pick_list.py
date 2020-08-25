import frappe


def execute():
	frappe.reload_doc("stock", "doctype", "pick_list")
	pick_lists = frappe.get_all("Pick List", filters={"purpose": "Delivery"}, fields=["name", "customer"])

	for pick_list in pick_lists:
		# set a delivery date in each Pick List based on sales orders
		sales_orders = frappe.get_all("Pick List Item",
			filters={"parent": pick_list.name},
			fields=["sales_order"],
			distinct=True)

		order_delivery_dates = []
		for sales_order in sales_orders:
			if sales_order.sales_order:
				delivery_dates = frappe.get_all("Sales Order Item", {"parent": sales_order.sales_order}, "delivery_date")
				order_delivery_dates = [delivery.delivery_date for delivery in delivery_dates if delivery.delivery_date]

		if order_delivery_dates:
			frappe.db.set_value("Pick List", pick_list.name, "delivery_date", min(order_delivery_dates), update_modified=False)

		# set the customer name in each Pick List
		customer = None
		if pick_list.customer:
			customer_name = frappe.db.get_value("Customer", pick_list.customer, "customer_name")
		else:
			for sales_order in sales_orders:
				if sales_order.sales_order:
					customer_name = frappe.db.get_value("Sales Order", sales_order.sales_order, "customer_name")
					break

		if customer_name:
			frappe.db.set_value("Pick List", pick_list.name, "customer_name", customer_name, update_modified=False)
