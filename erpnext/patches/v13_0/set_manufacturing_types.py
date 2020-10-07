import frappe


def execute():
	frappe.reload_doc("manufacturing", "doctype", "bom", force=True)
	frappe.reload_doc("manufacturing", "doctype", "work_order", force=True)
	frappe.reload_doc("stock", "doctype", "stock_entry", force=True)

	for dt in ('BOM', 'Work Order', 'Stock Entry'):
		frappe.db.sql("""
			UPDATE
				`tab%s`
			SET
				manufacturing_type = "Discrete"
			WHERE
				manufacturing_type IS NULL
		""" % (dt))
