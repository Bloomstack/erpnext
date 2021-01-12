# Copyright (c) 2018, Frappe and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

def execute():
	if frappe.db.table_exists("Bank Reconciliation"):
		frappe.rename_doc('DocType', 'Bank Reconciliation', 'Bank Clearance', force=True)
		frappe.reload_doc('Accounts', 'doctype', 'Bank Clearance')

		frappe.rename_doc('DocType', 'Bank Reconciliation Detail', 'Bank Clearance Detail', force=True)
		frappe.reload_doc('Accounts', 'doctype', 'Bank Clearance Detail')

	_rename_single_field(doctype = "Bank Clearance", old_name = "bank_account" , new_name = "account")
	_rename_single_field(doctype = "Bank Clearance", old_name = "bank_account_no", new_name = "bank_account")

def _rename_single_field(**kwargs):
	count = frappe.db.sql("SELECT COUNT(*) FROM tabSingles WHERE doctype='{doctype}' AND field='{new_name}';".format(**kwargs))[0][0] #nosec
	if count == 0:
		frappe.db.sql("UPDATE tabSingles SET field='{new_name}' WHERE doctype='{doctype}' AND field='{old_name}';".format(**kwargs)) #nosec