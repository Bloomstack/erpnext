// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Plant Disease Diagnosis', {
	disease: (frm) => {
		return frm.call({
			method: "get_treatment_tasks",
			doc: frm.doc,
			callback: function(r) {
				frm.set_value("treatment_task", r.message);
			}
		});
	}
});
