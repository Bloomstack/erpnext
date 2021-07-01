from __future__ import unicode_literals
from frappe import _


def get_data():
	return [
		{
			"label": _("Financial Reports"),
			"icon": "fa fa-star",
			"items": [{
				"type": "report",
				"name": "Trial Balance",
				"doctype": "GL Entry",
				"is_query_report": True,
			},
			{
				"type": "report",
				"name": "Profit and Loss Statement",
				"doctype": "GL Entry",
				"is_query_report": True
			},
			{
				"type": "report",
				"name": "Balance Sheet",
				"doctype": "GL Entry",
				"is_query_report": True
			},
			{
				"type": "report",
				"name": "Cash Flow",
				"label": _("Cash Flow Statement"),
				"doctype": "GL Entry",
				"is_query_report": True
			},
			{
				"type": "report",
				"name": "Cost Center Financial Statements",
				"doctype": "GL Entry",
				"is_query_report": True
			},
			{
				"type": "report",
				"label": _("Consolidated Financial Statements"),
				"name": "Consolidated Financial Statement",
				"doctype": "GL Entry",
				"is_query_report": True
			}]
		},
		{
			"label": _("Recievables and Payables Reports"),
			"icon": "fa fa-star",
			"items": [{
				"type": "report",
				"name": "Accounts Receivable",
				"doctype": "Sales Invoice",
				"is_query_report": True
			},
			{
				"type": "report",
				"name": "Accounts Receivable Summary",
				"doctype": "Sales Invoice",
				"is_query_report": True
			},
			{
				"type": "report",
				"name": "Accounts Payable",
				"doctype": "Purchase Invoice",
				"is_query_report": True
			},
			{
				"type": "report",
				"name": "Accounts Payable Summary",
				"doctype": "Purchase Invoice",
				"is_query_report": True
			}]
		},
		{
			"label": _("Stock Reports"),
			"icon": "fa fa-star",
			"items": [{
				"type": "page",
				"name": "stock-balance",
				"label": _("Stock Summary"),
				"dependencies": ["Item"],
			},
			{
				"type": "report",
				"is_query_report": True,
				"name": "Stock Ledger",
				"doctype": "Stock Ledger Entry",
				"onboard": 1,
				"dependencies": ["Item"],
			},
			{
				"type": "report",
				"is_query_report": True,
				"name": "Stock Balance",
				"doctype": "Stock Ledger Entry",
				"onboard": 1,
				"dependencies": ["Item"],
			},
			{
				"type": "report",
				"is_query_report": True,
				"name": "Stock Projected Qty",
				"doctype": "Item",
				"onboard": 1,
				"dependencies": ["Item"],
			},
			{
				"type": "report",
				"is_query_report": True,
				"name": "Stock Ageing",
				"doctype": "Item",
				"dependencies": ["Item"],
			},
			{
				"type": "report",
				"is_query_report": True,
				"name": "Item Price Stock",
				"doctype": "Item",
				"dependencies": ["Item"],
			},
			{
				"type": "report",
				"is_query_report": False,
				"name": "Item-wise Price List Rate",
				"doctype": "Item Price",
				"onboard": 1,
			},
			{
				"type": "report",
				"is_query_report": True,
				"name": "Stock Analytics",
				"doctype": "Stock Entry",
				"onboard": 1,
			},
			{
				"type": "report",
				"is_query_report": True,
				"name": "Ordered Items To Be Delivered",
				"doctype": "Delivery Note"
			},
			{
				"type": "report",
				"is_query_report": True,
				"name": "Item Shortage Report",
				"doctype": "Bin"
			},
			{
				"type": "report",
				"is_query_report": True,
				"name": "Batch-Wise Balance History",
				"doctype": "Batch"
			}]
		},
		{
			"label": _("Sales Reports"),
			"icon": "fa fa-star",
			"items": [{
				"type": "report",
				"name": "Sales Register",
				"doctype": "Sales Invoice",
				"is_query_report": True
			},
			{
				"type": "report",
				"name": "Sales Register by Item",
				"is_query_report": True,
				"doctype": "Sales Invoice"
			},
			{
				"type": "report",
				"name": "Delivered Items To Be Billed",
				"is_query_report": True,
				"doctype": "Sales Invoice"
			},
			{
				"type": "report",
				"name": "Ordered Items To Be Billed",
				"is_query_report": True,
				"doctype": "Sales Invoice"
			}]
		},
		{
			"label": _("Purchase Reports"),
			"icon": "fa fa-star",
			"items": [{
				"type": "report",
				"name": "Purchase Register",
				"doctype": "Purchase Invoice",
				"is_query_report": True
			},
			{
				"type": "report",
				"name": "Item-wise Purchase Register",
				"is_query_report": True,
				"doctype": "Purchase Invoice"
			},
			{
				"type": "report",
				"name": "Purchase Order Items To Be Billed",
				"is_query_report": True,
				"doctype": "Purchase Invoice"
			},
			{
				"type": "report",
				"name": "Received Items To Be Billed",
				"is_query_report": True,
				"doctype": "Purchase Invoice"
			},
			{
				"type": "report",
				"is_query_report": True,
				"name": "Purchase Receipt Trends",
				"doctype": "Purchase Receipt"
			},
			{
				"type": "report",
				"is_query_report": True,
				"name": "Purchase Order Items To Be Received",
				"doctype": "Purchase Receipt"
			}]
		},
		{
			"label": _("Customer Reports"),
			"icon": "fa fa-star",
			"items": [{
				"type": "report",
				"label": _("Customer Wise Total Sales and Expenses"),
				"name": "Customer-wise Total Sales and Expenses",
				"doctype": "Customer",
				"is_query_report": True
			},
			{
				"type": "report",
				"label": _("Customer Acquisition and Loyalty"),
				"name": "Customer Acquisition and Loyalty",
				"doctype": "Customer",
				"is_query_report": True
			},
			{
				"type": "report",
				"label": _("Customer Credit Balance"),
				"name": "Customer Credit Balance",
				"doctype": "Customer",
				"is_query_report": True
			},
			{
				"type": "report",
				"label": _("Customer Wise Item Price"),
				"name": "Customer-wise Item Price",
				"doctype": "Customer",
				"is_query_report": True
			}]
		},
		{
			"label": _("Employee Reports"),
			"icon": "fa fa-star",
			"items": [{
				"type": "report",
				"label": _("Employee Leave Balance"),
				"name": "Employee Leave Balance",
				"doctype": "Employee",
				"is_query_report": True
			},
			{
				"type": "report",
				"label": _("Employee Leave Balance Summary"),
				"name": "Employee Leave Balance Summary",
				"doctype": "Employee",
				"is_query_report": True
			},
			{
				"type": "report",
				"label": _("Employee Advance Summary"),
				"name": "Employee Advance Summary",
				"doctype": "Employee Advance",
				"is_query_report": True
			},
			{
				"type": "report",
				"label": _("Employee CheckIn Report"),
				"name": "Employee Checkin Report",
				"doctype": "Employee Checkin",
				"is_query_report": True
			}]
		}
	]
