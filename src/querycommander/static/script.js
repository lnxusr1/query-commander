//var site_path = window.location.pathname;
var version = "v${VERSION}";
var timer;
var is_mouse_down = false;
var current_user = "";
var role_list = [];
var connection_list = [];
var connection_selected = "";
var tab_counter = 0;
var escape_key = false;
var fade_login = false;
var wss_url = '';
var editor_type = 'default';
var editors = {};
var connection_defaults = {};

$.ajaxSetup({
    cache: false
});

let no_cache_headers = {
};

function generate_url() {
    let baseUrl = window.location.pathname;
    let randomString = Math.random().toString(36).substring(2, 15);
    let timestamp = Date.now();
    let cacheBreaker = randomString + "_" + timestamp;
    let finalUrl = baseUrl + "?" + cacheBreaker;
    
    return finalUrl;
}

function getCookieValue(cookieName) {
    let name = cookieName + "=";
    let decodedCookies = decodeURIComponent(document.cookie); // Decode URI components
    let cookiesArray = decodedCookies.split(';'); // Split cookies into an array

    for (let i = 0; i < cookiesArray.length; i++) {
        let cookie = cookiesArray[i].trim(); // Trim any whitespace

        // Check if the cookie name matches
        if (cookie.indexOf(name) === 0) {
            return cookie.substring(name.length, cookie.length); // Return the cookie's value
        }
    }

    return null; // If the cookie isn't found
}

function highlightContents(divSelector) {
    var div = $(divSelector).get(0);  // Get the DOM element from the jQuery object

    if (window.getSelection && document.createRange) {
        var range = document.createRange();
        range.selectNodeContents(div);
        
        var selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
    }
}

function doGetCurrentDate() {
    var now = new Date();
    var month = now.getMonth() + 1; // Months are zero-based
    var day = now.getDate();
    var year = now.getFullYear();
    var hours = now.getHours();
    var minutes = now.getMinutes();
    var seconds = now.getSeconds();
    var ampm = hours >= 12 ? 'PM' : 'AM';

    // Convert 24-hour format to 12-hour format
    hours = hours % 12;
    hours = hours ? hours : 12; // the hour '0' should be '12'

    // Pad minutes and seconds with leading zeros
    minutes = minutes < 10 ? '0' + minutes : minutes;
    seconds = seconds < 10 ? '0' + seconds : seconds;

    var formattedDate = month + '/' + day + '/' + year + ' ' + hours + ':' + minutes + ':' + seconds + ' ' + ampm;
    return formattedDate;
}

function doClearTimer() {
    clearTimeout(timer);
}

function doStartTimer(delay=60000) {
    if (timer) { 
        clearTimeout(timer); // only clearing the timer so it can be reset
    }
    timer = setTimeout(function() { doCheckSession(); }, delay);
}

function doEnableSlider(box, slider_id, direction) {
    let block = $(box)[0];
    let slider = $(slider_id)[0];
    
    if ($(slider_id).hasClass('activated')) { return; }

    slider.onmousedown = function dragMouseDown(e) {
        let dragX = -1;
        if (direction == "vertical") {
            dragX = e.clientY;
        } else {
            dragX = e.clientX;
        }

        document.onmousemove = function onMouseMove(e) {
            if (direction == "vertical") {
                $(box).addClass('resized');
                block.style.height = block.offsetHeight + e.clientY - dragX + 'px';
                dragX = e.clientY;
            } else {
                block.style.width = block.offsetWidth + e.clientX - dragX + 'px';
                dragX = e.clientX;
            }
        }
        document.onmouseup = () => document.onmousemove = document.onmouseup = null;
    }

    $(slider_id).addClass('activated');
}

function selectTo(table, cell, ci_start, ri_start) {
    let row = cell.parent();
    let cidx = cell.index();
    let ridx = row.index();

    let r_start, r_end, c_start, c_end;

    if (ridx < ri_start) {
        r_start = ridx;
        r_end = ri_start;
    } else {
        r_start = ri_start;
        r_end = ridx;
    }

    if (cidx < ci_start) {
        c_start = cidx;
        c_end = ci_start;
    } else {
        c_start = ci_start;
        c_end = cidx;
    }

    for (let i = r_start; i <= r_end; i++) {
        let rc = table.find("tr").eq(i).find("td");
        for (let j = c_start; j <= c_end; j++) {
            rc.eq(j - 1).addClass('selected');
        }
    }
}

function selectColumn(table, cell, ci_start) {
    let cidx = cell.index();
    let c_start, c_end;

    if (cidx < ci_start) {
        c_start = cidx;
        c_end = ci_start;
    } else {
        c_start = ci_start;
        c_end = cidx;
    }

    if (c_start == 0) { c_end = table.find('tr').first().children().length - 1; }
    table.find('.selected').removeClass('selected');

    for (let i = 0; i <= table.find('tr').length; i++) {
        let rc = table.find("tr").eq(i).find("td");
        for (let j = c_start; j <= c_end; j++) {
            rc.eq(j - 1).addClass('selected');
        }
    }
}

function selectRow(table, cell, ri_start) {
    let ridx = cell.parent().parent().index();
    let r_start, r_end;

    if (ridx < ri_start) {
        r_start = ridx;
        r_end = ri_start;
    } else {
        r_start = ri_start;
        r_end = ridx;
    }

    for (let i = r_start; i <= r_end; i++) {
        table.find("tr").eq(i).find("td").addClass('selected');
    }
}

function doTableSort(container, column_index, sort_direction="ascending") {

    $(container).find('.selected').removeClass('.selected');

    var c_idx = column_index;
    var rows = $(container).find('table > tbody').children('tr').get();

    rows.sort(function(a, b) {
        let x = $(a).children().eq(c_idx).text().toLowerCase();
        let y = $(b).children().eq(c_idx).text().toLowerCase();

        if ($(a).children().eq(c_idx).children('data').hasClass('number')) { x = parseFloat(x); y = parseFloat(y); }

        if (sort_direction === "ascending") {
            if (x < y) return -1;
            if (x > y) return 1;
        } else {
            if (x < y) return 1;
            if (x > y) return -1;
        }
        return 0;
    });

    $.each(rows, function(index, row) {
        $(row).children().eq(0).find('data').text(index+1);
        $(container).find('table > tbody').append(row);
    });

    doApplyFilterOptions();
}

function doSimpleNotice(xhr) {
    $('.simple-notice a').trigger('click');
    $('.simple-notice a').off();
    $('.simple-notice a').click(function() {
        if (xhr) {
            try {
                xhr.abort();
            } catch {}
        }
        $('.simple-notice').hide();
        return false;
    });
    $('.simple-notice').show();

}

function doHideMenus() {
    $('.sidebar-context-menu').hide();
    $(".tab-list-items").removeClass('active');
    $('.database-select').hide();
    $('.simple-notice').hide();
}

function getMetaPath(obj) {
    let obj_path = {};
    let itm = obj.parent();
    while (true) {
        if (itm.prop('tagName') == "LI") {
            if (!(itm.attr('data-type') in obj_path)) {
                obj_path[itm.attr('data-type')] = itm.children('a').find('span').text();
            }
            itm = itm.parent().parent();
        } else {
            break;
        }
    }

    return obj_path;
}

function updateStatusBar() {

    setTimeout(function() {

        if (editor_type == "codemirror") {
            if ($('tab.active').hasClass('query')) {
                $('#cur_pos').text('0'); $('#sel_pos').text('0 : 0');
                let editor = editors[$('tab.active').prop('id')];

                let selection = editor.getSelection();
    
                if (selection) {
                    // Calculate number of lines and total length of the selection
                    let selectionStart = editor.getCursor("start");
                    let selectionEnd = editor.getCursor("end");
                    
                    let startLine = selectionStart.line;
                    let endLine = selectionEnd.line;
                    let startCh = selectionStart.ch;
                    let endCh = selectionEnd.ch;
            
                    let numLines = endLine - startLine + 1;
                    let totalLength = 0;
            
                    // Calculate total length of the selected text
                    for (let i = startLine; i <= endLine; i++) {
                        let lineContent = editor.getLine(i);
                        if (i === startLine && i === endLine) {
                            // Single line selection
                            totalLength = endCh - startCh;
                        } else if (i === startLine) {
                            // Start line
                            totalLength += lineContent.length - startCh;
                        } else if (i === endLine) {
                            // End line
                            totalLength += endCh;
                        } else {
                            // Middle lines
                            totalLength += lineContent.length;
                        }
                    }
                    
                    $('#sel_pos').text(totalLength + ' : ' + numLines);
                    return;
                }

                let cursor = editor.getCursor();
                let line = cursor.line;
                let column = cursor.ch;
                
                // Calculate the absolute position
                var absolutePosition = column; // Start with the column of the current line
                for (var i = 0; i < line; i++) {
                    absolutePosition += editor.getLine(i).length + 1; // +1 for the newline character
                }
                
                $('#cur_pos').text(absolutePosition);
            }
        } else {

            if ($('tab.active.query textarea.editor').val() === undefined) { $('#cur_pos').text('0'); $('#sel_pos').text('0 : 0'); return; }

            if ($('tab.active.query textarea.editor').is(':focus')) {
                $('#cur_pos').text('0');
                let p_loc = $('tab.active.query textarea.editor').prop("selectionEnd");
                if ($('tab.active.query textarea.editor').val().length == 0) { p_loc = 0; }
                if ((p_loc) && ($('tab.active.query textarea.editor').is(':focus'))) {
                    $('#cur_pos').text(p_loc);
                }

                $('#sel_pos').text('0 : 0');
                if (window.getSelection().toString()) {
                    let s = window.getSelection().toString();
                    let s_len = s.length;
                    let s_lines = (s.indexOf("\n") !== -1) ? s.split('\n').length : 1;
                    $('#sel_pos').text(s_len + ' : ' + s_lines);
                }
            }
        }
    }, 100);
}

function doManageTab(obj, is_shift) {
    let x = obj.val();
    let text_to_insert="    ";

    let p_start = obj[0].selectionStart; 
    let p_end = obj[0].selectionEnd
    //let new_value = x.slice(0,p_start)+text_to_insert+x.slice(p_start);

    let x_sel = x.slice(p_start, p_end);

    if (is_shift) {
        if (p_end != p_start) {
            x_sel = ("\n" + x_sel).replace(/(\r?\n)\s{4}/g, "\n").slice(1);
        }
    } else {
        x_sel = text_to_insert + x_sel.replace(/\n/g, "\n" + text_to_insert)
    }

    let new_value = x.slice(0,p_start) + x_sel + x.slice(p_end);
    obj.val(new_value);
    //obj.val(text_to_insert + x_sel);
    p_end = p_end + (x_sel.length - (p_end - p_start))
    if ((p_end - p_start) > 4) {
        obj[0].selectionStart = p_start;
    }
    obj[0].selectionEnd = p_end; // + text_to_insert.length;
}

function doLoadMore(tab_id) {
    if ($(tab_id + ' div.section.data').find('thead').first().hasClass('has-more')) {
        doExecuteSQL(tab_id, 'query', $(tab_id + ' div.section.statement > div').text(), true);
    }
}

function doGetSQL(tab_id) {
    let sql = '';

    if (editor_type == "codemirror") {
        let editor = editors[tab_id.slice(1)];
        let selectedText = editor.getSelection();
        if (selectedText) {
            return selectedText;
        } else {
            let fullContent = editor.getValue();
            return fullContent;
        }
    }

    $(tab_id + ' textarea.editor').focus(); 
    if ($(tab_id + ' textarea.editor').is(":focus")) {
        sql = window.getSelection().toString();
    }

    if (('' + sql).trim() == '') {
        
        sql = $(tab_id + ' textarea.editor').first().val();
    }

    return sql;
}

function doExecuteSQL(tab_id, exec_type, sql_statement='', as_more=false) {

    let sql = sql_statement
    if (sql_statement == '') {
        sql = doGetSQL(tab_id);
    }

    let connection_name = $('tablist > item > a.active').attr('connection');
    let db_name = $('tablist > item > a.active').attr('database');
    let schema_name = $('tablist > item > a.active').attr('schema');

    if ((sql == '') || (connection_name == '')) { return; }

    if ($(tab_id + ' > item:last-child').css('height') == '0px') {
        $(tab_id + ' > item:first-child').css('height', '48%');
    }

    $(tab_id + ' .btn-tab-results').trigger('click');
    let row_count = 0;
    if (as_more) { row_count = $(tab_id + ' div.section.data table > tbody > tr').length; }

    let req_data = {
        command: "query",
        type: exec_type,
        statement: sql,
        connection: connection_name,
        database: db_name,
        schema: schema_name,
        row_count: row_count
    }

    $(tab_id + ' div.section.data').addClass('is-loading');

    if (wss_url != '') {
        // web sockets

        $(tab_id + ' .tab-loading').find('.btn-stop-loading').trigger('click');
        $(tab_id + ' .tab-loading').find('.btn-stop-loading').off();

        $(tab_id + ' .tab-loading').css('display', '');
        $(tab_id + ' div.section.statement div').text(req_data["statement"]);

        let socket = new WebSocket(wss_url);
        let socket_timer = setTimeout(function() { $(tab_id + ' .tab-loading').find('.btn-stop-loading').trigger('click'); }, 960000); // 16 mins

        req_data["token"] = getCookieValue('token');
        req_data["username"] = getCookieValue('username');
        
        socket.onmessage = function(event) {
            let data = JSON.parse(event.data);

            if ((data.message) && (data.message == "Endpoint request timed out")) {
                return; // silently discard endpoint timeouts (lambda still running in background)
            }

            if (!as_more) {
                doClearQueryResults($(tab_id + ' div.section.data'));
            }

            if (!data.ok) {
                if (data.error) { alert(data.error); }
                if (data.logout) { doLogout(); }
                return;
            }

            if (data.data) {
                doLoadQueryData($(tab_id + ' div.section.data'), data.data, true, true, as_more);
            }

            socket.close();

        };
        
        socket.onclose = function(event) {
            clearTimeout(socket_timer);
            $(tab_id + ' .tab-loading').hide();
            $(tab_id + ' div.section.data').removeClass('is-loading');
        };

        socket.onopen = function(event) { 
            socket.send(JSON.stringify(req_data)); 
        };

        $(tab_id + ' .tab-loading').find('.btn-stop-loading').click(function() {
            try {
                socket.close();
            } catch (error) {
                console.error('An error occurred:', error.message);
            }

            if (!$(tab_id + ' .tab-loading').is(':visible')) {
                doClearQueryResults($(tab_id + ' div.section.data'));
            }

            $(tab_id + ' div.section.output div').text('Request cancelled.');
            $(tab_id + ' .btn-tab-output').trigger('click');
            $(tab_id + ' .tab-loading').hide();
            $(tab_id + ' div.section.data').removeClass('is-loading');

            return false;
        });

    } else {
        // ajax

        $.ajax({
            url: generate_url(),
            dataType: "json",
            method: "POST",
            headers: no_cache_headers,
            data: JSON.stringify(req_data),
            contentType: "application/json",
            beforeSend: function(xhr) {
                $(tab_id + ' .tab-loading').show();
                $(tab_id + ' div.section.statement div').text(req_data["statement"]);
                $(tab_id + ' .tab-loading').find('.btn-stop-loading').hide();

            },
            success: function(data) {
                if (!as_more) {
                    doClearQueryResults($(tab_id + ' div.section.data'));
                }

                if (!data.ok) {
                    if (data.error) { alert(data.error); }
                    if (data.logout) { doLogout(); }
                    return;
                }

                if (data.data) {
                    doLoadQueryData($(tab_id + ' div.section.data'), data.data, true, true, as_more);
                }
            },
            error: function(e) {
                doClearQueryResults($(tab_id + ' div.section.data'));
                $(tab_id + ' div.section.output div').text('An unexpected error occurred while executing the query.\nThis could be caused by a broken connection or malformed request.\n\nUnable to proceed.');
                $(tab_id + ' .btn-tab-output').trigger('click');
            },
            complete: function() {
                $(tab_id + ' .tab-loading').hide();
                $(tab_id + ' div.section.data').removeClass('is-loading');
            }
        });
    }
}

function doGetTableContents(container, selection=false, delimiter="\t") {

    let col_start = 1;
    let col_end = $(container).find('thead tr:first-child > th > data').length - 1;

    if (selection) {
        if ($(container).find('tbody > tr.show > td.selected').length > 0) {
            col_start = $(container).find('tbody > tr.show > td.selected').first().index();
            col_end = $(container).find('tbody > tr.show > td.selected').last().index();
        }
    }

    let content = '';
    $(container).find('thead tr:first-child > th > data').each(function(i, o) {
        if ((i >= col_start) && (i <= col_end)) {
            if (i > col_start) {
                content = content + delimiter;
            }

            let data_item = $(o).find('span').text();
            if ((data_item.includes(delimiter)) || (data_item.includes('"'))) {
                if (data_item.includes('"')) {
                    data_item = data_item.replace('"', '""');
                }
                content = content + '"' + data_item + '"';
            } else {
                content = content + data_item;
            }
        }
    });

    $(container).find('tbody tr.show').each(function(ir, tr) {
        if ((selection) && ($(tr).find('td.selected').length == 0)) { return; }
        if (content != "") { content = content + "\r\n"; }
        $(tr).children().each(function(i, o) {
            if ((i >= col_start) && (i <= col_end)) {

                if (i > col_start) {
                    content = content + delimiter;
                }

                let data_item = $(o).find('data').text();
                if ((data_item.includes(delimiter)) || (data_item.includes('"'))) {
                    if (data_item.includes('"')) {
                        data_item = data_item.replace('"', '""');
                    }
                    content = content + '"' + data_item + '"';
                } else {
                    content = content + data_item;
                }
            }
        });
    });

    return content;
}

function doApplyFilterOptions() {
    let headers = $('tab.active').find('.section.data').find('thead > tr');

    let sel_value = headers.attr('filter-text');

    let sel_compare = headers.attr('filter-type');
    let sel_idx = headers.find('th.selected').index();

    let rows = $('tab.active').find('.section.data').find('tbody').children();
    rows.removeClass('alt');

    if (sel_idx <= 0) {
        rows.removeClass('hide');
        rows.addClass('show');
    }

    if (sel_idx > 0) {
        for (let i=0; i<rows.length;i++) {
            let r_data = rows.eq(i).children().eq(sel_idx).find('data');
            let r_type = 'text';

            if (r_data.hasClass('number')) {
                r_type = 'number';
            }
            if (r_data.hasClass('date')) {
                r_type = 'date';
            }

            let r_val = r_data.text();

            if ((r_type == "number") && (["eq","gt","lt"].includes(sel_compare))) {
                r_val = parseFloat(r_val);
                sel_value = parseFloat(sel_value);
            }

            if (sel_compare == "sw") {
                if (!r_val.startsWith(sel_value)) {
                    rows.eq(i).removeClass('show');
                    rows.eq(i).addClass('hide');
                } else {
                    rows.eq(i).removeClass('hide');
                    rows.eq(i).addClass('show');
                }
            }

            if (sel_compare == "ew") {
                if (!r_val.endsWith(sel_value)) {
                    rows.eq(i).removeClass('show');
                    rows.eq(i).addClass('hide');
                } else {
                    rows.eq(i).removeClass('hide');
                    rows.eq(i).addClass('show');
                }
            }

            if (sel_compare == "cn") {
                if (!r_val.includes(sel_value)) {
                    rows.eq(i).removeClass('show');
                    rows.eq(i).addClass('hide');
                } else {
                    rows.eq(i).removeClass('hide');
                    rows.eq(i).addClass('show');
                }
            }

            if (sel_compare == "eq") {
                if (r_val != sel_value) {
                    rows.eq(i).removeClass('show');
                    rows.eq(i).addClass('hide');
                } else {
                    rows.eq(i).removeClass('hide');
                    rows.eq(i).addClass('show');
                }
            }

            if (sel_compare == "gt") {
                if (r_val <= sel_value) {
                    rows.eq(i).removeClass('show');
                    rows.eq(i).addClass('hide');
                } else {
                    rows.eq(i).removeClass('hide');
                    rows.eq(i).addClass('show');
                }
            }

            if (sel_compare == "lt") {
                if (r_val >= sel_value) {
                    rows.eq(i).removeClass('show');
                    rows.eq(i).addClass('hide');
                } else {
                    rows.eq(i).removeClass('hide');
                    rows.eq(i).addClass('show');
                }
            }
        }
    }

    $('tab.active').find('.section.data').find('tbody tr.show').each(function(i,o) {
        if (i % 2 == 0) {
            $(o).addClass('alt');
        }
    });

    $('#tab-filter-options').hide();
}

function doShowFilterOptions() {
    $('#sel-compare').find("option").prop('selected', false);

    let columns = $('#sel-column');
    columns.empty();

    let headers = $('tab.active').find('.section.data').find('thead > tr');
    $('#sel-value').val(headers.attr('filter-text'));

    for (let i = 1; i < headers.children().length; i++) {
        let o = headers.children().eq(i);
        let op = $('<option></option>');
        op.text(o.find('span').text());
        op.val(o.find('span').text());

        if (o.hasClass('selected')) {
            op.prop('selected', true);
        }

        columns.append(op);
    }

    let f_type = headers.attr('filter-type');
    if (f_type != '') {
        let copts = $('#sel-compare').find('option');
        for (let i = 0; i < copts.length; i++) {
            if (copts.eq(i).val() == f_type) {
                copts.eq(i).prop('selected', true);
            }
        }
    }

    $('#tab-filter-options').show();
}

function doClearQueryResults(container) {

    //$(container).parent().find('div.section.statement div').text('');
    $(container).parent().find('div.section.data div').scrollTop(0);
    $(container).parent().find('div.section.data div').scrollLeft(0);
    $(container).parent().find('div.section.output div').text('');
    $(container).parent().parent().find('.btn-tab-export').prop('disabled', true);
    $(container).parent().parent().find('.btn-tab-copy').prop('disabled', true);

    $(container).find('table th > data').off();
    $(container).find('table tbody td').off();
    $(container).find('table thead th data span').off();

    $(container).find('table thead').find('tr').remove();
    $(container).find('table tbody').find('tr').remove();
    $(container).find('resultsnav').find('button').prop('disabled', true);
    $(container).find('resultsnav').find('.metrics').text('');
}

function doLoadQueryData(container, data, with_types=true, with_numbers=true, as_more=false) {

    if ((data["error"]) && (data["error"] != "")) {
        doClearQueryResults(container);
        $(container).parent().find('div.section.output div').first().text(data["error"]);
        $(container).parent().parent().find('.btn-tab-output').first().trigger('click');
        return;
    }

    if (data["has_more"]) {
        $(container).find('thead').first().addClass('has-more');
    } else {
        $(container).find('thead').first().removeClass('has-more');
    }

    if (data["output"]) {
        $(container).parent().find('div.section.output div').first().text(data["output"]);
    }

    let record_start_count = container.find('tbody').children('tr').length;
    let records = record_start_count;

    if (data["headers"]) {
        if (!as_more) {
            container.find('thead').append($('<tr></tr>'));
            if ((data["headers"].length > 0) && (with_numbers)) {
                container.find('thead').find('tr').append($('<th><data></data></th>'));
            }
            for (let h=0; h<data["headers"].length; h++) {
                let el = $('<th><data><span></span></data></th>');
                el.find('data > span').append(data["headers"][h]["name"]);
                if (with_types) {
                    let data_type_class = "fa-font";
                    if (data["headers"][h]["type"] == "date") { data_type_class = "fa-clock"; }
                    if (data["headers"][h]["type"] == "number") { data_type_class = "fa-hashtag"; }
                    el.find('data').prepend($('<i class="data-type fas '+data_type_class+' fa-fw"></i>'));
                    el.find('data').append($('<i class="sort-order fas fa-caret-down fa-fw"></i>'));
                }
                container.find('thead').find('tr').append(el);
            }
        }

        if (data["records"]) {
            
            for (let r=0; r<data["records"].length; r++) {
                let tr = $('<tr class="show"></tr>');
                if (with_numbers) {
                    tr.append($('<th><data></data></th>'));
                    tr.find('data').text(records+r+1);
                }
                for (let c=0; c<data["records"][r].length; c++) {
                    let el = $('<td><data></data></td>');
                    el.find('data').text(data["records"][r][c]);
                    el.find('data').addClass(data["headers"][c]["type"]);
                    tr.append(el);
                }
                container.find('tbody').append(tr);
            }

            if (!as_more) {
                if (data["records"].length == 0) {
                    if (((data["output"]) && (data["output"].length > 0)) && (data["headers"].length == 0)) {
                        $(container).parent().parent().find('.btn-tab-output').first().trigger('click');
                    } else {
                        if (!$(container).parent().parent().find('.btn-tab-results').first().hasClass('active')) {
                            $(container).parent().parent().find('.btn-tab-results').first().trigger('click');
                        }
                    }
                    $(container).find('resultsnav').find('.btn-tab-refresh').prop('disabled', false);
                } else {
                    if (!$(container).parent().parent().find('.btn-tab-results').first().hasClass('active')) {
                        $(container).parent().parent().find('.btn-tab-results').first().trigger('click');
                    }

                    $(container).parent().parent().find('.btn-tab-export').prop('disabled', false);
                    $(container).parent().parent().find('.btn-tab-copy').prop('disabled', false);
                    
                    $(container).find('resultsnav').find('button').prop('disabled', false);
                    //$(container).find('resultsnav').find('.btn-tab-filter').prop('disabled', true);
                }
            }

            records = records + data["records"].length;
        }
    }

    if (data["stats"]) {
        //if (data["records"]) {
        //    records = data["records"].length;
        //}

        let secs = parseFloat('0.00').toFixed(2);
        if (data["stats"]["exec_time"]) {
            secs = parseFloat(data["stats"]["exec_time"]).toFixed(2);
        }

        $(container).parent().find('div.section.data .metrics').text(records + ' records - ' + doGetCurrentDate() + ' - ' + secs + ' secs')
    }

    $(container).find('table th > data > i.sort-order').click(function(event) {
        doHideMenus();
        if ($(this).hasClass('fa-caret-down')) {
            $(this).parent().parent().parent().find('i.sort-order').removeClass('fa-caret-up');
            $(this).parent().parent().parent().find('i.sort-order').addClass('fa-caret-down');
            $(this).parent().parent().parent().find('i.sort-order').css('opacity', '0.5');
            $(this).removeClass('fa-caret-down');
            $(this).addClass('fa-caret-up');
            $(this).css('opacity', '1');
            doTableSort($(this).parent().parent().parent().parent().parent().parent().parent(), $(this).parent().parent().index(), "ascending");
        } else {
            $(this).parent().parent().parent().find('i.sort-order').removeClass('fa-caret-up');
            $(this).parent().parent().parent().find('i.sort-order').addClass('fa-caret-down');
            $(this).parent().parent().parent().find('i.sort-order').css('opacity', '0.5');
            $(this).removeClass('fa-caret-up');
            $(this).addClass('fa-caret-down');
            $(this).css('opacity', '1');
            doTableSort(container, $(this).parent().parent().index(), "descending");
        }
        return false;
    });

    //$(container).find('table tbody tr td data').css('width', '120px');

    let extra_width = 0;
    if (with_numbers) {
        extra_width = 36;
    }

    $(container).find('table th > data').mousedown(function(e) {
        let t = $(this);
        document.onmousemove = function onMouseMove(e) {
            $(container).find('table tbody tr td:nth-child('+($(t).parent().index()+1)+') data').css('width', ($(t).width()+extra_width) + 'px');
        }
        document.onmouseup = function onMouseUp(e) {
            document.onmousemove = document.onmouseup = null;
        }
    });

    if (with_numbers) {
        let ci_start = null;
        let ri_start = null;
        let table = $(container).find('table tbody');

        table.find('td').off();
        table.find('td').mousedown(function(e) {
            is_mouse_down = true;
            let cell = $(this);

            table.find('.selected').removeClass('selected');
            cell.addClass('selected');
            // $('box.active output controls button.copy').prop('disabled', false);

            if (e.shiftKey) {
                selectTo(table, $(this), ci_start, ri_start);
            } else {
                cell.addClass("selected");
                // $('box.active output controls button.copy').prop('disabled', false);

                ci_start = cell.index();
                ri_start = cell.parent().index();
            }

            //return false;
        })
        .mouseover(function() {
            if (!is_mouse_down) return;
            // $('box.active output controls button.copy').prop('disabled', false);

            table.find('.selected').removeClass('selected');
            selectTo(table, $(this), ci_start, ri_start);
        })
        .bind("selectstart", function() {
            return false;
        });

        if (!as_more) {
            let table2 = $(container).find('table thead');

            table2.find('th data span').mousedown(function(e) {
                is_mouse_down = true;
                let cell = $(this).parent().parent();

                table.find('.selected').removeClass('selected');
                //$('box.active output controls button.copy').prop('disabled', false);
                
                if (e.shiftKey) {
                    selectColumn(table, $(this).parent().parent(), ci_start);
                } else {
                    ci_start = cell.index();
                    ri_start = cell.parent().index();
                    selectColumn(table, $(this).parent().parent(), ci_start);
                }

                //return false;
            })
            .mouseover(function() {
                if (!is_mouse_down) return;
                //$('box.active output controls button.copy').prop('disabled', false);
                //if ($(this).parent().index() == 0) { return; }
                table2.find('.selected').removeClass('selected');
                selectColumn(table, $(this).parent().parent(), ci_start);
            })
            .bind("selectstart", function() {
                return false;
            });
        }

        table.find('th data').off();
        table.find('th data').mousedown(function(e) {
            is_mouse_down = true;
            let cell = $(this).parent();

            table.find('.selected').removeClass('selected');
            //$('box.active output controls button.copy').prop('disabled', false);
            
            if (e.shiftKey) {
                selectRow(table, $(this), ri_start);
            } else {
                ci_start = 1;
                ri_start = cell.parent().index();
                selectRow(table, $(this), ri_start);
            }

            return false;
        })
        .mouseover(function() {
            if (!is_mouse_down) return;
            table.find('.selected').removeClass('selected');
            selectRow(table, $(this), ri_start);
        })
        .bind("selectstart", function() {
            return false;
        });
    }

    doApplyFilterOptions();
}

function doWireUpQueryTab(tab_id) {

    $(tab_id + ' textarea.editor').mouseup(function() { updateStatusBar(); });
    $(tab_id + ' textarea.editor').focus(function() { escape_key = false; });

    $(tab_id + ' textarea.editor').keyup(function(e) { 

        if (!(escape_key) && (e.keyCode == 9)) {
            e.preventDefault();
        }

        if (e.ctrlKey || e.metaKey) {
            if ((e.keyCode == 81) || (e.keyCode == 13)) {
                $('#btn-execute').trigger('click');
            }
        }

        escape_key = false;

        if (e.keyCode == 27) {
            // Esc
            escape_key = true;
        }

        updateStatusBar(); 
    });

    $(tab_id + ' textarea.editor').keydown(function(e) { 
        if (!(escape_key) && (e.keyCode == 9)) {
            // Tab
            e.preventDefault();

            doManageTab($(this), e.shiftKey);
            return false;
        }

        if (e.ctrlKey || e.metaKey) {
            if (e.keyCode == 83) {
                e.preventDefault();
                $('#btn-save-profile').trigger('click');
                return false;
            }
        }
    });

    $(tab_id + ' .tab-loading').hide();
    $(tab_id + ' item:first-child').css('height', '100%');
    doEnableSlider(tab_id + ' item:first-child', tab_id + ' slider', 'vertical');

    $(tab_id + ' .btn-tab-execute').click(function(event) { doHideMenus(); doExecuteSQL(tab_id, 'sql'); return false; });
    $(tab_id + ' .btn-tab-explain').click(function(event) { doHideMenus(); doExecuteSQL(tab_id, 'explain'); return false; });

    $(tab_id + ' .btn-tab-settings').click(function() { doHideMenus(); });
    
    $(tab_id + ' .btn-tab-results').click(function() {
        doHideMenus();
        $(tab_id + ' results > div.section').hide();
        $(tab_id + ' .data').show();
        $(tab_id + ' navmenu .active').removeClass('active');
        $(this).addClass('active');
        return false;
    });

    $(tab_id + ' .btn-tab-code').click(function() { 
        doHideMenus();
        $(tab_id + ' results > div.section').hide();
        $(tab_id + ' .statement').show();
        $(tab_id + ' navmenu .active').removeClass('active');
        $(this).addClass('active');
        return false;
    });

    $(tab_id + ' .btn-tab-output').click(function() { 
        doHideMenus();
        $(tab_id + ' results > div.section').hide();
        $(tab_id + ' .output').show();
        $(tab_id + ' navmenu .active').removeClass('active');
        $(this).addClass('active');
        return false;
    });

    $(tab_id + ' .btn-tab-export').click(function() { 
        doHideMenus();
        
        //TODO: Get content from loaded table
        let content = doGetTableContents($(tab_id + ' div.section.data'), false, ",");
        let blob = new Blob([content], { type: "text/plain" });
        let url = URL.createObjectURL(blob);
        let a = document.createElement('a');
        a.href = url;
        a.download = 'export.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        return false;
    });
    $(tab_id + ' .btn-tab-copy').click(function() { 
        doHideMenus();
        let content = '';

        if ($(tab_id + ' .btn-tab-results').hasClass('active')) {
            let selected_only = false;
            if ($(tab_id + ' div.section.data table').find('.selected').length > 0) {
                selected_only = true;
            }
    
            content = doGetTableContents($(tab_id + ' div.section.data'), selected_only);
        }

        if ($(tab_id + ' .btn-tab-code').hasClass('active')) {
            content = $(tab_id + ' .section.statement > div').text();
        }

        if ($(tab_id + ' .btn-tab-output').hasClass('active')) {
            content = $(tab_id + ' .section.output > div').text();
        }

        if (content != '') {
            navigator.clipboard
                .writeText(content)
                .then(() => {})
                .catch(() => { alert("Copy to Clipboard failed."); });
        }

        return false;
    });

    $(tab_id + ' .btn-tab-filter').click(function() { 
        doHideMenus(); 
        doShowFilterOptions();
        return false; 
    });

    $(tab_id + ' .btn-tab-first').click(function() { 
        doHideMenus();
        $(tab_id + ' .section.data table').find('.selected').removeClass('selected');
        let el = $(tab_id + ' .section.data table tbody > tr').first().find('td').first();
        el.addClass('selected');
        el.focus();

        $(tab_id + ' > item > results .data > div').scrollTop(0);
        
        return false; 
    });

    $(tab_id + ' .btn-tab-prev').click(function() { 
        doHideMenus();
        let idx = $(tab_id + ' .section.data table tbody > tr > td.selected').first().parent().index();
        $(tab_id + ' .section.data table').find('.selected').removeClass('selected');
        idx--;
        if (idx < 0) { idx = 0; }
        $(tab_id + ' .section.data table tbody').children('tr').eq(idx).children('td').first().addClass('selected');

        return false; 
    });

    $(tab_id + ' .btn-tab-next').click(function() { 
        doHideMenus();
        let idx = $(tab_id + ' .section.data table tbody > tr > td.selected').first().parent().index();
        $(tab_id + ' .section.data table').find('.selected').removeClass('selected');
        idx++;
        if (idx >= $(tab_id + ' .section.data table tbody').children('tr').length) { idx = $(tab_id + ' .section.data table tbody').children('tr').length - 1; }
        $(tab_id + ' .section.data table tbody').children('tr').eq(idx).children('td').first().addClass('selected');
        return false; 
    });

    $(tab_id + ' .btn-tab-last').click(function() { 
        doHideMenus();
        $(tab_id + ' .section.data table').find('.selected').removeClass('selected');
        let el = $(tab_id + ' .section.data table tbody > tr').last().find('td').first();
        el.addClass('selected');
        el.focus();

        $(tab_id + ' > item > results .data > div').scrollTop($(tab_id + ' > item > results .data > div > div:last-child').height());

        return false; 
    });

    $(tab_id + ' .btn-tab-refresh').click(function() { 
        doHideMenus();
        let sql_statement = $(tab_id + ' .section.statement > div').text();
        if (sql_statement.length > 0) {
            doExecuteSQL(tab_id, "query", sql_statement);
        }

        return false; 
    });

    $(tab_id + ' > item > results .data > div').scroll(function() {
        $(tab_id + ' > item > results .data > div > div:first-child table').css('top', '' + $(this).scrollTop() + 'px');
        $(tab_id + ' > item > results .data > div > div table tr > th:first-child').css('left', ($(this).scrollLeft()) + 'px');

        if ($(this).scrollTop() >= ($(this).children('div').eq(1).height() - Math.floor($(this).height()) + 25)) { 
            doLoadMore(tab_id);
        };
    });

    doClearQueryResults($(tab_id + ' .data'));
}

function doLoadSchemaList(tab_id) {
    if (!$('.database-select').find('div').eq(1).is(':visible')) {
        $('#btn-database').prop('disabled', false);
        return;
    } 

    let connection_name = $('#btn-connection').find('span').text();
    let database_name = $('.database-select').find('div').eq(0).find('a.selected').text();

    let qry2 = {
        command: "meta",
        path: { connection: connection_name, database: database_name },
        target: database_name,
        type: "schema-list"
    }

    $.ajax({
        url: generate_url(),
        dataType: "json",
        method: "POST",
        headers: no_cache_headers,
        data: JSON.stringify(qry2),
        contentType: "application/json",
        beforeSend: function() {
            $('#btn-database').prop('disabled', true);
        },
        complete: function() {
            $('#btn-database').prop('disabled', false);
        },
        success: function(data) {
            if (!data.ok) {
                if (data.error) { alert(data.error); }
                if (data.logout) { doLogout(); }
                return;
            }

            if ((!data.items) || (!Array.isArray(data.items))) {
                return;
            }

            if (data.items.length == 0) {
                return;
            }

            let dv = $('.database-select').find('div').eq(1);
            dv.empty();
            let schema_name = $('#btn-database').find('span').eq(2).text();
            for(let i=0;i<data.items.length;i++) {
                let opt = $('<a href="#"></a>');
                opt.text(data.items[i]);
                opt.click(function() {
                    $(this).parent().find('a').removeClass('selected');
                    $(this).addClass("selected");
                    let schema_name = $(this).text();
                    $('#btn-database').find('span').eq(2).text(schema_name);
                    $('tablist').find('a').each(function(x,o) {
                        if ($(o).attr('data-target') == '#' + tab_id) {
                            $(o).attr('schema', schema_name);
                        }
                    });
                    doHideMenus();
                    return false;
                });
                if (data.items[i] == schema_name) { opt.addClass("selected"); }
                opt.appendTo(dv);
            }

            if (dv.find('a.selected').length == 0) {
                dv.find('a').first().addClass('selected');
                let schema_name = dv.find('a').first().text();
                $('#btn-database').find('span').eq(2).text(schema_name);
                $('tablist').find('a').each(function(x,o) {
                    if ($(o).attr('data-target') == '#' + tab_id) {
                        $(o).attr('schema', schema_name);
                    }
                });
            }

        }
    });

}

function doLoadDBList() {
    let tab_id = $('tab.active').prop('id');

    let connection_name = $('#btn-connection').find('span').text();

    let qry1 = {
        command: "meta",
        path: { connection: connection_name },
        target: connection_name,
        type: "database-list"
    }

    $.ajax({
        url: generate_url(),
        dataType: "json",
        method: "POST",
        headers: no_cache_headers,
        data: JSON.stringify(qry1),
        contentType: "application/json",
        beforeSend: function() {
            $('#btn-database').prop('disabled', true);
        },
        success: function(data) {
            if (!data.ok) {
                if (data.error) { alert(data.error); }
                if (data.logout) { doLogout(); }
                return;
            }

            if ((!data.items) || (!Array.isArray(data.items))) {
                return;
            }

            if (data.items.length == 0) {
                return;
            }

            let dv = $('.database-select').find('div').eq(0);
            dv.empty();
            let db_name = $('#btn-database').find('span').eq(0).text();
            for(let i=0;i<data.items.length;i++) {
                let opt = $('<a href="#"></a>');
                opt.text(data.items[i]);
                opt.click(function() {
                    $(this).parent().find('a').removeClass('selected');
                    $(this).addClass("selected");
                    //if (!$('.database-select').find('div').eq(1).is(':visible')) {
                    let db_name = $(this).text();
                    $('#btn-database').find('span').eq(0).text(db_name);
                    $('tablist').find('a').each(function(x,o) {
                        if ($(o).attr('data-target') == '#' + tab_id) {
                            $(o).attr('database', db_name);
                        }
                    });
                    if (!$('.database-select').find('div').eq(1).is(':visible')) {
                        doHideMenus();
                    }
                    
                    doLoadSchemaList(tab_id);
                    return false;
                });
                if (data.items[i] == db_name) { opt.addClass("selected"); }
                opt.appendTo(dv);
            }

            doLoadSchemaList(tab_id);
            
        },
        error: function() {
            $('#btn-database').prop('disabled', false);
        }
    });
}

function doRefreshDBOptions() {

    let tab_id = $('tab.active').prop('id'); // b/c of async call
    let connection_name = $('#btn-connection').find('span').text();
    let database_name = $('#btn-database').find('span').eq(0).text();
    let schema_name = $('#btn-database').find('span').eq(2).text();

    if (schema_name != "<not set>") {
        if (database_name != "<not set>") {
            $('#btn-database').find('span').eq(0).show(); 
        }

        if ($('#btn-database').find('span').eq(2).text() != '') {
            $('#btn-database').find('span').eq(1).show(); 
        } else {
            $('#btn-database').find('span').eq(1).hide(); 
        }
        $('#btn-database').find('span').eq(2).show();
        return;
    }

    if (database_name != "<not set>") {
        let qry2 = {
            command: "meta",
            path: { connection: connection_name, database: database_name },
            target: database_name,
            type: "schema-list"
        }

        $.ajax({
            url: generate_url(),
            dataType: "json",
            method: "POST",
            headers: no_cache_headers,
            data: JSON.stringify(qry2),
            contentType: "application/json",
            beforeSend: function() {
                $('#btn-database').prop('disabled', true);
            },
            complete: function() {
                $('#btn-database').prop('disabled', false);
            },
            success: function(data) {
                if (!data.ok) {
                    if (data.error) { alert(data.error); }
                    if (data.logout) { doLogout(); }
                    return;
                }
    
                if ((!data.items) || (!Array.isArray(data.items))) {
                    $('#btn-database').find('span').eq(2).text('');
                    $('#btn-database').find('span').eq(1).hide(); 
                    $('#btn-database').find('span').eq(2).hide(); 
                    $('tablist').find('a').each(function(i,o) {
                        if ($(o).attr('data-target') == '#'+tab_id) {
                            $(o).attr('schema', '');
                            $(o).attr('db-only', '1');
                        }
                    });
                    return;
                }

                if (data.items.length == 0) { 
                    $('#btn-database').find('span').eq(1).hide(); 
                    $('#btn-database').find('span').eq(2).hide(); 
                } else {
                    if ($('#btn-database').find('span').eq(0).text() != '') {
                        $('#btn-database').find('span').eq(1).show(); 
                    }
                    $('#btn-database').find('span').eq(2).show();
                }
                
                $('#btn-database').find('span').eq(2).text(data.items[0]);
                $('tablist').find('a').each(function(i,o) {
                    if ($(o).attr('data-target') == '#'+tab_id) {
                        $(o).attr("schema", data.items[0]);
                        $(o).attr('db-only', '0');
                    }
                });
            }
        });

        return;
    }

    $('#btn-database').find('span').eq(1).hide();
    $('#btn-database').find('span').eq(2).hide();

    let qry1 = {
        command: "meta",
        path: { connection: connection_name },
        target: connection_name,
        type: "database-list"
    }

    $.ajax({
        url: generate_url(),
        dataType: "json",
        method: "POST",
        headers: no_cache_headers,
        data: JSON.stringify(qry1),
        contentType: "application/json",
        beforeSend: function() {
            $('#btn-database').prop('disabled', true);
        },
        success: function(data) {
            if (!data.ok) {
                if (data.error) { alert(data.error); }
                if (data.logout) { doLogout(); }
                return;
            }

            if ((!data.items) || (!Array.isArray(data.items))) {
                $('#btn-database').find('span').eq(0).hide();
                $('#btn-database').find('span').eq(0).text(''); // not supported by DB
                $('tablist').find('a').each(function(i,o) {
                    if ($(o).attr('data-target') == '#'+tab_id) {
                        $(o).attr('database', '');
                    }
                });
                doRefreshDBOptions();
                return;
            }

            if (data.items.length == 0) { 
                $('#btn-database').find('span').eq(0).hide(); 
            } else {
                $('#btn-database').find('span').eq(0).show(); 
            }
            
            $('#btn-database').find('span').eq(0).text(data.items[0]);
            $('tablist').find('a').each(function(i,o) {
                if ($(o).attr('data-target') == '#'+tab_id) {
                    $(o).attr('database', data.items[0]);
                }
            });

            doRefreshDBOptions();
        }
    });

}

function addQueryTab(check_exists, connection_name, database="", tab_name="", schema="", do_active=true, do_save=true) {

    if (connection_name != "") {
        if (((database == "") || (database == "<not set>")) && (connection_name in connection_defaults)) {
            let db_key = Object.keys(connection_defaults[connection_name])[0];
            if (db_key != "") {
                database = db_key
                if (((schema == "") || (schema == "<not set>")) && (database in connection_defaults[connection_name])) {
                    if (connection_defaults[connection_name][database] != "") {
                        schema = connection_defaults[connection_name][database];
                    }
                }
            }
        }
    }

    if (check_exists) {
        if ($('core > tablist').children().length > 2) { return; }
    }

    if (tab_name == "") { tab_name = connection_name; }

    let tab_id = 'tab'+tab_counter;
    tab_counter++;

    let tab_button = $('<item><a class="active" href="#"><span></span><button title="Close"><i class="fas fa-times"></i></button></a></item>');
    let tab = $('<tab class="query"></tab>');
    tab.html($('templates > tab_query').html())
    tab.prop('id', tab_id);
    if (!do_save) {
        tab.addClass('skip');
    }

    tab_button.find('a').attr('connection', connection_name);
    tab_button.find('a').attr('database', database);
    tab_button.find('a').attr('schema', schema);

    tab_button.find('span').text(tab_name);
    tab_button.find('a').attr('data-target', '#'+tab_id);
    tab_button.find('button').click(function() {
        doHideMenus();
        let t_id = $(this).parent().attr('data-target');
        
        if (editor_type == "codemirror") {
            let t_nm = t_id.slice(1);
            editors[t_nm].off('cursorActivity', updateStatusBar);
            delete editors[t_nm];
        }

        $(this).parent().parent().remove();
        $(t_id).remove();
        $('#btn-connection').hide();
        $('#btn-database').hide();

        $('core > tablist').find('a').first().trigger('click');
        return false;
    });

    tab_button.find('a').click(function() {
        doHideMenus();
        let t_id = $(this).attr('data-target');
        $('core > tab').removeClass('active');
        $(t_id).addClass('active');
        $('core > tablist > item > a').removeClass('active');
        $(this).addClass('active');
        $(t_id).find('textarea').focus();

        if (!$($(this).attr('data-target')).hasClass('skip')) {
            $('#btn-connection').show();
            $('#btn-database').show();

            $('#btn-connection').find('span').text($(this).attr('connection'));
            $('#btn-database').find('span').eq(0).text($(this).attr('database'));
            $('#btn-database').find('span').eq(2).text($(this).attr('schema'));
            doRefreshDBOptions();

            $('#btn-connection').css('display', 'inline-flex');
            $('#btn-database').css('display', 'inline-flex');
    
        } else {
            $('#btn-connection').hide();
            $('#btn-database').hide();
        }
        return false;
    });

    $('core > tablist > item > a').removeClass('active');
    $('core > tab').removeClass('active');

    $('core > tablist > item:first-child').after(tab_button);
    $('core').append(tab);
    tab.addClass('active');
    tab.find('textarea').prop('name','editor_'+tab_id);

    if (do_active) {
        tab_button.find('a').trigger('click');
    }

    /*
    let do_load_conns = true;
    for (let i=0; i<connection_list.length; i++) {
        if (connection_list[i]["name"] == connection_name) {
            if (["oracle","redshift"].includes(connection_list[i]["type"])) {
                tab.find('.editor-selector-area').hide();
                do_load_conns = false;
            }
        }
    }
    */

    editors[tab_id] = CodeMirror.fromTextArea($('#' + tab_id + ' textarea.editor')[0], {
        mode: 'text/x-sql',
        lineNumbers: true,
        theme: 'default',
        matchBrackets: true,
        scrollbarStyle: 'native',
        tabSize: 4,
        indentUnit: 4,
        indentWithTabs: false,
        extraKeys: {
            Tab: function(cm) {
                if (cm.somethingSelected()) {
                    cm.indentSelection("add");
                } else {
                    var spaces = Array(cm.getOption("indentUnit") + 1).join(" ");
                    cm.replaceSelection(spaces);
                }
            },
            "Shift-Tab": "indentLess",
            "Ctrl-Enter": function(cm) {
                $('#btn-execute').trigger('click');
            },
            "Ctrl-Q": function(cm) {
                $('#btn-execute').trigger('click');
            },
            "Ctrl-S": function(cm) {
                $('#btn-save-profile').trigger('click');
            }
        }
      });

      editors[tab_id].on('cursorActivity', updateStatusBar);

    doWireUpQueryTab('#' + tab_id);

    $('#' + tab_id + ' textarea.editor').focus();

    //$('#' + tab_id + ' > item:first-child select').children().remove();
    //let o = $('<option></option>');
    //o.val(database);
    //o.text(database);
    //o.prop('selected', true);
    //$('#' + tab_id + ' > item:first-child select').append(o);

    /*
    let databases = [];

    if (!do_load_conns) {
        return;
    }


    if (databases != null) {
        if (databases) {
            databases.sort();
            for (let i = 0; i<databases.length; i++) {
                let o = $('<option></option>');
                o.val(databases[i]);
                o.text(databases[i]);
                if (databases[i] == database) { o.prop('selected', true); }
                $('#' + tab_id + ' > item:first-child select').append(o);
            }
        }

        return;
    }

    let meta_request = {
        command: "meta", 
        target: connection_name, 
        type: "connection", 
        path: {
            connection: connection_name
        }
    };

    $.ajax({
        url: generate_url(),
        dataType: "json",
        method: "POST",
        headers: no_cache_headers,
        data: JSON.stringify(meta_request),
        contentType: "application/json",
        beforeSend: function(xhr) {
            $('#' + tab_id + ' > item:first-child select').empty();
            $('#' + tab_id + ' > item:first-child .loading').show();
        },
        success: function(data) {
            if (!data.ok) {
                if (data.error) { alert(data.error); }
                let o = $('<option></option>');
                o.val('');
                o.text('<default>');
                $('#' + tab_id + ' > item:first-child select').append(o);
                if (data.logout) { doLogout(); }
                return;
            }
            if (data.items) {
                data.items.sort();
                for (let i = 0; i<data.items.length; i++) {
                    let o = $('<option></option>');
                    o.val(data.items[i]);
                    o.text(data.items[i]);
                    if (data.items[i] == database) { o.prop('selected', true); }
                    $('#' + tab_id + ' > item:first-child select').append(o);
                }
            }
        },
        complete: function() {
            $('#' + tab_id + ' > item:first-child .loading').hide();
        },
        error: function(e) {

        }
    });

    */

    return tab_id;

}

function doAddDetailTab(obj_details) {
    
    //let data_encoded = JSON.stringify(obj_details);
    obj_details["command"] = "details";

    $.ajax({
        url: generate_url(),
        dataType: "json",
        method: "POST",
        headers: no_cache_headers,
        data: JSON.stringify(obj_details),
        contentType: "application/json",
        beforeSend: function(xhr) {
            doSimpleNotice(xhr);
        },
        complete: function() {
            doHideMenus();
        },
        success: function(data) {
            if (!data.ok) {
                if (data.error) { alert(data.error); }
                if (data.logout) { doLogout(); }
                return;
            }

            let tab_id = 'tab'+tab_counter;
            tab_counter++;

            let tab_button = $('<item><a class="active" href="#"><span></span><button title="Close"><i class="fas fa-times"></i></button></a></item>');
            let tab = $('<tab class="properties"></tab>');
            tab.html($('templates > tab_properties').html())
            tab.prop('id', tab_id);    

            tab_button.find('span').text(obj_details["target"]);
            tab_button.find('a').attr('data-target', '#'+tab_id);
            tab_button.find('button').click(function() {
                doHideMenus();
                let t_id = $(this).parent().attr('data-target');
                $(this).parent().parent().remove();
                $(t_id).remove();
                $('core > tablist').find('a').first().trigger('click');
                return false;
            });

            tab_button.find('a').click(function() {
                doHideMenus();
                let t_id = $(this).attr('data-target');
                $('core > tab').removeClass('active');
                $(t_id).addClass('active');
                $('core > tablist > item > a').removeClass('active');
                $(this).addClass('active');
                $(t_id).find('textarea').focus();

                $('#btn-connection').hide();
                $('#btn-database').hide();
        
                return false;
            });

            $('core > tablist > item > a').removeClass('active');
            $('core > tab').removeClass('active');

            $('core > tablist > item:first-child').after(tab_button);
            $('core').append(tab);
            tab.addClass('active');

            obj_details["breadcrumbs"].reverse();
            tab.find('breadcrumbs').text(obj_details["breadcrumbs"].join(' : '));

            $('#' + tab_id + ' settings > div').empty();
            for (let i=0; i < data.properties.meta.length; i++) {
                let itm = $('<item><text></text><value><data></data></value></item>');
                itm.find('text').text(data.properties.meta[i]["name"]);
                itm.find('data').text(data.properties.meta[i]["value"]);

                if (i % 2 == 0) {
                    itm.appendTo($('#' + tab_id + ' settings > div:first-child'));
                } else {
                    itm.appendTo($('#' + tab_id + ' settings > div:last-child'));
                }
            }

            $('#' + tab_id + ' propdetail .action-buttons').empty();
            $('#' + tab_id + ' propdetail .section').remove();

            let c=0;
            Object.keys(data.properties.sections).forEach(function (key) {

                c++;

                let sec_dtl = data.properties.sections[key];
                let btn = $('<button></button>');
                btn.text(key);
                btn.appendTo($('#' + tab_id + ' .action-buttons'));
                btn.attr('item-id', c);
                btn.click(function() {
                    doHideMenus();
                    $(this).parent().find('.active').removeClass("active");
                    $(this).addClass("active");
                    $(this).parent().parent().children('div.section').hide();
                    $(this).parent().parent().children('div').eq($(this).attr('item-id')).show();
                });

                let content = $('<div class="section"></div>');
                content.addClass(sec_dtl["type"]);
                content.html($('templates tab_properties div.section.' + sec_dtl["type"]).html());
                content.appendTo('#' + tab_id + ' propdetail');

                if (sec_dtl["type"] == "code") {
                    let dv = $('<div></div>');
                    dv.text(sec_dtl["data"]);
                    content.append(dv);
                }

                if (sec_dtl["type"] == "table") {
                    doClearQueryResults(content);
                    doLoadQueryData(content, sec_dtl, false, false);
                }

                content.scroll(function() {
                    $(this).find('div:first-child > table').css('top', '' + $(this).scrollTop() + 'px')
                });

            });

            $('#' + tab_id + ' propdetail .action-buttons').find('button').first().trigger('click');
            let height = 0;
            height = height + $('body > toolbar').height();
            height = height + $('body > statusbar').height();
            height = height + $('tablist').height();
            height = height + $('#' + tab_id + ' properties').height();
            height = height + 4;
            $('#' + tab_id + ' propdetail .section').css('height', 'calc(100vh - '+height+'px)');

            if (tab_button.find('a').hasClass('active')) { tab_button.find('a').trigger('click'); }
        }
    });


}

function doGenerateDDL(obj_details) {
    
    let data_encoded = JSON.stringify(obj_details);
    obj_details["command"] = "ddl";
    
    $.ajax({
        url: generate_url(),
        dataType: "json",
        method: "POST",
        headers: no_cache_headers,
        data: JSON.stringify(obj_details),
        contentType: "application/json",
        beforeSend: function(xhr) {
            doSimpleNotice(xhr);
        },
        success: function(data) {
            if (!data.ok) {
                if (data.error) { alert(data.error); }
                if (data.logout) { doLogout(); }
                return;
            }

            $('overlay.chooser#ddl-data .message-box .message').attr('obj-details', data_encoded);
            $('overlay.chooser#ddl-data .message-box .message').text(data.ddl);

            $('overlay.chooser#ddl-data .btn-chooser-close').off();
            $('overlay.chooser#ddl-data .btn-chooser-close').click(function() { doHideMenus(); $('overlay.chooser#ddl-data').hide(); return false; });

            $('overlay.chooser#ddl-data .btn-chooser-refresh').off();
            $('overlay.chooser#ddl-data .btn-chooser-refresh').click(function() { 
                doHideMenus();
                let data_decoded = JSON.parse($('overlay.chooser#ddl-data .message-box .message').first().attr('obj-details'));
                doGenerateDDL(data_decoded); 
                return false; 
            });

            $('overlay.chooser#ddl-data .btn-chooser-copy').off();
            $('overlay.chooser#ddl-data .btn-chooser-copy').click(function() {
                doHideMenus();
                navigator.clipboard
                    .writeText($('overlay.chooser#ddl-data .message-box .message').text())
                    .then(() => {})
                    .catch(() => { alert("Copy to Clipboard failed."); });

                return false;
            });
            $('overlay.chooser#ddl-data').show();
        },
        complete: function() {
            doHideMenus();
        }
    });
}

function doLoadContextData(obj, type_name) {
    let target = $(obj).find('span').text();
    let data = { command: "details", type: type_name, target: "sql", path: { connection: target } }

    $.ajax({
        url: generate_url(),
        dataType: "json",
        method: "POST",
        headers: no_cache_headers,
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function(data) {
            let sql_statement = data["properties"]["sections"]["Source"]["data"];
            let tab_title = "Sessions";
            if (type_name == "locks") {
                tab_title = "Locks";
            }

            addQueryTab(false, target, '', tab_title+' ['+target+']', '', true, false);
            $('tab.active').children().eq(0).css('height','0px');        
            if (editor_type == "codemirror") {
                editors[$('tab.active').prop('id')].setValue(sql_statement);
            } else {
                $('tab.active').find('.editor').val(sql_statement);
            }
            $('#btn-execute').trigger("click");
        }
    });

    $(obj).removeClass("highlight");
    $('.sidebar-context-menu').hide();
}

function doLoadContextMenu(obj, event, menu_items) {
    doHideMenus();
    doCloseContextMenu();
    $(obj).addClass('highlight');
    $('.sidebar-context-menu a').off();

    let obj_path = getMetaPath(obj);

    $('.sidebar-context-menu > ul > li').hide();
    for (let z=0; z < menu_items.length; z++) {
        if (menu_items[z] == "refresh") { $('#btn-context-refresh-item').parent().show(); }
        if (menu_items[z] == "copy") { $('#btn-context-copy-name').parent().show(); }
        if (menu_items[z] == "extra") { $('.context-extra').show(); }
        if (menu_items[z] == "ddl") { $('.sidebar-context-menu > ul > li.optional').show(); }
        if (menu_items[z] == "details") { $('#btn-context-view-details').parent().show(); }
        if (menu_items[z] == "tab") { 
            $('.sidebar-context-menu > ul > li.new-tab').show(); 
            if ((!obj_path.database) && (!obj_path.schema)) {
                $('.sidebar-context-menu > ul > li.connection-only').hide(); 
            }
        }
    }

    $('#btn-set-default').click(function() {
        doHideMenus();
        if ((obj_path.connection) && (obj_path.connection != "")) {
            if (!(obj_path.connection in connection_defaults)) {
                connection_defaults[obj_path.connection] = {};
            }

            if ((obj_path.database) && (obj_path.database != "")) {
                if (!(obj_path.database in connection_defaults[obj_path.connection])) {
                    connection_defaults[obj_path.connection] = {};
                    connection_defaults[obj_path.connection][obj_path.database] = "";
                }

                if ((obj_path.schema) && (obj_path.schema != "")) {
                    connection_defaults[obj_path.connection][obj_path.database] = obj_path.schema;
                }
            }
        }

        alert('Default set successfully.');

        return false;
    });

    $('#btn-context-refresh-item').click(function() {
        doHideMenus();
        $(obj).removeClass("loaded");
        $(obj).removeClass("expanded");
        $(obj).removeClass("highlight");
        $(obj).parent().children('ul').remove();
        $(obj).trigger('click');
        $('.sidebar-context-menu').hide();
        return false;
    });

    $('#btn-new-tab').click(function() {
        doHideMenus();
        
        let obj_path = getMetaPath(obj);
        let conn_name = obj_path.connection;
        let db_name = (obj_path.database) ? obj_path.database : '<not set>';
        let schema_name = (obj_path.schema) ? obj_path.schema : '<not set>';

        addQueryTab(false, conn_name, db_name, conn_name, schema_name);
        return false;
    });

    $('#btn-context-sessions').click(function() {
        doHideMenus();
        doLoadContextData(obj, "sessions");
        return false;        
    });

    $('#btn-context-locks').click(function() {
        doHideMenus();
        doLoadContextData(obj, "locks");
        return false;
    });

    $('#btn-context-copy-name').click(function() {
        doHideMenus();
        $(obj).removeClass("highlight");

        navigator.clipboard
            .writeText($(obj).find('span').text())
            .then(() => {})
            .catch(() => { alert("Copy to Clipboard failed."); });

        $('.sidebar-context-menu').hide();
        return false;
    });

    $('#btn-context-generate-ddl').click(function() {
        doHideMenus();
        
        let obj_path = getMetaPath(obj);

        doGenerateDDL({
            target: $(obj).find('span').text(),
            type: $(obj).parent().attr('data-type'),
            path: obj_path
        });

        $(obj).removeClass("highlight");
        $('.sidebar-context-menu').hide();
        return false;
    });

    $('#btn-context-view-details').click(function() {
        doHideMenus();
        let obj_path = {};
        let itm = $(obj).parent();
        let breadcrumbs = [];
        while (true) {
            if (itm.prop('tagName') == "LI") {
                if (!(itm.attr('data-type') in obj_path)) {
                    obj_path[itm.attr('data-type')] = itm.children('a').find('span').text();
                    if (!itm.attr('data-type').includes("folder")) {
                        breadcrumbs.push(itm.children('a').find('span').text());
                    }
                }
                itm = itm.parent().parent();
            } else {
                break;
            }
        }

        doAddDetailTab({
            target: $(obj).find('span').text(),
            type: $(obj).parent().attr('data-type'),
            path: obj_path,
            breadcrumbs: breadcrumbs
        });

        $(obj).removeClass("highlight");
        $('.sidebar-context-menu').hide();
        return false;
    });

    $('.sidebar-context-menu').css(
        {
            display: "block",
            top: event.pageY + "px",
            left: event.pageX + "px"
        }
    );
}

function doCloseContextMenu() {
    $('.sidebar-context-menu').hide();
    $('a.highlight').removeClass('highlight');
}

function doLoadMeta(obj) {
    doHideMenus();
    doCloseContextMenu();

    if ($(obj).hasClass('expanded')) {
        $(obj).removeClass('expanded');
        $(obj).parent().children('ul').hide();
    } else {

        if ($(obj).hasClass('loaded')) {
            $(obj).addClass("expanded");
            $(obj).parent().children('ul').show();
            return;
        }

        $(obj).addClass('loading');
        let obj_path = getMetaPath(obj);

        let data = {
            command: "meta",
            target: $(obj).find('span').text(),
            type: $(obj).parent().attr('data-type'),
            path: obj_path
        }

        $.ajax({
            url: generate_url(),
            dataType: "json",
            method: "POST",
            headers: no_cache_headers,
            data: JSON.stringify(data),
            contentType: "application/json",
            success: function(data) {
                if (!data.ok) {
                    if (data.error) { alert(data.error); }
                    if (data.logout) { doLogout(); }
                    return;
                }

                let ul = $('<ul></ul>');
                for (let i=0; i < data.items.length; i++) {
                    let el = $('<li><a href="#"><i class="fa fa-fw"></i><span></span></a></li>');
                    el.attr('data-type', data.meta.type)
                    el.find('span').text(data.items[i]);
                    el.appendTo(ul);
                    for (let x=0; x < data.meta.classes.length; x++) {
                        el.find('i').addClass(data.meta.classes[x]);
                    }
                    el.find('i').css('color', data.meta.color);
                    if (!data.meta.children) {
                        el.find('a').addClass('loaded');
                        el.find('a').addClass('empty');
                    }
                    el.find('a').on('contextmenu', function(event) { doLoadContextMenu($(this), event, data.meta.menu_items); return false; });        
                    el.find('a').click(function() {
                        doHideMenus();
                        doLoadMeta($(this));
                        return false; 
                    });
                }

                ul.appendTo($(obj).parent());
                if (data.items.length > 0) {
                    $(obj).addClass("expanded");
                    $(obj).parent().children('ul').show();
                } else {
                    $(obj).addClass("empty");
                }
                $(obj).addClass("loaded");
            },
            complete: function() {
                $(obj).removeClass('loading');
            },
            error: function() {

            }
        });
    }
}

function doClearPage() {

    doRefreshConnections();
    $('core > tablist').empty();
    $('<item><div style="width: 25px;"></div></item>').appendTo($('core > tablist'));
    $('<item></item>').appendTo($('core > tablist'));
    $('tab').remove();
}

function doRefreshConnections() {
    $('sidebar > metadata > ul').empty();
    
    connection_list.sort((a, b) => {
        if (a.name < b.name) {
          return -1;
        }
        if (a.name > b.name) {
          return 1;
        }
        return 0;
      });
    for (let i = 0; i < connection_list.length; i++) {
        let el = $('<li data-type="connection"><a href="#"><i class="fa fa-server fa-fw"></i><span></span><server-type></server-type></a></li>');
        el.find('span').text(connection_list[i]["name"]);
        el.find('server-type').text(connection_list[i]["type"]);
        el.appendTo($('sidebar > metadata > ul'));
        el.find('a').prop('title', connection_list[i]["type"]);
        el.find('a').on('contextmenu', function(event) { doLoadContextMenu($(this), event, ["refresh", "extra", "tab"]); return false; });        
        el.find('a').click(function() {
            doHideMenus();
            doLoadMeta($(this));
            return false; 
        });
    }
}

function doShowConnectionDialog(update_tab=false) {
    if (update_tab) {
        $('#chooser-select-connection').attr('tabupdate', 'yes');
    } else {
        $('#chooser-select-connection').attr('tabupdate', 'no');
    }

    connection_list.sort((a, b) => {
        if (a.name < b.name) {
          return -1;
        }
        if (a.name > b.name) {
          return 1;
        }
        return 0;
      });
    $('#chooser-select-connection .message').find('ul').empty();

    for (let i = 0; i < connection_list.length; i++) {
        let option = $('<li><input/><label></label></li>');
        option.find('input').prop('type','radio');
        option.find('input').prop('name','connection');
        option.find('input').val(connection_list[i]["name"]);
        option.find('input').prop('id','connection'+i);
        option.find('label').prop('for','connection'+i);
        let el1 = $('<span></span>');
        el1.text(connection_list[i]["name"])
        let el2 = $('<span></span>');
        el2.text(connection_list[i]["type"])
        option.find('label').append(el1);
        option.find('label').append(el2);

        option.appendTo($('#chooser-select-connection .message').find('ul'));
    }

    if (connection_selected == "") {
        $('#chooser-select-connection').find('ul').find('input').first().prop('checked', true);
    } else {
        $('#chooser-select-connection').find('ul').find('input').each(function(i,o) {
            if ($(o).val() == connection_selected) {
                $(o).prop('checked', true);
            }
        });
    }

    if ($('input[name="connection"]:checked').val() == "") {
        $('#chooser-select-connection').find('ul').find('input').first().prop('checked', true);
    }

    $('#chooser-select-connection').fadeIn('fast');
}

function doOpenForm() {
    if ($('core > tablist').children().length == 2) {
        if (connection_selected != "") { 
            addQueryTab(true, connection_selected, "<not set>", connection_selected, "<not set>");
        } else {
            doShowConnectionDialog();
        }
    }

    $('#page-loading').hide();

    if (!fade_login) {
        $('#login').hide();
    } else {
        $('#login').fadeOut('fast');
    }

    doDisableLoginLoading();
}

function doLoginSuccess(data, hide_login) {
    if (current_user != data.username) {
        doClearPage();
        current_user = data.username;
    }

    connection_list = data.connections;
    editor_type = data.editor;

    doStartTimer();

    if (connection_selected == "") {
        doRefreshConnections();

        if (connection_list.length == 1) {
            connection_selected = connection_list[0]["name"];
        }
    }

    if (data.web_socket) { wss_url = data.web_socket; }

    if (data.profiles) {
        doLoadProfile();
    } else {
        $('#btn-save-profile').prop('disabled', true);
        $('#btn-save-profile').hide();
        doOpenForm();
    }

}

function doDisableLoginLoading() {
    $('#username').prop('disabled', false);
    $('#password').prop('disabled', false);
    $('#btn-login').prop('disabled', false);
    $('#span-login').show();
    $('#span-login-loading').hide();
}

function doLogin() { 

    fade_login = true;
    role_list = [];
    connection_list = [];
    connection_selected = "";
    tab_counter = 0;

    doClearPage();

    let this_user = $('#username').val();
    $('#username').removeClass('error');
    $('#password').removeClass('error');
    $('#login-error').hide();

    if (($("#username").val() == "") || ($("#password").val() == "")) { 
        $('#username').addClass('error'); 
        $('#password').addClass('error'); 
        $('#login-error').text('Invalid or missing username or password.');
        $('#login-error').show(); 
        return false; 
    }

    let data = {
        "command": "login",
        "username": $('#username').val(),
        "password": $('#password').val()
    }

    $('#password').val('');

    $.ajax({
        url: generate_url(),
        dataType: "json",
        method: "POST",
        headers: no_cache_headers,
        data: JSON.stringify(data),
        contentType: "application/json",
        beforeSend: function(xhr) {
            $('#username').prop('disabled', true);
            $('#password').prop('disabled', true);
            $('#btn-login').prop('disabled', true);
            $('#span-login').hide();
            $('#span-login-loading').show();
        },
        error: function() {
            $('#login-error').text('An error occurred attempting to connect to the service.');
            $('#login-error').show();        
        },
        success: function(data) {
            if (data.ok) {
                doLoginSuccess(data, false);
            } else {
                $('#login-error').text('Login failed.  Invalid username or password.');
                $('#login-error').show();

                doDisableLoginLoading();
                return;
            }
        },
        complete: function() {
        }
    });
}

function doLogout() { 
    doClearPage();
    doClearTimer();
    is_mouse_down=false;

    $.ajax({
        url: generate_url(),
        dataType: "json",
        method: "POST",
        headers: no_cache_headers,
        data: JSON.stringify({ "command": "logout" }),
        contentType: "application/json",
        beforeSend: function(xhr) {
            $('#username').prop('disabled', true);
            $('#password').prop('disabled', true);
            $('#btn-login').prop('disabled', true);
        },
        error: function() {
            $('#login-error').text('Call failed.  Please try again.');
            $('#login-error').show();
            $('#login').fadeIn('fast');
        },
        complete: function(data) {
            doDisableLoginLoading();
            $('#login').fadeIn('fast');

        }
    });
}

function doCheckSession(extend=false) {
    let data = {
        "command": "check",
        "extend": extend
    }

    $.ajax({
        url: generate_url(),
        dataType: "json",
        method: "POST",
        headers: no_cache_headers,
        data: JSON.stringify(data),
        contentType: "application/json",
        error: function() {
            $('#page-loading').hide();
            alert('Warning: An error occurred attempting to connect to the service.');
            doStartTimer();
        },
        success: function(data) {
            if (!data.ok) {
                $('#login').show();
                $('#username').focus();
                $('#page-loading').hide();
                doClearTimer();
            } else {
                if (extend) {
                    doLoginSuccess(data, true);
                } else {
                    doStartTimer();
                }
            }
        }
    });
}

function doLoadProfile() {

    let data = {
        command: 'get-profile'
    }

    $.ajax({
        url: generate_url(),
        dataType: "json",
        method: "POST",
        headers: no_cache_headers,
        data: JSON.stringify(data),
        contentType: "application/json",
        error: function() {
        },
        success: function(data) {
            if (!data.ok) {
                alert("Unable to get profile.");
                if (data.logout) { doLogout(); }
                return;
            }

            if ((data.defaults) && (data.defaults.connections)) {
                connection_defaults = data.defaults.connections;
            }

            if (data.tabs) {
                let tab_id = '';
                for (let i=data.tabs.length-1; i>=0; i--) {
                    tab_id = addQueryTab(false, data.tabs[i]["connection"], data.tabs[i]["database"], data.tabs[i]["name"], data.tabs[i]["schema"], false);
                    $('tablist').find('a').each(function(x,o) {
                        if ($(o).attr('data-target') == '#' + tab_id) {
                            $(o).attr('db-only', data.tabs[i]["db_only"]);
                        }
                    });

                    if (editor_type == "codemirror") {
                        editors[tab_id].setValue(data.tabs[i]["content"]);
                    } else {
                        $('#'+tab_id+' textarea.editor').val(data.tabs[i]["content"]);
                    }
                }
                if (tab_id != '') {
                    $('tablist').find('a').each(function(i,o) {
                        if ($(o).attr('data-target') == '#'+tab_id) {
                            $(o).trigger('click');
                            return;
                        }
                    });
                }
            }
        },
        complete: function() {
            doOpenForm();
        }
    })
}

function doSaveProfile() {
    let tab_items = [];
    $('tablist').find('item').each(function(i,o) {
        if ((i == 0) || (i >= $('tablist').find('item').length - 1)) { return; }
        if ($($(o).find('a').attr('data-target')).hasClass('skip')) { return; }
        if (!$($(o).find('a').attr('data-target')).hasClass('query')) { return; }

        let tab_name = $(o).find('a').text();
        let tab_connection = $(o).find('a').attr('connection');
        let tab_content = '';

        if (editor_type == "codemirror") {
            tab_content = editors[$($(o).find('a').attr('data-target')).prop('id')].getValue();
        } else {
            tab_content = $($(o).find('a').attr('data-target')).find('.editor').val();
        }

        let tab_db_name = $(o).find('a').attr('database');
        let tab_db_schema = $(o).find('a').attr('schema');
        let tab_db_only = $(o).find('a').attr('db-only');
        if (tab_db_only != '1') { tab_db_only = '0'; }

        if (tab_name != '') {
            let tab_data = {
                name: tab_name,
                connection: tab_connection,
                database: tab_db_name,
                schema: tab_db_schema,
                db_only: tab_db_only,
                content: tab_content
            }

            tab_items.push(tab_data);
        }
    });

    let data = {
        command: "save-profile",
        tabs: tab_items,
        settings: {},
        defaults: {
            connections: connection_defaults
        }
    }

    $.ajax({
        url: generate_url(),
        dataType: "json",
        method: "POST",
        headers: no_cache_headers,
        data: JSON.stringify(data),
        contentType: "application/json",
        beforeSend: function(xhr) {
            $('#btn-save-profile').children().eq(0).show();
            $('#btn-save-profile').children().eq(0).removeClass('fa-floppy-disk');
            $('#btn-save-profile').children().eq(0).removeClass('fa-check');                
            $('#btn-save-profile').children().eq(0).addClass('fa-spinner');
            $('#btn-save-profile').children().eq(0).addClass('fa-spin');
        },
        error: function() {
        },
        success: function(data) {
            if (data.ok) {
            } else {
                if (data.logout) { doLogout(); return; }
                alert("Unable to save profile.");
            }
        },
        complete: function() {
            $('#btn-save-profile').children().eq(0).addClass('fa-check');
            $('#btn-save-profile').children().eq(0).removeClass('fa-spinner');
            $('#btn-save-profile').children().eq(0).removeClass('fa-spin');
            setTimeout(function() {
                $('#btn-save-profile').children().eq(0).fadeTo(300, .1, function() { 
                    $('#btn-save-profile').children().eq(0).removeClass('fa-check');                
                    $('#btn-save-profile').children().eq(0).addClass('fa-floppy-disk');
                }).delay(100).fadeTo(100, 1);
                
            }, 400);
        }
    })
}

$(document).ready(function() {
    $('version').text(version);

    $('#btn-help').click(function() {
        doHideMenus();
        window.open('https://docs.querycommander.com', 'docs_page');
        return false;
    });

    $('#btn-about').click(function() {
        doHideMenus();
        window.open('https://docs.querycommander.com/en/latest/about/', 'docs_page');
        return false;
    });

    $('#btn-logout').click(function() { doHideMenus(); doLogout(); return false; });
    $('#form-login').submit(function() { doHideMenus(); doLogin(); return false; });
    $('#btn-login').click(function() { doHideMenus(); $('#form-login').submit(); return false; });
    $('#btn-refresh-connections').click(function() { doHideMenus(); doRefreshConnections(); return false; });
    $('#btn-execute').click(function() {
        doHideMenus();
        $('core').children('tab').each(function(i, o) {
            if ($(o).hasClass('query')) {
                if ($(o).hasClass('active')) {
                    $(o).find('.btn-tab-execute').trigger('click');
                }
            }
        });

        return false;
    });

    $('#chooser-select-connection .btn-chooser-close').click(function() { doHideMenus(); $('#chooser-select-connection').fadeOut('fast'); return false; });
    $('#chooser-select-connection .btn-chooser-select').click(function() { 
        doHideMenus();
        connection_selected = $('input[name="connection"]:checked').val(); 
        if ($('#chooser-select-connection').attr('tabupdate') == "yes") {
            
            if ($("#btn-connection").find('span').text() != connection_selected) {
                $("#btn-connection").find('span').text(connection_selected);
                $("#btn-database").find('span').eq(0).text('<not set>');
                $("#btn-database").find('span').eq(2).text('<not set>');
                $('tablist a.active').attr('connection', connection_selected);
                $('tablist a.active').attr('database', '');
                $('tablist a.active').attr('schema', '');
                doRefreshDBOptions();
                
                let tab_name = $('tablist a.active').find('span').text();
                if (tab_name == connection_selected) {
                    $('tablist a.active').find('span').text(connection_selected);
                }
            }
        } else {
            addQueryTab(false, connection_selected, "<not set>", connection_selected, "<not set>");
        }
        $('#chooser-select-connection').fadeOut('fast');
        return false; 
    });
    
    $('#btn-new-tab-menu').click(function() {
        doHideMenus();
        if ((connection_list.length == 1) && (connection_selected == connection_list[0]["name"])) {
            addQueryTab(false, connection_selected, "<not set>", connection_selected, "<not set>");
        } else {
            doShowConnectionDialog();
        }
        return false;
    });

    $('#btn-outdent').click(function() {
        doHideMenus();
        if ($('tab.active').hasClass('query')) {
            if (editor_type == "codemirror") {
                let editor = editors[$('tab.active').prop('id')];
                if (editor.somethingSelected()) {
                    editor.indentSelection("subtract"); // Un-indents all selected lines
                } else {
                    var cursor = editor.getCursor();
                    var lineContent = editor.getLine(cursor.line);
                    var indentUnit = editor.getOption("indentUnit");
                    var leadingSpaces = lineContent.match(/^\s*/)[0].length;
            
                    // Determine how much to un-indent based on the current indentation level
                    var newIndentLevel = Math.max(leadingSpaces - indentUnit, 0);
                    editor.replaceRange(" ".repeat(newIndentLevel), { line: cursor.line, ch: 0 }, { line: cursor.line, ch: leadingSpaces });
                }
            } else {
                $('tab.active textarea.editor').focus();
                doManageTab($('tab.active textarea.editor'), true);
            }
        }
        return false;
    });

    $('#btn-indent').click(function() {
        doHideMenus();
        if ($('tab.active').hasClass('query')) {
            if (editor_type == "codemirror") {
                let editor = editors[$('tab.active').prop('id')];
                if (editor.somethingSelected()) {
                    editor.indentSelection("add"); // Indents all selected lines
                } else {
                    var spaces = Array(editor.getOption("indentUnit") + 1).join(" ");
                    editor.replaceSelection(spaces);
                }
            } else {
                $('tab.active textarea.editor').focus();
                doManageTab($('tab.active textarea.editor'), false);
            }
        }
        return false;
    });

    $('#btn-save-profile').click(function() {
        doHideMenus();
        if (!$(this).prop('disabled')) {
            doSaveProfile();
        }
        return false;
    });

    $('#btn-connection').click(function() {
        doHideMenus();
        connection_selected = $(this).find('span').text();

        doShowConnectionDialog(true);
        return false;
    });

    $('#btn-database').click(function() {
        if ($('.database-select').css('display') == 'flex') {
            doHideMenus();
            return;            
        }

        doHideMenus();

        let pos = $('#btn-database').offset();
        $('.database-select').css('left', pos.left);

        $('.database-select').find('div').eq(1).show();
        let c_offset = $('#btn-database').width() / 2;
        let tab_id = $('tab.active').prop('id');
        
        $('tablist').find('a').each(function(i,o) {
            if ($(o).attr('data-target') == '#'+tab_id) {
                if ($(o).attr('db-only') == "1") {
                    $('.database-select').find('div').eq(1).hide();
                    $('.database-select').css('left', pos.left - Math.abs((176/2) - c_offset));
                } else {
                    $('.database-select').css('left', pos.left - Math.abs(172 - c_offset)); // 176+168 / 2
                }
            }
        });

        $('.database-select').find('div').eq(0).html('<span class="loading"><i class="fas fa-spinner fa-spin"></i> Loading...</span>');
        $('.database-select').find('div').eq(1).html('<span class="loading"><i class="fas fa-spinner fa-spin"></i> Loading...</span>');

        doLoadDBList();

        $('.database-select').css('display', 'flex');

        return false;
    });

    doEnableSlider('page > sidebar', 'page > slider', 'horizontal');

    $(document).mouseup(function() { is_mouse_down=false; updateStatusBar(); });
    $(document).click(function() { doCloseContextMenu(); doHideMenus(); });

    $(document).keydown(function (e) {
        if (e.which === 27) {
            // Esc
            $('.sidebar-context-menu').hide();
            $('overlay.chooser#chooser-select-connection').hide();
            $('overlay.chooser#ddl-data').hide();
        }
    });


    $(document).keydown(function (e) {
        if (["TEXTAREA","INPUT"].includes($(document).find(':focus').prop('tagName'))) {
            return true;
        } else {
            if (e.ctrlKey || e.metaKey) {
                if (e.keyCode == 65) {
                    // A
                    if ($('tab.active .btn-tab-results').hasClass('active')) {
                        $('tab.active results table').find('td').addClass('selected');
                        e.preventDefault();
                        return false;
                    } else {
                        e.preventDefault();

                        if ($('.chooser#ddl-data').is(':visible')) { 
                            highlightContents('#ddl-data .message'); 
                            return false;
                        }
                        
                        if ($('tab.active').hasClass('properties')) {
                            if ($('tab.active .section.code').is(':visible')) {
                                highlightContents('tab.active .section.code > div');
                                return false;
                            }
                        }

                        if ($('tab.active .btn-tab-output').hasClass('active')) {
                            highlightContents('tab.active .section.output > div');
                            return false;
                        }

                        if ($('tab.active .btn-tab-code').hasClass('active')) {
                            highlightContents('tab.active .section.statement > div');
                            return false;
                        }

                        return false;
                    }
                }

                if (e.keyCode == 67) {
                    // C
                    if (($('tab.active .btn-tab-results').hasClass('active')) && ($('tab.active results table').find('.selected').length > 0)) {
                        $('tab.active .btn-tab-copy').trigger('click');
                        e.preventDefault();
                        return false;
                    }
                }

                if (e.keyCode == 83) {
                    // S
                    e.preventDefault();
                    $('#btn-save-profile').trigger('click');
                    return false;
                }
            }
        }
    });

    $('#btn-tab-selector').click(function() {
        if ($('.tab-list-items').hasClass('active')) {
            doHideMenus();
            return false;
        }

        doHideMenus();

        if ($('tablist').children().length <= 2) { return false; }

        $('.tab-list-items > ul').empty();
        $('.tab-list-items').addClass('active');

        for(let i=1;i < $('tablist').children().length - 1; i++) {
            let o = $('<li><a href="#"></a></li>');
            o.find('a').text($('tablist').children().eq(i).find('span').text());
            o.find('a').attr('data-index', i);
            o.appendTo($('.tab-list-items > ul'));
            o.find('a').click(function() {
                let t = $('tablist').children().eq($(this).attr('data-index'));
                $('tablist').children().eq(0).after(t);
                t.find('a').trigger('click');
                doHideMenus();
                return false;
            });
        }

        return false;
    });

    $('#tab-filter-options').find('.btn-chooser-close').click(function() { $('#tab-filter-options').hide(); return false; });
    $('#tab-filter-options').find('.btn-chooser-apply').click(function() { 
        let headers = $('tab.active').find('.section.data').find('thead > tr');

        headers.children().removeClass('selected');
        let sel_idx = -1;
        let sel_value = $('#sel-value').val();
        let sel_compare = $('#sel-compare').find('option:selected').val();
        let sel_column = $('#sel-column').find('option:selected').val();
    
        for (let i = 1; i < headers.children().length; i++) {
            let o = headers.children().eq(i);
            if (sel_column == o.find('span').text()) {
                o.addClass('selected');
                sel_idx = i;
            }
        }
    
        headers.attr('filter-type', sel_compare);
        headers.attr('filter-text', sel_value);

        doApplyFilterOptions();
        return false; 
    });

    $('#tab-filter-options').find('.btn-chooser-clear').click(function() {
        let headers = $('tab.active').find('.section.data').find('thead > tr');
        headers.children().removeClass('selected');

        headers.attr('filter-type', '');
        headers.attr('filter-text', '');

        doApplyFilterOptions();
        return false;
    });

    $('.simple-notice a').click(function() { return false; });

    doCheckSession(true);

});