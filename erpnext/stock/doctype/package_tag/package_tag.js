// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Package Tag', {
	setup: (frm) => {
		frm.make_methods = {
			'Waste Disposal': () => frappe.model.open_mapped_doc({
				method: "erpnext.stock.doctype.package_tag.package_tag.make_waste_disposal",
				frm: frm,
			})
		};
	},
	refresh: function(frm) {
		frm.trigger("make_dashboard");
		frm.add_custom_button(__('Lost / Destroyed'), function() {
			frm.set_value("is_used", 1);
			frm.set_value("lost_or_destroyed", 1);
			frm.save();
		});
	},

	make_dashboard: (frm) => {
		if(!frm.is_new()) {
			frappe.call({
				method: 'erpnext.stock.doctype.package_tag.package_tag.get_package_tag_qty',
				args: {package_tag: frm.doc.name},
				callback: (r) => {
					if(!r.message) {
						return;
					}

					var section = frm.dashboard.add_section(`<h5 style="margin-top: 0px;">
						${ __("Stock Levels") }</a></h5>`);

					// sort by qty
					r.message.sort(function(a, b) { a.qty > b.qty ? 1 : -1; });

					var rows = $('<div></div>').appendTo(section);

					// show
					var total_qty = 0;
					(r.message || []).forEach(function(d) {
						if(d.qty > 0) {
							total_qty = total_qty + d.qty;
							$(`<div class='row' style='margin-bottom: 10px;'>
								<div class='col-sm-3 small' style='padding-top: 3px;'>${d.warehouse}</div>
								<div class='col-sm-3 small text-right' style='padding-top: 3px;'>${d.qty}</div>
								<div class='col-sm-6'>
									<button class='btn btn-default btn-xs btn-move' style='margin-right: 7px;'
										data-qty = "${d.qty}"
										data-warehouse = "${d.warehouse}">
										${__('Adjust')}</button>
								</div>
							</div>`).appendTo(rows);
						}
					});
					$(`<div class='col-sm-3 small' style='padding-top: 3px;'>Total</div>
					<div class='col-sm-3 small text-right' style='padding-top: 3px;'>${total_qty}</div>
					`).appendTo(rows);

					// adjust - ask for qty and adjustment reason
					// and make stock reconciliation
					rows.find('.btn-move').on('click', function() {
						var $btn = $(this);
						frappe.prompt([
							{
								fieldname: 'qty',
								label: __('Qty to Adjust'),
								fieldtype: 'Float',
								reqd: 1,
								default: $btn.attr('data-qty')
							},
							{
								fieldname: 'adjustment_reason',
								label: __('Adjustment Reason'),
								fieldtype: 'Data',
								reqd: 1
							}
						],
						(data) => {
							frappe.call({
								method: 'erpnext.stock.doctype.package_tag.package_tag.make_stock_reconciliation',
								args: {
									item_code: frm.doc.item_code,
									batch_no: frm.doc.batch_no,
									package_tag: frm.doc.name,
									qty: data.qty,
									warehouse: $btn.attr('data-warehouse'),
									adjustment_reason: data.adjustment_reason
								},
								callback: (r) => {
									frappe.show_alert(__('Stock Reconciliation {0} created',
										['<a href="#Form/Stock Reconciliation/'+r.message.name+'">' + r.message.name+ '</a>']));
									frm.refresh();
								},
							});
						},
						__('Adjust Package Tag'),
						__('Adjust')
						);
					});

					frm.dashboard.show();
				}
			});
		}
	}
});
