import frappe

def execute():
	frappe.reload_doc("manufacturing", "doctype", "BOM", force=1)
	frappe.reload_doc("manufacturing", "doctype", "Work Order")
	frappe.reload_doc("stock", "doctype", "Stock Entry")
	for dt in ('BOM', 'Work Order', 'Stock Entry'):
		frappe.db.sql("""
			UPDATE
				`tab%s`
			SET
				manufacturing_type = "Discrete"
			WHERE
				manufacturing_type IS NULL
		"""% (dt))
