import frappe

def execute():
	"""
		Sets IS Used in Package Tag if there are SLEs
	"""
	frappe.reload_doc("compliance", "doctype", "package_tag")

	for package_tag in frappe.get_all("Package Tag"):
		if frappe.db.exists("Stock Ledger Entry", {"package_tag": package_tag.name}):
			frappe.db.set_value("Package Tag", package_tag.name, "is_used", 1)
