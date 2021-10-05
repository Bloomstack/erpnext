// Copyright (c) 2021, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('AsanaSettings Settings', {
	enable: function(frm) {
		frm.set_df_property("personal_access_token", "reqd", frm.doc.enable ? 1 : 0);
	}
});