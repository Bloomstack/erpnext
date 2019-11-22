// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Packing Slip", {
	onload_post_render: (frm) => {
		if (frm.doc.sales_order && frm.is_new()) {
			frm.trigger("get_items");
		}
	},

	setup: (frm) => {
		frm.set_query("sales_order", (doc) => {
			return {
				filters: {
					"docstatus": 1,
					"per_delivered": ["<", 100]
				}
			}
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
	}
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
