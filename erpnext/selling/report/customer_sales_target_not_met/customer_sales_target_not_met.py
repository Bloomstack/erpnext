# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe import _
import frappe

def execute(filters=None):
	columns=get_columns(filters)

	data = get_data(filters)

	return columns, data

def get_columns(filters):
	return [
        _("Customer") + ":Link/Customer:150",
		_("Monthly Sales Target") + ":currency:150",
		_("Total Monthly Salest") + ":currency:150"
        ]

def get_data(filters= None):
	return frappe.db.sql("""
            SELECT
                customer_name,monthly_sales_target,total_monthly_sales
            FROM
                tabCustomer
    		WHERE 
				monthly_sales_target > total_monthly_sales
				""")
				