# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals

no_cache = 1

import frappe
import re
import frappe.sessions

from erpnext.shopping_cart.cart import get_cart_quotation

def get_context(context):
	try:
		boot = frappe.sessions.get()
	except Exception as e:
		boot = frappe._dict(status='failed', error = str(e))
		print(frappe.get_traceback())

	# Disable document creation from frontend for quick forms, etc...
	boot.user.can_create = []

	boot_json = frappe.as_json(boot)
	# remove script tags from boot
	boot_json = re.sub("\<script\>[^<]*\</script\>", "", boot_json)

	context.update({
		"boot": boot if context.get("for_mobile") else boot_json
	})

	context.update(get_cart_quotation())
