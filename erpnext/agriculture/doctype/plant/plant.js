// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Plant', {
	setup: function(frm) {
		frm.make_methods = {
			'Harvest': () => frappe.model.open_mapped_doc({
				method: "erpnext.agriculture.doctype.plant.plant.make_harvest",
				frm: frm
			}),
			'Destroyed Plant Log': () => { frm.trigger("destroy_plant"); }
		}
	},
	destroy_plant: (frm) => {
		frappe.prompt([
		{
			fieldname: 'reason',
			label: __('Reason'),
			fieldtype: 'Text',
			reqd: 1,
		}],
		(data) => {
			frm.call('destroy_plant', {
				destroy_count: 1,
				reason: data.reason
			}).then(r => {
				frappe.run_serially([
					() => frm.reload_doc(),
					() => frappe.set_route('Form', "Destroyed Plant Log", r.message)
				]);
			});
		},
		__('Destroyed Plant Log'),
		__('Destroy')
		);
	},
});
