// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Plant Batch', {
	setup: function (frm) {
		frm.make_methods = {
			'Plant': () => frappe.model.open_mapped_doc({
				method: "erpnext.agriculture.doctype.plant_batch.plant_batch.make_plant",
				frm: frm
			}),
			'Harvest': () => frappe.model.open_mapped_doc({
				method: "erpnext.agriculture.doctype.plant_batch.plant_batch.make_harvest",
				frm: frm
			}),
			'Destroyed Plant Log': () => { frm.trigger("destroy_plant_batch"); }
		};
	},

	refresh: (frm) => {
		if (!frm.doc.__islocal)
			frm.add_custom_button(__('Reload Linked Analysis'), () => frm.call("reload_linked_analysis"));

		frappe.realtime.on("List of Linked Docs", (output) => {
			let analysis_doctypes = ['Soil Texture', 'Plant Analysis', 'Soil Analysis'];
			let analysis_doctypes_docs = ['soil_texture', 'plant_analysis', 'soil_analysis'];
			let obj_to_append = { soil_analysis: [], soil_texture: [], plant_analysis: [] };
			output['Location'].forEach((land_doc) => {
				analysis_doctypes.forEach((doctype) => {
					output[doctype].forEach((analysis_doc) => {
						let point_to_be_tested = JSON.parse(analysis_doc.location).features[0].geometry.coordinates;
						let poly_of_land = JSON.parse(land_doc.location).features[0].geometry.coordinates[0];
						if (is_in_land_unit(point_to_be_tested, poly_of_land)) {
							obj_to_append[analysis_doctypes_docs[analysis_doctypes.indexOf(doctype)]].push(analysis_doc.name);
						}
					});
				});
			});
			frm.call('append_to_child', {
				obj_to_append: obj_to_append
			});
		});
	},

	destroy_plant_batch: (frm) => {
		frappe.prompt([{
			fieldname: 'destroy_count',
			label: __('Destroy Count'),
			fieldtype: 'Int',
			reqd: 1,
		},
		{
			fieldname: 'reason',
			label: __('Reason'),
			fieldtype: 'Data',
			reqd: 1,
		}],
		(data) => {
			frm.call('destroy_plant_batch', {
				destroy_count: data.destroy_count,
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
	}
});

function is_in_land_unit(point, vs) {
	// ray-casting algorithm based on
	// http://www.ecse.rpi.edu/Homepages/wrf/Research/Short_Notes/pnpoly.html

	var x = point[0], y = point[1];

	var inside = false;
	for (var i = 0, j = vs.length - 1; i < vs.length; j = i++) {
		var xi = vs[i][0], yi = vs[i][1];
		var xj = vs[j][0], yj = vs[j][1];

		var intersect = ((yi > y) != (yj > y))
			&& (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
		if (intersect) inside = !inside;
	}

	return inside;
};
