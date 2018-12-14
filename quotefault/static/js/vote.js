
function makeVote(quote_id, direction){
    $.ajax({
            url: "/vote",
            data: {
                "quote_id" : quote_id,
                "direction": direction
            },
            method: "POST"
    });
    $("#votes-" + quote_id).upvote();

    if(direction === 1){
        $("#votes-" + quote_id).upvote('upvote');
    } else {
        $("#votes-" + quote_id).upvote('downvote');
    }
}


