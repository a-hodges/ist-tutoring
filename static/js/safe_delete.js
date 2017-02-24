function del(){
    if (confirm('Are you sure you want to delete this record? It cannot be recovered.')){
        let id = $('#id').val();
        let form = $('<form></form>')
            .attr('action', deleteurl).attr('method', 'post');
        form.append($('<input>').attr('type', 'hidden')
            .attr('name', 'id').val(id));
        form.append($('<input>').attr('type', 'hidden')
            .attr('name', 'action').val('delete'));
        $(document.body).append(form);
        form.submit();
    }
}

$(document).ready(function(){
    $('#delete').click(del);
});
