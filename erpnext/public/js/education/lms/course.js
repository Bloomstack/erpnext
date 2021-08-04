frappe.ready(() => {
    $('.content-name').on("click", function () {
        $('.searched-content .details').html("");
        $('.content-data p, .content-data p span, .content-data ol').html("");
        $('li').removeClass('active-parent');
        $('a.content-name').removeClass('active');
        $(this).parent('li').addClass('active-parent');
        content_type = getURLParameter(this.href, 'type');
        content_name = decodeURIComponent(getURLParameter(this.href, 'content'));

        frappe.call({
			method: "erpnext.www.lms.course.get_content_details",
			args: {
                type: content_type,
                content_name: content_name
			},
			callback: (r) => {
				if (r.message) {
					$('.details').append(
                      r.message.content
                    );
                    $(".title h1").text(content_name);
				} else {
					$('.searched-content .error-message').append('<h5>Not Found</h5>')
				}
			}
		});
    });

    function getURLParameter(url, name) {
        return (RegExp(name + '=' + '(.+?)(&|$)').exec(url)||[,null])[1];
    }

});