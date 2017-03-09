let options;
function get_sections(){
    let course = $('#course_id').val();
    $('#section_id').val('');
    $('#section_id optgroup').remove();
    $('#section_id').append(options.filter('[parent="{0}"]'.format(course)));
}

$(function(){
    options = $('#section_id optgroup');
    $('#course_id').change(get_sections);
    get_sections();
});
