import frappe

def execute():
    notes = frappe.get_all("Delivery Note" , fields=["name", "delivered", "status"])
    stops = frappe.get_all("Delivery Stop", fields=["visited", "sales_invoice", "delivery_note", "parent"])
    for stop in stops:
        if stop.visited:
            for note in notes:
                if stop.delivery_note == note.name:
                    si_status = frappe.db.get_value("Sales Invoice", stop.sales_invoice, "status")
                    if si_status == "Paid":
                        frappe.db.set_value("Delivery Note", note.name ,{
                            "delivered" : 1,
                            "status" : "Completed"
                        }, update_modified=False)
                    if si_status == "Unpaid":
                        frappe.db.set_value("Delivery Note", note.name ,{
                            "delivered" : 1,
                            "status" : "Delivered"
                        }, update_modified=False)
        else:
             for note in notes:
                if stop.delivery_note == note.name:
                    dt_status = frappe.db.get_value("Delivery Trip", stop.parent, "status")
                    if dt_status == "In Transit":
                        frappe.db.set_value("Delivery Note", note.name ,{
                            "delivered" : 0,
                            "status" : "Out for Delivery"
                        }, update_modified=False)

