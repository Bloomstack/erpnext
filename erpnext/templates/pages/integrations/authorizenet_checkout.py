# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
import json
from frappe.utils import fmt_money


def get_context(context):
	context.no_cache = 1
	payment_context = dict(frappe.local.request.args)
	context.payment_context = json.dumps(payment_context)
	context["description"] = payment_context.get("description") or ""
	context["amount"] = fmt_money(amount=payment_context.get('amount'), currency=payment_context.get('currency'))
