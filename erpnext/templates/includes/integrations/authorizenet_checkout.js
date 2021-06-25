/**
 * On Success Callback
 * @typedef {function(object):Promise<void>} onCardProcessSuccess
 * @callback onCardProcessSuccess
 * @param {ProcessStatus} status The returned status object from the server
 */

/**
 * On Failure Callback
 * @typedef {function(object):Promise<void>} onCardProcessFail
 * @callback onCardProcessFail
 * @param {ProcessStatus} status returned status object from the server
 * @param {Exception} err If one occurs, the exception instance.
 */

/**
* @typedef {Object} ProcessStatus
* @property {string} status Status enum. Possible values: "Completed", "NotFound", "Queued", "Failed".
* @property {string} type On a failed request. The type is one of: "Validation", "HardError", "Timeout", "Unhandled"
* @property {string} description A reason message for the status returned.
* @property {int} wait An amount of time the client should wait before issuing 
*                      another status check request in milliseconds.
*/

frappe.ready(function () {
	const data = context;

	/**
	 * Fetches payment request status information
	 * @param {*} data Order information data structure. See authorizenet_settings.py
	 * @returns Promise<void>
	 */
	const fetch_status = async function (data) {
		const r = await frappe.call({
			method: "erpnext.erpnext_integrations.doctype.authorizenet_settings.authorizenet_settings.get_status",
			freeze: true,
			args: {
				"data": data
			}
		});

		return r.message;
	}

	/**
	 * Starts status request and UI updates to handle PR status check.
	 * @param {object} data Order information data structure. See authorizenet_settings.py
	 * @param {string} label Status label to display when processing status
	 * @param {onCardProcessSuccess} on_success a Success function callback. 
	 * @param {onCardProcessFail} on_fail A Failure function callback
	 * @param {int} counter A counter which is incremented internally as timeouts occur
	 * @param {int} maxTimeouts Maximum number of timeouts before a hard error
	 * @returns Promise<void>
	 */
	const check_status = async function (data, label, on_success, on_fail, counter, maxTimeouts) {
		if (!maxTimeouts) {
			maxTimeouts = 6; // 6 times x 5 secs = 30secs
		}
		// switch ui to display message to user
		start_status_check(label);
		try {
			const status = await fetch_status(data);

			// Process status result
			await process_status(status, label, on_success, on_fail, counter, maxTimeouts);
		} catch (err) {
			if (err) {
				if (!navigator.onLine || err.status === 0) {
					if (counter < maxTimeouts) {
						setTimeout(() => check_status(data,
							"Detected a network problem. Trying to reconnect, please wait...",
							on_success,
							on_fail,
							counter + 1),
							5000,
							maxTimeouts
						);
						return; // only early exit when queuing up a delayed check_status.
					} else {
						const errorStatus = {
							"status": "Failed",
							"type": "HardError",
							"description": "Network problem! Unfortunately we could not connect to our server. If your internet is down please try again later. Otherwise, contact support to help with your transaction."
						};

						$('#please-wait').text(__(errorStatus.description));
		
						if (on_fail) {
							on_fail(status);
						}
						return;
					}
				}
			}

			if (on_fail) {
				on_fail({}, err);
			}
		}
	}

	/**
	 * Hides form and displays message label.
	 * @param {string} label Feedback text to display to the user
	 */
	const start_status_check = function (label) {
		$('#please-wait').text(__(label || "Please Wait..."));
		$('#please-wait').fadeIn('fast');
		$('#payment-form').fadeOut('fast');
	}

	/**
	 * Displays the credit card form and hides message label.
	 */
	const show_form = function () {
		$('#please-wait').fadeOut('fast');
		$('#payment-form').fadeIn('fast');
	}


	/**
	 * Helper function, all status descriptions 
	 * @param {ProcessStatus} status The status object sent from the backend
	 * @param {string} label A label to display to the user during processing
	 * @param {onCardProcessSuccess} on_success a Success function callback. 
	 * @param {onCardProcessFail} on_fail A Failure function callback
	 * @param {int} counter A counter which is incremented internally as timeouts occur
	 * @param {int} maxTimeouts Maximum number of timeouts before a hard error
	 * @returns Promise<void>
	 */
	const process_status = async function (status, label, on_success, on_fail, counter, maxTimeouts) {
		if (!counter) {
			counter = 1;
		}
		if (!maxTimeouts) {
			maxTimeouts = 6;
		}

		if (status.status === "NotFound") {
			// No previous PR request found. So lets display the UI
			$('#please-wait').fadeOut('fast');
			$('#payment-form').fadeIn('fast');

		} else if (status.status === "Completed") {
			// Redirect user to payment success page
			if (on_success) {
				await on_success(status);
			}
			$('#please-wait').text(__("Payment was successful! Please wait while we redirect you."));

			window.location.href = "/integrations/payment-success";
		} else if (status.status === "Queued") {
			// Processing not completed. Wait for Queue
			$('#please-wait').text(__("Request is taking longer than expected. Please wait..."));
			setTimeout(function () { check_status(data, label, on_success, on_fail, counter + 1, maxTimeouts) }, status.wait);

		} else if (status.status === "Failed") {
			if (status.type === "Validation") {
				// On validation errors, re-enable form
				frappe.msgprint(__(status.description || ""));
				show_form();
				$('#submit').prop('disabled', false);
				$('#submit').html(__('Retry'));

				if (on_fail) {
					await on_fail(status);
				}
			} else if (status.type === "HardError") {
				if (status.description) {
					$('#please-wait').text(__(status.description));
				} else {
					$('#please-wait').text(__("There was an uhandled internal error. Please try again or contact support."));
				}
				if (on_fail) {
					await on_fail(status);
				}
			} else {
				// Anything else is a failed request. Lets figure out if its a hard error
				// or a validation one on the callback
				if (on_fail) {
					await on_fail(status);
				}
			}
		}
	}

	/**
	 * Starts card processing
	 * @param {onCardProcessSuccess} on_success a Success function callback. 
	 * @param {onCardProcessFail} on_fail A Failure function callback
	 * @returns Promise<void>
	 */
	const charge = async function (card, on_success, on_fail) {
		start_status_check("Processing. Please Wait...");
		try {
			const r = await frappe.call({
				method: "erpnext.erpnext_integrations.doctype.authorizenet_settings.authorizenet_settings.charge_credit_card",
				freeze: true,
				args: {
					"card": card,
					"data": data
				}
			});
			await process_status(r.message, "Processing. Please wait...", on_success, on_fail);
		} catch (err) {
			console.error(err);
			on_fail({}, err);
		}
	}

	// Handles credit card submit behaviour
	$('#submit').on("click", async function (e) {
		e.preventDefault();

		let cardHolderName = document.getElementById('cardholder-name').value;
		let cardHolderEmail = document.getElementById('cardholder-email').value;
		let cardNumberWithSpaces = document.getElementById('card-number').value;
		let cardNumber = cardNumberWithSpaces.replace(/ /g, "");
		let expirationMonth = document.getElementById('card-expiry-month').value;
		let expirationYear = document.getElementById('card-expiry-year').value;
		let expirationDate = expirationYear.concat("-").concat(expirationMonth);
		let cardCode = document.getElementById('card-code').value;
		let isValidCard = frappe.cardValidator.number(cardNumber);
		const card = {
			holder_name: cardHolderName,
			holder_email: cardHolderEmail,
			number: cardNumber,
			expiration_date: expirationDate,
			code: cardCode
		}

		if (!cardHolderName) {
			frappe.throw(__("Card Holder Name is mandatory."));
		}

		if (!cardHolderEmail) {
			frappe.throw(__("Card Holder Email is mandatory."));
		}

		if (!validate_email(cardHolderEmail)) {
			frappe.throw(__("Card Holder Email is invalid."));
		}

		if (!isValidCard.isPotentiallyValid) {
			frappe.throw(__("Card Number is Invalid."));
		}

		if (cardNumber.length < 13 || cardNumber.length > 16) {
			frappe.throw(__("Card Number length should be between 13 and 16 characters"));
		}

		if (expirationMonth === "00" || expirationMonth.length !== 2 || expirationYear === "0000" || expirationYear.length !== 4) {
			frappe.throw(__("Card Expiration Date is invalid"));
		}

		if (cardCode.length < 3 || cardCode.length > 4) {
			frappe.throw(__("Card Code length should be between 3 and 4 characters"));
		}

		$('#submit').prop("disabled", true);
		$('#submit').html(__("Processing..."));

		// issue credit card charge
		await charge(card, null, async (status, err) => {
			if (err) {
				if (!navigator.onLine || err.status === 0) {
					// We lost connection or timed out
					// Check status until network is back or timeout again
					// Default should be around 6 times or 30 seconds.
					check_status(data,
						"Detected a network problem. Trying to reconnect, please wait...",
						null, null, 0);
				}
			}

			if (status.status === "Fail" && status.type === "Duplicate") {
				// Allow up to one more request after a duplicate with a 10 second delay.
				// This can happen if a card is decliened but the next request is sent before
				// the duplicate window guard window.
				setTimeout(() => charge(card), 10000);
			}
		});
	});

	// Ensures only digits are entered on digit fields
	$('input[data-validation="digit"]')
		.on("paste", function (e) {
			if (e.originalEvent.clipboardData.getData('text').match(/[^\d]/))
				e.preventDefault(); //prevent the default behaviour
		})
		.keypress(function (event) {
			return (event.charCode !== 8 && event.charCode === 0 || (event.charCode >= 48 && event.charCode <= 57));
		});

	// Actively validates credit card formatting
	$('#card-number').on('keydown', function () {
		var val = $(this).val();
		val = val.replace(/\s/g, '');
		let newval = val;
		if (val.match(/.{1,4}/g))
			newval = val.match(/.{1,4}/g).join(" ");
		$(this).val(newval);
	});

	// ping server first to check if this PR was already fullfilled.
	check_status(data, "Loading...", null, async function (status, err) {
		// During any soft failure, display card form.
		show_form();
	}, 0);
});
