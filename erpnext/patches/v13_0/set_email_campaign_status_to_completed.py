import frappe

def execute():
	email_campaigns = frappe.get_all("Email Campaign", {"status": "Unsubscribed"})
	for email_campaign in email_campaigns:
		frappe.db.set_value("Email Campaign", email_campaign.name, "status", "Completed")
