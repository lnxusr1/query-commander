import { site_path } from './path.js';
var version = "v0.0.1-alpha";
var timer;
var is_mouse_down = false;
var current_user = "";
var role_list = [];
var connection_list = [];
var connection_selected = "";
var tab_counter = 0;

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

    //console.log({ start: r_start, end: r_end, idx: ridx });

    for (let i = r_start; i <= r_end; i++) {
        table.find("tr").eq(i).find("td").addClass('selected');
    }
}

function updateStatusBar() {

    setTimeout(function() {
        if ($('tab.active.query textarea.editor').val() === undefined) { $('#cur_pos').text('0'); $('#sel_pos').text('0 : 0'); return; }

        /*
        if ($('box.active textarea.code').val().length > 0) {
            $('.btn-execute').prop('disabled', false);
        } else {
            $('.btn-execute').prop('disabled', true);
        }
        */

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
    }, 100);
}

function doGetSQL(tab_id) {
    let sql = '';
    if ($(tab_id + ' textarea.editor').is(":focus")) {
        sql = window.getSelection().toString();
    }

    if (('' + sql).trim() == '') {
        
        sql = $(tab_id + ' textarea.editor').first().val();
    }

    return sql;
}

function doExecuteSQL(tab_id, exec_type) {
    $(tab_id + ' textarea.editor').focus(); 
    let sql = doGetSQL(tab_id);
    let connection_name = $('tablist > item > a.active > span').text();

    if ((sql == '') || (connection_name == '')) { return; }

    if ($(tab_id + ' > item:last-child').css('height') == '0px') {
        $(tab_id + ' > item:first-child').css('height', '48%');
    }

    $(tab_id + ' .btn-tab-results').trigger('click');

    let req_data = {
        command: "query",
        type: exec_type,
        statement: sql,
        connection: connection_name
    }

    $.ajax({
        url: site_path,
        dataType: "json",
        method: "POST",
        crossDomain: true,
        headers: { 'Access-Control-Allow-Origin': '*' },
        data: JSON.stringify(req_data),
        contentType: "application/json",
        beforeSend: function(xhr) {
            $(tab_id + ' .tab-loading').show();
            $(tab_id + ' div.section.statement div').text(req_data["statement"]);
        },
        success: function(data) {
            doClearQueryResults($(tab_id + ' div.section.data'));

            if (!data.ok) {
                if (data.error) { alert(data.error); }
                if (data.logout) { doLogout(); }
                return;
            }

            if (data.data) {
                doLoadQueryData($(tab_id + ' div.section.data'), data.data, true, true);
            }
        },
        error: function(e) {
            doClearQueryResults($(tab_id + ' div.section.data'));
            $(tab_id + ' div.section.output div').text('An unexpected error occurred while executing the query.\nThis could be caused by a broken connection or malformed request.\n\nUnable to proceed.');
            $(tab_id + ' .btn-tab-output').trigger('click');
        },
        complete: function() {
            $(tab_id + ' .tab-loading').hide();
        }
    });
}

function doGetTableContents(container, selection=false, delimiter="\t") {

    let content = '';
    $(container).find('thead tr:first-child > th > data').each(function(i, o) {
        if (i > 0) {
            if (i > 1) {
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

    $(container).find('tbody tr').each(function(ir, tr) {
        if (content != "") { content = content + "\r\n"; }
        $(tr).find('td').each(function(i, o) {
            if (i > 0) {
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
        });
    });

    return content;
}

function doClearQueryResults(container) {

    //$(container).parent().find('div.section.statement div').text('');
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

function doLoadQueryData(container, data, with_types=true, with_numbers=true) {

    if ((data["error"]) && (data["error"] != "")) {
        doClearQueryResults(container);
        $(container).parent().find('div.section.output div').first().text(data["error"]);
        $(container).parent().parent().find('.btn-tab-output').first().trigger('click');
        return;
    }

    if (data["output"]) {
        $(container).parent().find('div.section.output div').first().text(data["output"]);
    }

    if (data["headers"]) {
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

        if (data["records"]) {
            for (let r=0; r<data["records"].length; r++) {
                let tr = $('<tr></tr>');
                if (with_numbers) {
                    tr.append($('<th><data></data></th>'));
                    tr.find('data').text(r+1);
                }
                for (let c=0; c<data["records"][r].length; c++) {
                    let el = $('<td><data></data></td>');
                    el.find('data').text(data["records"][r][c]);
                    el.find('data').addClass(data["headers"][c]["type"]);
                    tr.append(el);
                }
                container.find('tbody').append(tr);
            }

            if (data["records"].length == 0) {
                $(container).parent().parent().find('.btn-tab-output').first().trigger('click');
            } else {
                $(container).parent().parent().find('.btn-tab-export').prop('disabled', false);
                $(container).parent().parent().find('.btn-tab-copy').prop('disabled', false);
            }
        }
    }

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
            //$('box.active output controls button.copy').prop('disabled', false);
            //if ($(this).parent().parent().index() == 0) { console.log('parent'); return; }
            table.find('.selected').removeClass('selected');
            selectRow(table, $(this), ri_start);
        })
        .bind("selectstart", function() {
            return false;
        });
    }
}

function doWireUpQueryTab(tab_id) {

    $(tab_id + ' textarea.editor').keyup(function() { updateStatusBar(); });
    $(tab_id + ' textarea.editor').mouseup(function() { updateStatusBar(); });

    $(tab_id + ' .tab-loading').hide();
    $(tab_id + ' item:first-child').css('height', '100%');
    doEnableSlider(tab_id + ' item:first-child', tab_id + ' slider', 'vertical');

    $(tab_id + ' .btn-tab-execute').click(function(event) { doExecuteSQL(tab_id, 'sql'); return false; });
    $(tab_id + ' .btn-tab-explain').click(function(event) { doExecuteSQL(tab_id, 'explain'); return false; });

    $(tab_id + ' .btn-tab-settings').click(function() { });
    
    $(tab_id + ' .btn-tab-results').click(function() {
        $(tab_id + ' results > div.section').hide();
        $(tab_id + ' .data').show();
        $(tab_id + ' navmenu .active').removeClass('active');
        $(this).addClass('active');
        return false;
    });

    $(tab_id + ' .btn-tab-code').click(function() { 
        $(tab_id + ' results > div.section').hide();
        $(tab_id + ' .statement').show();
        $(tab_id + ' navmenu .active').removeClass('active');
        $(this).addClass('active');
        return false;
    });

    $(tab_id + ' .btn-tab-output').click(function() { 
        $(tab_id + ' results > div.section').hide();
        $(tab_id + ' .output').show();
        $(tab_id + ' navmenu .active').removeClass('active');
        $(this).addClass('active');
        return false;
    });

    $(tab_id + ' .btn-tab-export').click(function() { 
        
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
        let selected_only = false;
        if ($(tab_id + ' div.section.data table').find('.selected').length > 0) {
            selected_only = true;
        }

        let content = doGetTableContents($(tab_id + ' div.section.data'), selected_only);
        console.log(content);

        return false;
    });

    $(tab_id + ' .btn-tab-filter').click(function() { });
    $(tab_id + ' .btn-tab-first').click(function() { });
    $(tab_id + ' .btn-tab-prev').click(function() { });
    $(tab_id + ' .btn-tab-next').click(function() { });
    $(tab_id + ' .btn-tab-last').click(function() { });
    $(tab_id + ' .btn-tab-refresh').click(function() { });

    $(tab_id + ' > item > results .data > div').scroll(function() {
        $(tab_id + ' > item > results .data > div > div:first-child table').css('top', '' + $(this).scrollTop() + 'px');
        $(tab_id + ' > item > results .data > div > div table tr > th:first-child').css('left', ($(this).scrollLeft()) + 'px');
    });

    doClearQueryResults($(tab_id + ' .data'));
    //doLoadQueryData($(tab_id + ' results .data'), { "headers": [], "records": [] });
}

function addQueryTab(check_exists=false) {

    if (check_exists) {
        if ($('core > tablist').children().length > 2) { return; }
    }

    let tab_id = 'tab'+tab_counter;
    tab_counter++;

    let tab_button = $('<item><a class="active" href="#"><span></span><button title="Close"><i class="fas fa-times"></i></button></a></item>');
    let tab = $('<tab class="query"></tab>');
    tab.html($('templates > tab_query').html())
    tab.prop('id', tab_id);
    
    tab_button.find('span').text(connection_selected);
    tab_button.find('a').attr('data-target', '#'+tab_id);
    tab_button.find('button').click(function() {
        let t_id = $(this).parent().attr('data-target');
        $(this).parent().parent().remove();
        $(t_id).remove();
        $('core > tablist').find('a').first().trigger('click');
        return false;
    });

    tab_button.find('a').click(function() {
        let t_id = $(this).attr('data-target');
        $('core > tab').removeClass('active');
        $(t_id).addClass('active');
        $('core > tablist > item > a').removeClass('active');
        $(this).addClass('active');
        $(t_id).find('textarea').focus();
        return false;
    });

    $('core > tablist > item > a').removeClass('active');
    $('core > tab').removeClass('active');

    $('core > tablist > item:first-child').after(tab_button);
    $('core').append(tab);
    tab.addClass('active');

    doWireUpQueryTab('#' + tab_id);

    $('#' + tab_id + ' textarea.editor').focus();
}

function doAddDetailTab(obj_details) {
    
    let data_encoded = JSON.stringify(obj_details);
    obj_details["command"] = "details";

    $.ajax({
        url: site_path,
        dataType: "json",
        method: "POST",
        crossDomain: true,
        headers: { 'Access-Control-Allow-Origin': '*' },
        data: JSON.stringify(obj_details),
        contentType: "application/json",
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
                let t_id = $(this).parent().attr('data-target');
                $(this).parent().parent().remove();
                $(t_id).remove();
                $('core > tablist').find('a').first().trigger('click');
                return false;
            });

            tab_button.find('a').click(function() {
                let t_id = $(this).attr('data-target');
                $('core > tab').removeClass('active');
                $(t_id).addClass('active');
                $('core > tablist > item > a').removeClass('active');
                $(this).addClass('active');
                $(t_id).find('textarea').focus();
                return false;
            });

            $('core > tablist > item > a').removeClass('active');
            $('core > tab').removeClass('active');

            $('core > tablist > item:first-child').after(tab_button);
            $('core').append(tab);
            tab.addClass('active');

            obj_details["breadcrumbs"].reverse();
            tab.find('breadcrumbs').text(obj_details["breadcrumbs"].join(' : '));

            //TODO: FIX THIS
            /*
            $(tab).find('.section.table').each(function(i, o) {
                doLoadQueryData($(this), {}, false);
            });
            */

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
        }
    });


}

function doGenerateDDL(obj_details) {
    
    let data_encoded = JSON.stringify(obj_details);
    obj_details["command"] = "ddl";
    
    $.ajax({
        url: site_path,
        dataType: "json",
        method: "POST",
        crossDomain: true,
        headers: { 'Access-Control-Allow-Origin': '*' },
        data: JSON.stringify(obj_details),
        contentType: "application/json",
        success: function(data) {
            if (!data.ok) {
                if (data.error) { alert(data.error); }
                if (data.logout) { doLogout(); }
                return;
            }

            $('overlay.chooser#ddl-data .message-box .message').attr('obj-details', data_encoded);
            $('overlay.chooser#ddl-data .message-box .message').text(data.ddl);

            $('overlay.chooser#ddl-data .btn-chooser-close').off();
            $('overlay.chooser#ddl-data .btn-chooser-close').click(function() { $('overlay.chooser#ddl-data').hide(); return false; });

            $('overlay.chooser#ddl-data .btn-chooser-refresh').off();
            $('overlay.chooser#ddl-data .btn-chooser-refresh').click(function() { 
                let data_decoded = JSON.parse($('overlay.chooser#ddl-data .message-box .message').first().attr('obj-details'));
                doGenerateDDL(data_decoded); 
                return false; 
            });

            $('overlay.chooser#ddl-data .btn-chooser-copy').off();
            $('overlay.chooser#ddl-data .btn-chooser-copy').click(function() {
                navigator.clipboard
                    .writeText($('overlay.chooser#ddl-data .message-box .message').text())
                    .then(() => {})
                    .catch(() => { alert("Copy to Clipboard failed."); });

                return false;
            });
            $('overlay.chooser#ddl-data').show();
        }
    });
}

function doLoadContextMenu(obj, event, menu_items) {
    doCloseContextMenu();
    $(obj).addClass('highlight');
    $('.sidebar-context-menu a').off();

    $('.sidebar-context-menu > ul > li').hide();
    for (let z=0; z < menu_items.length; z++) {
        if (menu_items[z] == "refresh") { $('#btn-context-refresh-item').parent().show(); }
        if (menu_items[z] == "copy") { $('#btn-context-copy-name').parent().show(); }
        if (menu_items[z] == "ddl") { $('#btn-context-generate-ddl').parent().show(); }
        if (menu_items[z] == "details") { $('#btn-context-view-details').parent().show(); }
    }

    $('#btn-context-refresh-item').click(function() {
        $(obj).removeClass("loaded");
        $(obj).removeClass("expanded");
        $(obj).removeClass("highlight");
        $(obj).parent().children('ul').remove();
        $(obj).trigger('click');
        $('.sidebar-context-menu').hide();
        return false;
    });

    $('#btn-context-copy-name').click(function() {
        $(obj).removeClass("highlight");

        navigator.clipboard
            .writeText($(obj).find('span').text())
            .then(() => {})
            .catch(() => { alert("Copy to Clipboard failed."); });

        $('.sidebar-context-menu').hide();
        return false;
    });

    $('#btn-context-generate-ddl').click(function() {
        let obj_path = {};
        let itm = $(obj).parent();
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

        let data = {
            command: "meta",
            target: $(obj).find('span').text(),
            type: $(obj).parent().attr('data-type'),
            path: obj_path
        }

        $.ajax({
            url: site_path,
            dataType: "json",
            method: "POST",
            crossDomain: true,
            headers: { 'Access-Control-Allow-Origin': '*' },
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
    
    connection_list.sort();
    for (let i = 0; i < connection_list.length; i++) {
        let el = $('<li data-type="connection"><a href="#"><i class="fa fa-server fa-fw"></i><span></span></a></li>');
        el.find('span').text(connection_list[i]);
        el.appendTo($('sidebar > metadata > ul'));
        el.find('a').on('contextmenu', function(event) { doLoadContextMenu($(this), event, ["refresh"]); return false; });        
        el.find('a').click(function() {
            doLoadMeta($(this));
            return false; 
        });
    }
}

function doLoadPage() {
    doRefreshConnections();
    
    if (connection_list.length == 1) { connection_selected = connection_list[0]; }
    if (connection_selected != "") { 
        if ($('core > tablist').children().length == 2) {
            addQueryTab(true);
        }
    }
}

function doShowConnectionDialog() {
    connection_list.sort();
    $('#chooser-select-connection .message').find('ul').empty();

    for (let i = 0; i < connection_list.length; i++) {
        let option = $('<li><input/><label></label></li>');
        option.find('input').prop('type','radio');
        option.find('input').prop('name','connection');
        option.find('input').val(connection_list[i]);
        option.find('input').prop('id','connection'+i);
        option.find('label').prop('for','connection'+i);
        option.find('label').text(connection_list[i]);

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

function doShowRoleDialog() {
    role_list.sort();
    $('#chooser-select-role .message').find('ul').empty();

    for (let i = 0; i < role_list.length; i++) {
        let option = $('<li><input/><label></label></li>');
        option.find('input').prop('type','radio');
        option.find('input').prop('name','role');
        option.find('input').val(role_list[i]);
        option.find('input').prop('id','role'+i);
        option.find('label').prop('for','role'+i);
        option.find('label').text(role_list[i]);

        option.appendTo($('#chooser-select-role .message').find('ul'));
    }

    if ($('#role_selected').text() == "<default>") {
        $('#chooser-select-role').find('ul').find('input').first().prop('checked', true);
    } else {
        $('#chooser-select-role').find('ul').find('input').each(function(i,o) {
            if ($(o).val() == $('#role_selected').text()) {
                $(o).prop('checked', true);
            }
        });
    }

    if ($('#role_selected').text() == "<default>") { 
        $('#chooser-select-role .btn-chooser-close').hide(); 
    } else { 
        $('#chooser-select-role .btn-chooser-close').show(); 
    }
    
    $('#chooser-select-role').fadeIn('fast');
}

function doSelectRole() {
    let role_chosen = $('input[name="role"]:checked').val();
    let data = {
        "command": "select-role",
        "role": role_chosen
    }
    
    $.ajax({
        url: site_path,
        dataType: "json",
        method: "POST",
        crossDomain: true,
        headers: { 'Access-Control-Allow-Origin': '*' },
        data: JSON.stringify(data),
        contentType: "application/json",
        beforeSend: function(xhr) {
            $('#chooser-select-role button').prop('disabled', true);
        },
        success: function(data) {
            if (data.ok) {
                $('#role_selected').text(role_chosen);
                connection_list = data.connections;
                doLoadPage();
                $('#chooser-select-role').fadeOut('fast');
                if (connection_list == 0) {
                    alert('No connections found!')
                } else {
                    connection_selected = connection_list[0];
                    if (connection_list.length > 1) {
                        doShowConnectionDialog();
                    } else {
                        addQueryTab(true);
                    }
                }
            } else {
                alert("Unable to change active role to selected value.");
                if (data.logout) { doLogout(); }
            }
        },
        complete: function(data) {
            $('#chooser-select-role button').prop('disabled', false);
        },
        error: function() {

        }
    });
}

function doLoginSuccess(data, hide_login) {
    if (current_user != data.username) {
        doClearPage();
        current_user = data.username;
    }

    role_list = data.roles;
    connection_list = data.connections;

    if (role_list.length == 0) {
        $('#login-error').text('Unable to determine available roles.');
        $('#login-error').show();
        $('#login').show();
        return false;
    }

    doStartTimer();
    if (data.role_selected != "") {
        $('#role_selected').text(data.role_selected);
        $('#chooser-select-role').hide();
        if (role_list.length == 1) { $('.btn-open-role-chooser').hide(); }

        if (connection_selected == "") {
            if (connection_list.length == 1) {
                connection_selected = connection_list[0];
                doLoadPage();
            } else {
                doRefreshConnections();
                doShowConnectionDialog();
            }
        }
    } else {
        $('#role_selected').text('<default>');
        doShowRoleDialog();
    }

    //doLoadPage();
    if (hide_login) {
        $('#login').hide();
    } else {
        $('#login').fadeOut('fast');
    }

}

function doLogin() { 

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
        url: site_path,
        dataType: "json",
        method: "POST",
        crossDomain: true,
        headers: { 'Access-Control-Allow-Origin': '*' },
        data: JSON.stringify(data),
        contentType: "application/json",
        beforeSend: function(xhr) {
            $('#username').prop('disabled', true);
            $('#password').prop('disabled', true);
            $('#btn-login').prop('disabled', true);
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
                return;
            }
        },
        complete: function() {
            $('#username').prop('disabled', false);
            $('#password').prop('disabled', false);
            $('#btn-login').prop('disabled', false);
        }
    });
}

function doLogout() { 
    doClearPage();
    doClearTimer();
    is_mouse_down=false;

    $.ajax({
        url: site_path,
        dataType: "json",
        method: "POST",
        crossDomain: true,
        headers: { 'Access-Control-Allow-Origin': '*' },
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
            $('#username').prop('disabled', false);
            $('#password').prop('disabled', false);
            $('#btn-login').prop('disabled', false);
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
        url: site_path,
        dataType: "json",
        method: "POST",
        crossDomain: true,
        headers: { 'Access-Control-Allow-Origin': '*' },
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
                    $('#page-loading').hide();
                    doLoginSuccess(data, true);
                } else {
                    doStartTimer();
                }
            }
        }
    });
}

$(document).ready(function() {
    $('version').text(version);

    $('#btn-logout').click(function() { doLogout(); return false; });
    $('#form-login').submit(function() { doLogin(); return false; });
    $('#btn-login').click(function() { $('#form-login').submit(); return false; });
    $('#btn-refresh-connections').click(function() { doRefreshConnections(); return false; });
    $('#btn-execute').click(function() {
        $('core').children('tab').each(function(i, o) {
            if ($(o).hasClass('query')) {
                if ($(o).hasClass('active')) {
                    $(o).find('.btn-tab-execute').trigger('click');
                }
            }
        });

        return false;
    });

    //TODO: FIX THESE vvv
    $('#chooser-select-role .btn-chooser-close').click(function() { $('#chooser-select-role').fadeOut('fast'); return false; });
    $('.btn-open-role-chooser').click(function() { doShowRoleDialog(); return false; });
    $('#chooser-select-role .btn-chooser-select').click(function() { doSelectRole(); return false; });
    
    $('#chooser-select-connection .btn-chooser-close').click(function() { $('#chooser-select-connection').fadeOut('fast'); return false; });
    $('#chooser-select-connection .btn-chooser-select').click(function() { 
        connection_selected = $('input[name="connection"]:checked').val(); 
        addQueryTab();
        $('#chooser-select-connection').fadeOut('fast');
        return false; 
    });
    //TODO: FIX ABOVE ^^^
    
    $('#btn-new-tab').click(function() {
        if ((connection_list.length == 1) && (connection_selected == connection_list[0])) {
            addQueryTab();
        } else {
            doShowConnectionDialog();
        }
        return false;
    });

    doEnableSlider('page > sidebar', 'page > slider', 'horizontal');

    doCheckSession(true);

    $(document).mouseup(function() { is_mouse_down=false; updateStatusBar(); });
    $(document).click(function() { doCloseContextMenu(); });
});