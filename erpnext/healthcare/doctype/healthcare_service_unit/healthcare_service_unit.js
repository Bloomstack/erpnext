// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Healthcare Service Unit', {
	onload: function(frm) {
		frm.list_route = "Tree/Healthcare Service Unit";

		// get query select healthcare service unit
		frm.set_query('parent_healthcare_service_unit', function() {
			return {
				filters: {
					is_group: 1,
					name: ["!=", frm.doc.healthcare_service_unit_name]
				}
			};
		});
	},
	refresh: function(frm) {
		// read-only for root healthcare service unit
		frm.set_root_read_only("parent_healthcare_service_unit");
		frm.set_df_property("service_unit_type", "reqd", 1);
		frm.add_custom_button(__("Healthcare Service Unit Tree"), function() {
			frappe.set_route("Tree", "Healthcare Service Unit");
		});
	},
	allow_appointments: function(frm) {
		if(!frm.doc.allow_appointments){
			frm.set_value("overlap_appointments", false);
		}
	},
	is_group: function(frm) {
		if(frm.doc.is_group == 1){
			frm.set_value("allow_appointments", false);
			frm.set_df_property("service_unit_type", "reqd", 0);
		}
		else{
			frm.set_df_property("service_unit_type", "reqd", 1);
		}
	}
});
