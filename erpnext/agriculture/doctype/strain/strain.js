// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.provide("erpnext.strain");
$('head').append('<link rel="stylesheet" type="text/css" href="assets/erpnext/css/progressbar.css">');
frappe.ui.form.on('Strain', {
	setup: function (frm) {
		frm.make_methods = {
			'Plant Batch': () => frappe.model.open_mapped_doc({
				method: "erpnext.agriculture.doctype.strain.strain.make_plant_batch",
				frm: frm
			})
		}
	},

	refresh: function(frm) {
		frm.set_query("item_code", "materials_required", function() {
			return {
				query: "erpnext.controllers.queries.item_query"
			};
		});
		frm.fields_dict.materials_required.grid.set_column_disp('bom_no', false);
		frm.trigger('show_progress_for_metrc');
	},

	onload_post_render: function(frm) {
		frm.get_field("materials_required").grid.set_multiple_add("item_code", "qty");
	},

	show_progress_for_metrc: function(frm) {
		let selected_status = frm.doc.metrc_status;
		let completed_status = [];
		let incomplete_status = [];
		let successful_status = [
			'Compliance Document',
			'Reported to Bloomtrace',
			'Successful on Bloomtrace',
			'Reported to METRC',
			'Successful on METRC'
		];
		let unsuccessful_status = [
			'Failed on Bloomtrace',
			'Failed on METRC',
			'METRC ID Reported to Bloomstack'
		];
		let status_widths = [
			'Compliance Document',
			'Reported to Bloomtrace',
			'Status on Bloomtrace',
			'Reported to METRC',
			'Status on METRC',
			'METRC ID Reported to Bloomstack'
		];
		let colorsclass = {
			'Compliance Document': 'green',
			'Reported to Bloomtrace': 'green',
			'Successful on Bloomtrace': 'green',
			'Failed on Bloomtrace': 'red',
			'Reported to METRC': 'green',
			'Successful on METRC': 'green',
			'Failed on METRC': 'red',
			'METRC ID Reported to Bloomstack':'green'
		};

		let bars = [];
		let message = '';
		if(!status_widths.includes(selected_status)) {
			if(selected_status.includes('Bloomtrace')) {
				let index = status_widths.indexOf("Status on Bloomtrace");
				status_widths.splice(index, 1, selected_status);
			}
			else {
				let index = status_widths.indexOf("Status on METRC");
				status_widths.splice(index, 1, selected_status);
			}
		}
		status_widths.forEach((status, i) => {
			if(status == selected_status) {
				completed_status = status_widths.slice(0, i+1);
				jQuery.grep(status_widths, function(el) {
					if (jQuery.inArray(el, completed_status) == -1) incomplete_status.push(el);
				});
				completed_status.forEach(completed => {
					message = completed;
					bars.push({
						'title': completed,
						'width': '14%',
						'progress_class': colorsclass[selected_status]
					});
				});
				incomplete_status.forEach(incomplete => {
					message = incomplete;
					bars.push({
						'title': incomplete,
						'width': '14%',
						'progress_class':""
					});
				});
			}
		});
		frm.dashboard.add_progress_chart(__('Status'), bars, message);
		if(!frm.is_new() && successful_status.includes(selected_status) && !frm.frozen) {
			frm.frozen = true;
			frappe.dom.freeze();
		}
		if(!frm.is_new() && unsuccessful_status.includes(selected_status)) {
			frm.frozen = false;
			frappe.dom.unfreeze();
		}
	}
});


frappe.ui.form.on("BOM Item", {
	item_code: (frm, cdt, cdn) => {
		erpnext.strain.update_item_rate_uom(frm, cdt, cdn);
	},
	qty: (frm, cdt, cdn) => {
		erpnext.strain.update_item_qty_amount(frm, cdt, cdn);
	},
	rate: (frm, cdt, cdn) => {
		erpnext.strain.update_item_qty_amount(frm, cdt, cdn);
	}
});

erpnext.strain.update_item_rate_uom = function(frm, cdt, cdn) {
	frm.doc.materials_required.forEach((item, index) => {
		if (item.name == cdn && item.item_code){
			frappe.call({
				method:'erpnext.agriculture.doctype.strain.strain.get_item_details',
				args: {
					item_code: item.item_code
				},
				callback: (r) => {
					frappe.model.set_value('BOM Item', item.name, 'uom', r.message.uom);
					frappe.model.set_value('BOM Item', item.name, 'rate', r.message.rate);
				}
			});
		}
	});
};

erpnext.strain.update_item_qty_amount = function(frm, cdt, cdn) {
	frm.doc.materials_required.forEach((item, index) => {
		if (item.name == cdn){
			if (!frappe.model.get_value('BOM Item', item.name, 'qty'))
				frappe.model.set_value('BOM Item', item.name, 'qty', 1);
			frappe.model.set_value('BOM Item', item.name, 'amount', item.qty * item.rate);
		}
	});
};