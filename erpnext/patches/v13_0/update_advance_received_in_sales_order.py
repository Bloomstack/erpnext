import frappe

def execute():
    frappe.reload_doc("selling", "doctype", "sales_order")
    docs = frappe.get_all("Sales Order", {
        "advance_paid": ["!=", 0]
    }, "name")
    for doc in docs:
        frappe.db.set_value("Sales Order", doc.name, "advance_received", 1, update_modified=False)