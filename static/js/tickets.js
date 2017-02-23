var claim = true;

function getTickets(){
    let FIELDS = {
        "name": 2,
        "course": 2,
        "assignment": 3,
        "question": 4,
    };
    $.getJSON("/tickets.json", function(data){
        data = data.d;
        var list = $(document.createElement("ul")).attr("id", "tickets");
        for (var item in data){
            item = data[item];
            var li = $(document.createElement("li"));
            li.addClass("row");
            for (var field in FIELDS){
                field = FIELDS[field];
                var node = $(document.createElement("span"));
                node.addClass("col-md-{}".format(FIELDS[field] * 1));
                node.addClass("col-xs-{}".format(FIELDS[field] * 3));
                node.append(item[field]);
                li.append(node);
            }
            var node = $(document.createElement("a"))
                .attr("href", "/claim-ticket/" + item.id.toString())
                .addClass("col-xs-1")
                .append("Claim");
            if (claim){
                li.append(node);
            }
            list.append(li);
        }
        $("#tickets").replaceWith(list);
    });
}

$(document).ready(function(){
    getTickets();
    setInterval(getTickets, 60000);
});
