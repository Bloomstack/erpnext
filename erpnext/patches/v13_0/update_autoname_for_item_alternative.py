import frappe

def execute():
    # Update the name of all Item Alternative.
    frappe.reload_doc('stock', 'doctype', 'item_alternative')
    frappe.db.sql("""UPDATE `tabItem Alternative` set name=alternative_item_code""")
