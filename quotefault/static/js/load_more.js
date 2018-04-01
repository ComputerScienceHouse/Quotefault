function buttonAjax(buttonElem, options, failOnly) {
    if (failOnly === undefined) {
        failOnly = false;
    }

    // Get original html and click events
    var html = buttonElem.html();

    // Disable button
    buttonElem
        .prop('disabled', true)
        .css('pointer-events', 'none')
        .css('cursor', 'not-allowed');

    // Prepend spinner
    buttonElem.html('<i class="fas fa-spinner fa-spin"></i>&nbsp;' + html);

    var disableFunc = function () {
        // Reset original html
        buttonElem.html(html);

        // Enable button
        buttonElem
            .css('pointer-events', '')
            .prop('disabled', false)
            .css('cursor', '');
    };

    // Send AJAX
    if (failOnly === true) {
        return $.ajax(options).always(fail);
    } else {
        return $.ajax(options).always(disableFunc);
    }
}

$(function () {
    $("#get_more").one("click", function (e) {
        buttonAjax($(this), {
            url: '/additional',
            method: 'GET',
            success: function (data, textStatus, jqXHR) {
                $("#moreQuotes").html(data)
                    .collapse("show");
            },
            error: function (error) {
                console.log(error);
            }
        });
    });
});
