// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

frappe.listview_settings['Job Applicant'] = {
	add_fields: ["company", "designation", "job_applicant", "status"],
	get_indicator: function (doc) {
		if (doc.status == "Accepted") {
			return [__(doc.status), "green", "status,=," + doc.status];
		} else if (["Open", "Replied"].includes(doc.status)) {
			return [__(doc.status), "orange", "status,=," + doc.status];
		} else if (["Hold", "Rejected"].includes(doc.status)) {
			return [__(doc.status), "red", "status,=," + doc.status];
		}
	},

	onload: function(listview){
		const action = () => { 			
			let filters = {
				doctype: listview.doctype,
				docnames: listview.get_checked_items(),
			}
			let w = window.open(
				frappe.urllib.get_full_url(
					"/api/method/frappe.core.doctype.file.file.download_zip_files?" 
					+ "filters=" + JSON.stringify(filters)
				)
			);
			if (!w) {
				frappe.msgprint(__("Please enable pop-ups")); return;
			}
		}
		listview.page.add_actions_menu_item(__('Download Applicant Resume'), action, true);

	}
};
