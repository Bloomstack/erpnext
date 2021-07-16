// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Holiday List', {
	refresh: function(frm) {
		if (frm.doc.holidays) {
			frm.set_value('total_holidays', frm.doc.holidays.length);
		}

		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("Create Events"), function() {
				frappe.show_alert({
					message:__("Creating Calendar Events."),
					indicator:'blue'
				});

				frappe.call({
					method: "erpnext.hr.doctype.holiday_list.holiday_list.create_events",
					args: {
						holiday_list: frm.doc.name
					},
					callback: function(r) {
						console.log(r)
						if (r && r.message) {
							frappe.show_alert({
								message:__("Calendar Events created."),
								indicator:'green'
							});
						}
					}
				});
			});
		}
	},
	from_date: function(frm) {
		if (frm.doc.from_date && !frm.doc.to_date) {
			var a_year_from_start = frappe.datetime.add_months(frm.doc.from_date, 12);
			frm.set_value("to_date", frappe.datetime.add_days(a_year_from_start, -1));
		}
	}
});
