import frappe

def execute():
    stock_settings = frappe.get_doc('Stock Settings')
    if not (stock_settings.valuation_method):
        stock_settings.valuation_method = 'FIFO'
    stock_settings.save()

    #Updating valuation method for exisitng items
    frappe.reload_doc("stock", "doctype", "item")
    frappe.db.sql("""
        UPDATE `tabItem`
        SET
            valuation_method = 'FIFO'
        WHERE valuation_method = ''
	""")