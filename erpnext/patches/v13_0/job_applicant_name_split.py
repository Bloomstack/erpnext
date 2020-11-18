import frappe


def execute():
	frappe.reload_doc("hr", "doctype", "job_applicant")
	applicant_list = frappe.get_all("Job Applicant",fields=["name", "applicant_name"])
	for applicant in applicant_list:
		splitted_name = applicant.applicant_name.split(" ")
		frappe.db.set_value("Job Applicant", applicant.name, {
			"first_name": splitted_name[0],
			"last_name": splitted_name[-1]
		}, update_modified=False)
