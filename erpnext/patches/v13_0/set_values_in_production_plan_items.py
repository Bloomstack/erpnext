import frappe
from erpnext.manufacturing.doctype.production_plan.production_plan import get_item_data


def execute():
    frappe.reload_doctype("Production Plan Item")
    production_plans = frappe.get_all("Production Plan Item", fields=["name", "item_code","bom_no"])
    for production_plan in production_plans:
        if production_plan.get("bom_no"):
            data = get_item_data(production_plan.item_code)
            frappe.db.set_value("Production Plan Item", production_plan.name, "raw_material_cost", data.get("raw_material_cost"), update_modified=False)
            frappe.db.set_value("Production Plan Item", production_plan.name, "total_operational_cost", data.get("total_operational_cost"), update_modified=False)
            frappe.db.set_value("Production Plan Item", production_plan.name, "total_operational_hours", data.get("total_operational_hours"), update_modified=False)
            frappe.db.set_value("Production Plan Item", production_plan.name, "total_workstations", data.get("total_workstations"), update_modified=False)
            