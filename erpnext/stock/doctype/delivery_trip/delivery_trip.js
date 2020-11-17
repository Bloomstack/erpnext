// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Delivery Trip', {
	setup: function (frm) {
		frm.set_indicator_formatter('customer', (stop) => (stop.visited) ? "green" : "orange");

		frm.set_query("driver", function () {
			return {
				filters: {
					"status": "Active"
				}
			};
		});

		frm.set_query("address", "delivery_stops", function (doc, cdt, cdn) {
			var row = locals[cdt][cdn];
			if (row.customer) {
				return {
					query: 'frappe.contacts.doctype.address.address.address_query',
					filters: {
						link_doctype: "Customer",
						link_name: row.customer
					}
				};
			}
		})

		frm.set_query("contact", "delivery_stops", function (doc, cdt, cdn) {
			var row = locals[cdt][cdn];
			if (row.customer) {
				return {
					query: 'frappe.contacts.doctype.contact.contact.contact_query',
					filters: {
						link_doctype: "Customer",
						link_name: row.customer
					}
				};
			}
		})
	},

	refresh: function (frm) {
		if (frm.doc.docstatus == 1 && frm.doc.status != "Completed") {
			if (frm.doc.status == "Scheduled") {
				frm.trigger("start");
			} else if (frm.doc.status == "In Transit") {
				frm.trigger("pause");
				frm.trigger("end");
			} else if (frm.doc.status == "Paused") {
				frm.trigger("continue");
				frm.trigger("end");
			}
		}

		frappe.db.get_value("Google Settings", { name: "Google Settings" }, "enable", (r) => {
			if (r.enable == 0) {
				// Hide entire Map section if Google Maps is disabled
				let wrapper = frm.fields_dict.sb_map.wrapper;
				wrapper.hide();
			} else {
				// Inject Google Maps data into map embed field
				let wrapper = frm.fields_dict.map_html.$wrapper;
				wrapper.html(frm.doc.map_embed);
			}
		});

		// Print delivery manifests
		if (frm.doc.docstatus === 1) {
			if (frm.doc.delivery_stops.length > 0) {
				let deliveryNotes = frm.doc.delivery_stops.map(stop => stop.delivery_note);
				deliveryNotes = [...new Set(deliveryNotes)];
				deliveryNotes = deliveryNotes.filter(Boolean);

				frm.add_custom_button(__("Print Shipping Manifests"), () => {
					if (deliveryNotes.length == 0) {
						frappe.msgprint(__("There are no Delivery Notes linked to any stop(s)"))
					} else {
						const w = window.open('/api/method/frappe.utils.print_format.download_multi_pdf?' +
							'doctype=' + encodeURIComponent("Delivery Note") +
							'&name=' + encodeURIComponent(JSON.stringify(deliveryNotes)) +
							'&format=' + encodeURIComponent(frm.doc.shipping_manifest_template || ""));

						if (!w) {
							frappe.msgprint(__('Please enable pop-ups'));
							return;
						}
					}
				}).addClass("btn-primary");
			};
		}
		if (frm.doc.docstatus == 1 && frm.doc.delivery_stops.length > 0) {
			frm.add_custom_button(__("Notify Customers via Email"), function () {
				frm.trigger('notify_customers');
			});
		}

		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Delivery Note'), () => {
				erpnext.utils.map_current_doc({
					method: "erpnext.stock.doctype.delivery_note.delivery_note.make_delivery_trip",
					source_doctype: "Delivery Note",
					target: frm,
					date_field: "posting_date",
					setters: {
						company: frm.doc.company,
					},
					get_query_filters: {
						docstatus: 1,
						company: frm.doc.company,
					}
				})
			}, __("Get customers from"));
		}
	},

	calculate_arrival_time: function (frm) {
		if (!frm.doc.driver_address) {
			frappe.throw(__("Cannot Calculate Arrival Time as Driver Address is Missing."));
		}
		frappe.show_alert({
			message: "Calculating Arrival Times",
			indicator: 'orange'
		});
		frm.call("process_route", {
			optimize: false,
		}, () => {
			frm.reload_doc();
		});
	},

	start: (frm) => {
		frm.add_custom_button(__("Start"), () => {
			frappe.db.get_value("Delivery Settings", { "name": "Delivery Settings" }, "default_activity_type")
				.then((r) => {
					if (!r.message.default_activity_type) {
						frappe.throw(__("Please set a default activity type in Delivery Settings to time this trip."));
						return;
					} else {
						frappe.prompt({
							"label": "Odometer Start Value",
							"fieldtype": "Float",
							"fieldname": "odometer_start_value",
							"reqd": 1
						},
							(data) => {
								frappe.call({
									method: "erpnext.stock.doctype.delivery_trip.delivery_trip.create_or_update_timesheet",
									args: {
										"trip": frm.doc.name,
										"action": "start",
										"odometer_value": data.odometer_start_value,
									},
									callback: (r) => {
										frm.reload_doc();
									}
								})
								// update status of delivery note to "In Transit" when user starts delivery trip
								for (let stop of frm.doc.delivery_stops) {
									if (stop.delivery_note) {
										frappe.db.set_value("Delivery Note", stop.delivery_note, "status", "In Transit");
									}
								}
							},
							__("Enter Odometer Value"));
					}
				})
		}).addClass("btn-primary");
	},

	pause: (frm) => {
		frm.add_custom_button(__("Pause"), () => {
			frappe.confirm(__("Are you sure you want to pause the trip?"),
				() => {
					frappe.call({
						method: "erpnext.stock.doctype.delivery_trip.delivery_trip.create_or_update_timesheet",
						args: {
							"trip": frm.doc.name,
							"action": "pause"
						},
						callback: (r) => {
							frm.reload_doc();
						}
					})
				},
				() => {
					frm.reload_doc();
				}
			);

		}).addClass("btn-primary");
	},

	continue: (frm) => {
		frm.add_custom_button(__("Continue"), () => {
			frappe.confirm(__("Are you sure you want to continue the trip?"),
				() => {
					frappe.call({
						method: "erpnext.stock.doctype.delivery_trip.delivery_trip.create_or_update_timesheet",
						args: {
							"trip": frm.doc.name,
							"action": "continue"
						},
						callback: (r) => {
							frm.reload_doc();
						}
					})
				},
				() => {
					frm.reload_doc();
				}
			);

		}).addClass("btn-primary");
	},

	end: (frm) => {
		frm.add_custom_button(__("End"), () => {
			frappe.prompt({
				"label": "Odometer End Value",
				"fieldtype": "Float",
				"fieldname": "odometer_end_value",
				"reqd": 1,
				"default": frm.doc.odometer_start_value
			},
				(data) => {
					if (data.odometer_end_value > frm.doc.odometer_start_value) {
						frappe.call({
							method: "erpnext.stock.doctype.delivery_trip.delivery_trip.create_or_update_timesheet",
							args: {
								"trip": frm.doc.name,
								"action": "end",
								"odometer_value": data.odometer_end_value,
							},
							callback: (r) => {
								frm.reload_doc();
							}
						})
					} else {
						frappe.msgprint(__("'Odometer End Value' should be greater then 'Odometer Start Value'"));
					}
				},
				__("Enter Odometer Value"));
		}).addClass("btn-primary");
	},

	before_submit: function (frm) {
		frm.toggle_reqd(["driver", "driver_address"], 1)
	},

	validate: function (frm) {
		if (frm.is_new() && frm.doc.delivery_stops) {
			// frappe.confirm doesn't wait for callback to validate, so creating
			// Promise to make sure execution is paused until user input
			return new Promise((resolve, reject) => {
				frappe.call({
					method: "erpnext.stock.doctype.delivery_trip.delivery_trip.validate_unique_delivery_notes",
					args: {
						delivery_stops: frm.doc.delivery_stops
					},
					callback: (r) => {
						if (!$.isEmptyObject(r.message)) {
							// create an unordered list of existing note <-> trip mappings
							let existing_trips = "<ul>";
							for (let trip in r.message) {
								existing_trips += `<li><strong>${trip}</strong> exists in <strong>${r.message[trip]}</strong></li>`
							}
							existing_trips += "</ul>"

							let confirm_message = `The following deliveries already exist in recent
								trip(s): ${existing_trips} Do you still want to continue?`;

							frappe.confirm(
								__(confirm_message),
								() => { resolve(); },  // If "Yes" is selected
								() => { frappe.set_route("List", frm.doc.doctype); }  // If "No" is selected
							);
						} else { resolve(); }
					},
					error: (r) => reject(r.message)
				})
			})

		}
	},
	driver: function (frm) {
		if (frm.doc.driver) {
			frappe.db.get_value("Delivery Trip", {
				docstatus: ["<", 2],
				driver: frm.doc.driver,
				departure_time: [">", frappe.datetime.nowdate()]
			}, "name", (r) => {
				if (r) {
					let confirm_message = `${frm.doc.driver_name} has already been assigned a Delivery Trip
											today (${r.name}). Do you want to modify that instead?`;

					frappe.confirm(__(confirm_message), function () {
						frappe.set_route("Form", "Delivery Trip", r.name);
					});
				};
			});

			frappe.call({
				method: "erpnext.stock.doctype.delivery_trip.delivery_trip.get_driver_email",
				args: {
					driver: frm.doc.driver
				},
				callback: (data) => {
					frm.set_value("driver_email", data.message.email);
				}
			});
		};
	},

	optimize_route: function (frm) {
		if (!frm.doc.driver_address) {
			frappe.throw(__("Cannot Optimize Route as Driver Address is Missing."));
		}
		frappe.show_alert({
			message: "Optimizing Route",
			indicator: 'orange'
		});
		frm.call("process_route", {
			optimize: true,
		}, () => {
			frm.reload_doc();
		});
	},

	make_payment_entry: function (frm, row, amount) {
		frappe.call({
			method: "erpnext.stock.doctype.delivery_trip.delivery_trip.make_payment_entry",
			args: {
				"payment_amount": amount,
				"sales_invoice": row.sales_invoice
			},
			callback: function (r) {
				if (!r.exc) {
					frm.reload_doc();
					if (r.message) {
						frappe.msgprint(__(`Payment Entry {0} created.`, [r.message]));
					} else {
						frappe.msgprint(__("The stop was marked as visited without payment"));
					}
				}
			}
		})
	},

	notify_customers: function (frm) {
		$.each(frm.doc.delivery_stops || [], function (i, delivery_stop) {
			if (!delivery_stop.delivery_note) {
				frappe.msgprint({
					"message": __("No Delivery Note selected for Customer {}", [delivery_stop.customer]),
					"title": __("Warning"),
					"indicator": "orange",
					"alert": 1
				});
			}
		});

		frappe.db.get_value("Delivery Settings", { name: "Delivery Settings" }, "dispatch_template", (r) => {
			if (!r.dispatch_template) {
				frappe.throw(__("Missing email template for dispatch. Please set one in Delivery Settings."));
			} else {
				frappe.confirm(__("Do you want to notify all the customers by email?"), function () {
					frappe.call({
						method: "erpnext.stock.doctype.delivery_trip.delivery_trip.notify_customers",
						args: {
							"delivery_trip": frm.doc.name
						},
						callback: function (r) {
							if (!r.exc) {
								frm.doc.email_notification_sent = true;
								frm.refresh_field('email_notification_sent');
							}
						}
					});
				});
			}
		});
	},

	email_coas: function(frm) {
		let delivery_notes = frm.doc.delivery_stops.map(stop => stop.delivery_note);
		delivery_notes = [...new Set(delivery_notes)];
		delivery_notes.forEach(delivery_note =>{
			frappe.call({
				method: "erpnext.stock.doctype.delivery_note.delivery_note.email_coas",
				args: {
					docname: delivery_note
				},
				callback: (r) => {
					if(r.message == "success"){
						frappe.show_alert({
							indicator: 'green',
							message: __('Email Queued')
						});
					}
				}
			})
		})
	}
});

frappe.ui.form.on('Delivery Stop', {
	customer: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.customer) {
			frappe.call({
				method: "erpnext.stock.doctype.delivery_trip.delivery_trip.get_contact_and_address",
				args: { "name": row.customer },
				callback: function (r) {
					if (r.message) {
						if (r.message["shipping_address"]) {
							frappe.model.set_value(cdt, cdn, "address", r.message["shipping_address"].parent);
						}
						else {
							frappe.model.set_value(cdt, cdn, "address", '');
						}
						if (r.message["contact_person"]) {
							frappe.model.set_value(cdt, cdn, "contact", r.message["contact_person"].parent);
						}
						else {
							frappe.model.set_value(cdt, cdn, "contact", '');
						}
					}
					else {
						frappe.model.set_value(cdt, cdn, "address", '');
						frappe.model.set_value(cdt, cdn, "contact", '');
					}
				}
			});


			frappe.call({
				method: "erpnext.stock.doctype.delivery_trip.delivery_trip.get_delivery_window",
				args: { doctype : "Delivery Note" , docname : row.delivery_note, customer : row.customer },
				callback: function (r) {
					if(r.message && (r.message.delivery_start_time || r.message.delivery_end_time) ){
						frappe.model.set_value(cdt, cdn, "delivery_start_time", r.message.delivery_start_time);
						frappe.model.set_value(cdt, cdn, "delivery_end_time", r.message.delivery_end_time);
					}
				}
			});
		}
	},

	address: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.address) {
			frappe.call({
				method: "frappe.contacts.doctype.address.address.get_address_display",
				args: { "address_dict": row.address },
				callback: function (r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, "customer_address", r.message);
					}
				}
			});
		} else {
			frappe.model.set_value(cdt, cdn, "customer_address", "");
		}
	},

	contact: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.contact) {
			frappe.call({
				method: "erpnext.stock.doctype.delivery_trip.delivery_trip.get_contact_display",
				args: { "contact": row.contact },
				callback: function (r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, "customer_contact", r.message);
					}
				}
			});
		} else {
			frappe.model.set_value(cdt, cdn, "customer_contact", "");
		}
	},


	make_payment_entry: function (frm, cdt, cdn) {
		const row = frm.selected_doc || locals[cdt][cdn];

		let dialog = frappe.prompt({
			"label": "Payment Amount",
			"fieldtype": "Currency",
			"fieldname": "payment_amount",
			"reqd": 1
		},
		function (data) {
			if (data.payment_amount === 0) {
				frappe.confirm(
					__("Are you sure you want to complete this delivery without a payment?"),
					() => { frm.events.make_payment_entry(frm, row, data.payment_amount); }
				);
			} else {
				frm.events.make_payment_entry(frm, row, data.payment_amount);
			}
		},
		__("Make Payment Entry"));

		dialog.$wrapper.on("shown.bs.modal", function () {
			if (frappe.is_mobile()) {
				dialog.$wrapper.find($('input[data-fieldtype="Currency"]')).attr('type', 'number');
			}
		});
	}
});
