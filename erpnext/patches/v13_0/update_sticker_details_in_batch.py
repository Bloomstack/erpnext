
import frappe
from erpnext.stock.doctype.batch.batch import update_batch_doc

def execute():
	frappe.reload_doc("stock", "doctype", "quality_inspection")
	frappe.reload_doc("stock", "doctype", "batch")
	quality_inspection = frappe.get_all("Quality Inspection", filters={"docstatus": 1}, fields=["name", "item_code", "batch_no", "thc", "cbd"])
	for qi in quality_inspection:
		if qi.thc or qi.cbd:
			update_batch_doc(qi.batch_no, qi.name, qi.item_code)
