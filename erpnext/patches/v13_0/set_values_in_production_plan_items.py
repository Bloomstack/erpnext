import frappe
from erpnext.manufacturing.doctype.production_plan.production_plan import get_item_data


def execute():
	frappe.reload_doctype("Production Plan Item")
	production_plans = frappe.get_all("Production Plan Item", fields=["name", "item_code"])

	for production_plan in production_plans:
		try:
			# handle case where an item doesn't have a default BOM
			data = get_item_data(production_plan.item_code)
		except frappe.ValidationError:
			continue
		else:
			frappe.db.set_value("Production Plan Item", production_plan.name, "raw_material_cost", data.get(
				"raw_material_cost"), update_modified=False)
			frappe.db.set_value("Production Plan Item", production_plan.name, "total_operational_cost", data.get(
				"total_operational_cost"), update_modified=False)
			frappe.db.set_value("Production Plan Item", production_plan.name, "total_operational_hours", data.get(
				"total_operational_hours"), update_modified=False)
			frappe.db.set_value("Production Plan Item", production_plan.name, "total_workstations", data.get(
				"total_workstations"), update_modified=False)
