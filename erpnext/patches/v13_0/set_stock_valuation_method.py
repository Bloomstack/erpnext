import frappe

def execute():
    stock_settings = frappe.get_doc('Stock Settings')
    if not (stock_settings.valuation_method):
        stock_settings.valuation_method = 'FIFO'
    stock_settings.save()