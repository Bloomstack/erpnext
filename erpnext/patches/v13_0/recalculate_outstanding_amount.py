import frappe

def execute():
	payment_references = frappe.get_all("Payment Entry Reference", filters={"docstatus": 1}, fields=["*"])
	reference_documents = {}

	for payment_reference in payment_references:
		if payment_reference.reference_name in reference_documents:
			reference_documents[payment_reference.reference_name] += [payment_reference]
		else:
			reference_documents[payment_reference.reference_name] = [payment_reference]

	for key in reference_documents:
		if len(reference_documents[key]) > 1:
			reference_documents[key].sort(key=sort)

		set_outstanding(reference_documents[key])

def sort(e):
	return e["modified"]

def set_outstanding(documents):
	total_amount = documents[0].total_amount

	for document in documents:
		total_amount -= document.allocated_amount
		frappe.db.set_value("Payment Entry Reference", document.name, "outstanding_amount", total_amount, update_modified=False)
