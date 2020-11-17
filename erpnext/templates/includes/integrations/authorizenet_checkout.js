$('#submit').on("click", function(e) {
	let data = context.replace(/'/g, '"');
	e.preventDefault();

	let cardNumber = document.getElementById('card-number').value;
	let expirationMonth = document.getElementById('card-expiry-month').value;
	let expirationYear = document.getElementById('card-expiry-year').value;
	let expirationDate = expirationYear.concat("-").concat(expirationMonth);
	let cardCode = document.getElementById('card-code').value;

	if(expirationMonth === "00" || expirationMonth.length !== 2 || expirationYear === "0000" || expirationYear.length !== 4){
		frappe.throw(__("Card Expiration Date is invalid"));
	}

	if(cardCode.length < 3 || cardCode.length > 4){
		frappe.throw(__("Card Code length should be between 3 and 4 characters"));
	}

	if(cardNumber.length < 13 || cardNumber.length > 16){
		frappe.throw(__("Card number length should be between 13 and 16 characters"));
	}

	$('#submit').prop('disabled', true);
	$('#submit').html(__('Processing...'));

	frappe.call({
		method: "erpnext.erpnext_integrations.doctype.authorizenet_settings.authorizenet_settings.charge_credit_card",
		freeze: true,
		args: {
			"card_number": cardNumber,
			"expiration_date": expirationDate,
			"card_code": cardCode,
			"data": data
		},
		callback: function(r) {
			if (r.message.status === "Completed") {
				window.location.href = "/integrations/payment-success";
			} else {
				frappe.msgprint(__(`${r.message.description}`));
				$('#submit').prop('disabled', false);
				$('#submit').html(__('Retry'));
			}
		}
	})
});

$('input[data-validation="digit"]').keypress(function(event){
	return (event.charCode !== 8 && event.charCode === 0 || (event.charCode >= 48 && event.charCode <= 57));
});