import frappe

def execute():
	frappe.reload_doc('stock', 'doctype', 'batch', force=True)
	batches = frappe.get_all("Batch")

	for batch in batches:
		batch_qty = frappe.db.sql("""
			SELECT
				sum(actual_qty) as qty
			FROM
				`tabStock Ledger Entry` as sle
			WHERE
				sle.batch_no = (%s)
		""",(batch.name), as_dict=1)

		if batch_qty and batch_qty[0].qty:
			frappe.db.sql("""
				UPDATE
					`tabBatch`
				SET
					batch_qty = %s
				WHERE
					name = %s
			""",(batch_qty[0].qty, batch.name))