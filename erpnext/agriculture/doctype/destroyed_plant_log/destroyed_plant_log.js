// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Destroyed Plant Log', {
	refresh: function(frm){
		frm.trigger('set_dynamic_field_lable');
	},
	category_type: function(frm){
		frm.trigger('set_dynamic_field_lable');
	},
	set_dynamic_field_lable: function(frm){
		frm.set_df_property("category", "label", frm.doc.category_type);
	}
});
