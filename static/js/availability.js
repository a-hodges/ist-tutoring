claim = false;

function getAvailability(){
    $.getJSON("/availability.json", function(data){
        data = data.d;
        var list = $(document.createElement("tbody"));
        var tickets = [];
        for (var item in data){
            item = data[item];
            var li = $(document.createElement("tr"));

            var node = $(document.createElement("td")).addClass("course-name");
            node.append(item.number + " " + item.name);
            li.append(node);

            var node = $(document.createElement("td")).addClass("course-tutors");
            node.append(item.tutors);
            li.append(node);

            if (item.tutors == 0){
                li.addClass("no-tutors");
            } else if (item.tickets >= (item.tutors * 2)){
                li.addClass("busy-tutors");
            } else {
                li.addClass("availabile-tutors");
            }
            list.append(li);
        }
        $("#course-availability > tbody").replaceWith(list);
    });
}

$(document).ready(function(){
    getAvailability();
    setInterval(getAvailability, 60000);
});
