/*

*/

function show_record(data) {
    data.duration = data.duration.toFixed(2)
    var template = '<tr class="odd"><td><a href="{{label}}/">{{label}}</a></td><td>{{reason}}</td><td>{{outcome}}</td><td>{{duration}}&nbsp;s</td><td>{{timestamp}}</td><td>{{executable.name}} {{executable.version}}</td><td>{{repository.url}}</td><td>{{version}}</td><td>{{main_file}}</td><td>{{script_arguments}}</td><td>{{#tags}}<a class="btn btn-mini" href="?tags={{.}}">{{.}}</a> {{/tags}}</td></tr>';
    var html = Mustache.to_html(template, data);
    $('table.main').append(html);
}

function show_records(project_data) {
    for (var i in project_data.records) {
        var url = project_data.records[i];
        $.getJSON(url, show_record);
    }
}

$(document).ready(function() {
    $.getJSON(window.location.href, show_records);
  });

$('.edit-form').on('submit', function() {
    $.ajax({ 
        type: "PUT",
        contentType: "application/json; charset=UTF-8",
        url: this.action, 
        data: JSON.stringify({"name": $("#prj-name").val(), "description": $("#prj-descr").val()}, null, 2),
        context: this,
        success: function(data, textStatus, jqXHR) {
            $("#edit_description").modal("hide");
            window.location.reload();
        },
        error: function(jqXHR, textStatus, errorThrown) {
            alert('something went wrong ' + textStatus + errorThrown);  
        }
    });
    return false;
});
