// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Destroyed Plant Log', {
	category: function(frm){
		frm.toggle_display('plant', frm.doc.category == "Plant");
		if (frm.doc.category == "Plant"){
			frm.set_df_property('plant', 'reqd', 1);
			frm.set_df_property('plant_batch', 'reqd', 0);
		}
		frm.toggle_display('plant_batch', frm.doc.category == "Plant Batch");
		if (frm.doc.category == "Plant Batch"){
			frm.set_df_property('plant_batch', 'reqd', 1);
			frm.set_df_property('plant', 'reqd', 0);
		}
	}
});
