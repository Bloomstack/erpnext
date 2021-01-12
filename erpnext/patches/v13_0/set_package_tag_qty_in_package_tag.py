import frappe

def execute():
	frappe.reload_doc('compliance', 'doctype', 'package_tag', force=True)
	package_tags = frappe.get_all("Package Tag")

	for package_tag in package_tags:
		package_tag_qty = frappe.db.sql("""
			SELECT
				sum(actual_qty) as qty
			FROM
				`tabStock Ledger Entry` as sle
			WHERE
				sle.package_tag = (%s)
		""",(package_tag.name), as_dict=1)

		if package_tag_qty and package_tag_qty[0].qty:
			frappe.db.sql("""
				UPDATE
					`tabPackage Tag`
				SET
					package_tag_qty = %s
				WHERE
					name = %s
			""",(package_tag_qty[0].qty, package_tag.name))