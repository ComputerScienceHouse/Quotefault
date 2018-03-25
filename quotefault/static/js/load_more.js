$(function () {
    $("#get_more").one("click", function (e) {
        $.ajax({
            url: '/additional',
            method: 'GET',
            success: function (data, textStatus, jqXHR) {
                $("#moreQuotes").html(data);
            },
            error: function (error) {
                console.log(error);
            }
        });
    });
});
