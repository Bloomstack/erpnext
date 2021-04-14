import frappe

def execute():
    """
    Set coa batch value in batch document if batch and coa batch is set in package tag
    """
    frappe.reload_doc("stock", "doctype", "batch")
    package_tags = frappe.get_all("Package Tag",
        filters = {'batch_no': ["is", "set"], "coa_batch_no": ["is", "set"]},
        fields = ['batch_no', "coa_batch_no"])
    for tag in package_tags:
        frappe.db.set_value("Batch", tag.batch_no, "coa_batch", tag.coa_batch)