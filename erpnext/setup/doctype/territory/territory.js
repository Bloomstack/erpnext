// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Territory", {
	setup: function(frm) {
		frm.set_query('parent_territory', function() {
			return {
				filters: {
					is_group: 1,
					name: ["!=", frm.doc.territory_name]
				}
			};
		});

		frm.set_query('distribution_id', 'targets', function(doc, cdt, cdn) {
			let row  = locals[cdt][cdn];
			return {
				filters: {
					fiscal_year: row.fiscal_year
				}
			};
		});
	},
	refresh: function(frm) {
		// read-only for root territory group
		frm.set_root_read_only("parent_territory");
	}
});