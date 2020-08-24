import frappe


def execute():
	# delete existing custom fields
	frappe.delete_doc('Custom Field', "Delivery Note-license")

	frappe.delete_doc('Custom Field', "Delivery Stop-paid_amount")
	frappe.delete_doc('Custom Field', "Delivery Stop-make_payment_entry")
	frappe.delete_doc('Custom Field', "Delivery Stop-sales_invoice")

	frappe.delete_doc("Custom Field", "Delivery Trip-odometer")
	frappe.delete_doc("Custom Field", "Delivery Trip-odometer_start_value")
	frappe.delete_doc("Custom Field", "Delivery Trip-odometer_start_time")
	frappe.delete_doc("Custom Field", "Delivery Trip-actual_distance_travelled")
	frappe.delete_doc("Custom Field", "Delivery Trip-column_break_17")
	frappe.delete_doc("Custom Field", "Delivery Trip-odometer_end_value")
	frappe.delete_doc("Custom Field", "Delivery Trip-odometer_end_time")
	frappe.delete_doc("Custom Field", "Delivery Trip-sb_map")
	frappe.delete_doc("Custom Field", "Delivery Trip-map_html")
	frappe.delete_doc("Custom Field", "Delivery Trip-map_embed")

	# reload doctypes with new changes
	frappe.reload_doc("stock", "doctype", "delivery_note", force=True)
	frappe.reload_doc("stock", "doctype", "delivery_trip", force=True)
	frappe.reload_doc("stock", "doctype", "delivery_stop", force=True)

	# reset status on existing delivery notes
	stops = frappe.get_all("Delivery Stop", fields=["visited", "sales_invoice", "delivery_note", "parent"])
	for stop in stops:
		if stop.delivery_note:
			if stop.visited and stop.sales_invoice:
				si_status = frappe.db.get_value("Sales Invoice", stop.sales_invoice, "status")
				if si_status == "Paid":
					frappe.db.set_value("Delivery Note", stop.delivery_note, {
						"delivered": 1,
						"status": "Completed"
					}, update_modified=False)
				elif si_status == "Unpaid":
					frappe.db.set_value("Delivery Note", stop.delivery_note, {
						"delivered": 1,
						"status": "Delivered"
					}, update_modified=False)
			else:
				dt_status = frappe.db.get_value("Delivery Trip", stop.parent, "status")
				if dt_status == "In Transit":
					frappe.db.set_value("Delivery Note", stop.delivery_note, {
						"delivered": 0,
						"status": "Out for Delivery"
					}, update_modified=False)
