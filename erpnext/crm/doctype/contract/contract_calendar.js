// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.views.calendar["Contract"] = {
	field_map: {
		"start": "end_date",
		"end": "end_date",
		"title": "name"
	},
	get_events_method: "erpnext.crm.doctype.contract.contract.get_events"
};
