import frappe

def execute():
	# Default existing coupons to enabled
	frappe.reload_doc("accounts", "doctype", "coupon_code", force=1)
	frappe.db.sql("UPDATE `tabCoupon Code` SET enabled = 1")
