frappe.ready(() => {
    $('.content-name').on("click", function () {
        $('li').removeClass('active-parent');
        $('a.content-name').removeClass('active');
        $(this).parent('li').addClass('active-parent');
    });
});