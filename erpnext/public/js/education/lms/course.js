frappe.ready(() => {
    val = decodeURIComponent(getURLParameter(location.href, "name"));
    frappe.call({
        method: "erpnext.www.lms.course.get_completed_topic_list",
        args: {
            course_name: val
        },
        callback: (r) => {
            console.log(r);
            r.message.forEach(e => {
                console.log(e.content);
                $('.content-name').filter(function () {
                    return $(this).attr("id") == e.content
                }).css({
                    'color': 'blue'
                }).parent('li').addClass('active-parent');

            });
        }
    });

    function getURLParameter(url, name) {
        return (RegExp(name + '=' + '(.+?)(&|$)').exec(url) || [, null])[1];
    }
});