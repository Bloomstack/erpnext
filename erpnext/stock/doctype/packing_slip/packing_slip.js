// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Packing Slip", {
	onload_post_render: (frm) => {
		if (frm.doc.sales_order && frm.is_new()) {
			frm.trigger("get_items");
		}
	},

	setup: (frm) => {
		frm.set_query('sales_order', (doc) => {
			return { filters: { 'docstatus': 1 } }
		});

		frm.set_query("item_code", "items", (doc, cdt, cdn) => {
			if (!doc.sales_order) {
				frappe.throw(__("Please select a Sales Order"));
			}

			return {
				query: "erpnext.stock.doctype.packing_slip.packing_slip.item_details",
				filters: { 'sales_order': doc.sales_order }
			}
		});
	},

	validate: (frm) => {
		frm.trigger("validate_case_nos");
		frm.trigger("validate_item_details");
		frm.trigger("calculate_package_weights");
	},

	items_on_form_rendered: (frm) => {
		// display the "Add Serial No" button
		erpnext.setup_serial_no();
	},

	sales_order: (frm) => {
		frm.trigger("get_items");
	},

	get_items: (frm) => {
		return frm.call({
			doc: frm.doc,
			method: "get_items",
			callback: (r) => {
				if (!r.exc) {
					frm.refresh();
				}
			}
		});
	},

	validate_case_nos: (frm) => {
		// To Case No. cannot be less than From Case No.
		if (!frm.doc.from_case_no) {
			frappe.throw(__("The 'From Package No.' field must neither be empty nor it's value less than 1."));
		} else if (!frm.doc.to_case_no) {
			frm.doc.to_case_no = frm.doc.from_case_no;
			refresh_field('to_case_no');
		} else if (frm.doc.to_case_no < frm.doc.from_case_no) {
			frappe.throw(__("'To Package No.' cannot be less than 'From Package No.'"));
		}
	},

	validate_item_details: (frm) => {
		// item quantity should be greater than 0
		for (let item of frm.doc.items) {
			if (item.qty <= 0) {
				frappe.throw(__(`Invalid quantity specified for item ${item.item_code}. Quantity should be greater than 0.`));
			}
		}

		// do not allow duplicate item codes
		const unique_items = frm.doc.items.uniqBy((item) => item.item_code)
		if (unique_items.length != frm.doc.items.length) {
			frappe.throw(__("You have entered duplicate items. Please rectify and try again."));
		}
	},

	calculate_package_weights: (frm) => {
		let net_weight = 0;
		frm.doc.net_weight_uom = (frm.doc.items && frm.doc.items.length) ? frm.doc.items[0].weight_uom : '';
		frm.doc.gross_weight_uom = frm.doc.net_weight_uom;

		for (let item of frm.doc.items) {
			if (item.weight_uom != frm.doc.net_weight_uom) {
				frappe.throw(__("Different UOM for items will lead to incorrect (Total) Net Weight value. Make sure that Net Weight of each item is in the same UOM."));
			}
			net_weight += flt(item.net_weight) * flt(item.qty);
		}

		frm.doc.net_weight_pkg = roundNumber(net_weight, 2);
		if (!flt(frm.doc.gross_weight_pkg)) {
			frm.doc.gross_weight_pkg = frm.doc.net_weight_pkg;
		}
		refresh_many(['net_weight_pkg', 'net_weight_uom', 'gross_weight_uom', 'gross_weight_pkg']);
	},
})

let make_row = (title, val, bold) => {
	return `<tr>
			<td class="datalabelcell">${(bold ? '<b>' : '')} ${title} ${(bold ? '</b>' : '')}</td>
			<td class="datainputcell" style="text-align:left;">${val}</td>
		</tr>`
}

cur_frm.pformat.net_weight_pkg = (doc) => {
	return `<table style="width:100%">${make_row('Net Weight', doc.net_weight_pkg)}</table>`
}

cur_frm.pformat.gross_weight_pkg = (doc) => {
	return `<table style="width:100%">${make_row('Gross Weight', doc.gross_weight_pkg)}</table>`
}
