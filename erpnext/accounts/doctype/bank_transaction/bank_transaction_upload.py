# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.utils import getdate
from frappe.utils.dateutils import parse_date
from six import iteritems
from frappe import _

@frappe.whitelist()
def upload_bank_statement():
	if getattr(frappe, "uploaded_file", None):
		with open(frappe.uploaded_file, "rb") as upfile:
			fcontent = upfile.read()
	else:
		fcontent = frappe.local.uploaded_file
		fname = frappe.local.uploaded_filename

	if frappe.safe_encode(fname).lower().endswith("csv".encode('utf-8')):
		from frappe.utils.csvutils import read_csv_content
		rows = read_csv_content(fcontent, False)

	elif frappe.safe_encode(fname).lower().endswith("xlsx".encode('utf-8')):
		from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
		rows = read_xlsx_file_from_attached_file(fcontent=fcontent)

	columns = rows[0]
	rows.pop(0)
	data = rows
	return {"columns": columns, "data": data}


@frappe.whitelist()
def create_bank_entries(columns, data, bank_account):
	bank_name = frappe.db.get_value("Bank Account", bank_account, "bank")
	bank = frappe.get_doc("Bank", bank_name)
	header_map = get_header_mapping(columns, bank)

	success = 0
	errors = 0
	total = len(json.loads(data))
	for idx, d in enumerate(json.loads(data)):
		if all(item is None for item in d) is True:
			continue
		fields = {}
		for key, value in iteritems(header_map):
			fields.update({
				key: get_value(d, key, bank, int(value)-1)
			})

		frappe.publish_progress(((idx+1)*100)/total, title=_("Importing Transactions"),description=_("Transaction {0} of {1}.").format(idx, total))

		try:
			bank_transaction = frappe.get_doc({
				"doctype": "Bank Transaction"
			})
			bank_transaction.update(fields)
			bank_transaction.date = getdate(parse_date(bank_transaction.date))
			bank_transaction.bank_account = bank_account
			bank_transaction.insert()
			bank_transaction.submit()
			success += 1
		except Exception:
			frappe.log_error(frappe.get_traceback())
			errors += 1

	return {"success": success, "errors": errors}

def get_value(data, key, bank, index):
	if not bank.is_single_column_import or key not in ["debit", "credit"]:
		return data[index]

	if key == "debit" and float(data[index]) >= 0:
		return data[index]
	elif key == "credit" and float(data[index]) < 0:
		return abs(float(data[index]))
	else:
		return None

def get_header_mapping(columns, bank):
	mapping = get_bank_mapping(bank)

	header_map = {}
	for column in json.loads(columns):
		if column["content"] in mapping:
			header_map.update({mapping[column["content"]]: column["colIndex"]})

	return header_map

def get_bank_mapping(bank):
	mapping = {row.file_field:row.bank_transaction_field for row in bank.bank_transaction_mapping}

	return mapping
