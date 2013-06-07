
function yui_autocomplete(name, ac_url, force_selection) {
    YAHOO.util.Event.onDOMReady(function () {
        var datasource = new YAHOO.util.XHRDataSource(ac_url);
        datasource.responseType = YAHOO.util.XHRDataSource.TYPE_JSON;
        datasource.responseSchema = {
            resultsList: "result",
            fields: ["label", "id"]
        };

        datasource.doBeforeParseData = function (request, original, callback) {
            var parsed = {"result": []};
            for (var i in original)
                parsed.result.push({"id": original[i][0], "label": original[i][1]});
            return parsed;
        }
        datasource.resultTypeList = false;

        var input = document.getElementById("id_"+name);
        var container = document.createElement("div");
        YAHOO.util.Dom.addClass(container, "yui-skin-sam");
        YAHOO.util.Dom.insertAfter(container, input);
// Please don't put yui-skin-sam on the whole body.  It causes the autocomplete
// to eat the next HTML chunk.  (I don't know why.)   --Paul Dexter
//      if (!YAHOO.util.Dom.hasClass(document.body, "yui-skin-sam"))
//          YAHOO.util.Dom.addClass(document.body, "yui-skin-sam");

        var autocomplete = new YAHOO.widget.AutoComplete(input, container, datasource);
        autocomplete.resultTypeList = false;
        // I'm reducing queryDelay.  I hope this doesn't break things. -Paul
        // autocomplete.queryDelay = .5;
        autocomplete.queryDelay = .2;
        // Don't clear pre-filled value onblur.
        //autocomplete.forceSelection = force_selection;
        autocomplete.forceSelection = false;

        var selected_item = {label: null, id: null};
        var hidden = document.getElementById("id_hidden_"+name)
        autocomplete.itemSelectEvent.subscribe(function (type, args) {
            selected_item = args[2];
            hidden.value = selected_item.id;
        });
        var allforms = document.getElementsByTagName("form");
        for (var i = 0; i < allforms.length; i++) {
            var form = allforms[i];
            YAHOO.util.Event.addListener(form, "submit", function (event, form) {
                if (input.value == '')
                    hidden.value = '';
                if (selected_item.label != input.value && !force_selection)
                    hidden.value = input.value;
            });
        }
        /*  OLD CODE WAS....
        form = document.getElementsByTagName("form")[0];
        YAHOO.util.Event.addListener(form, "submit", function (event, form) {
            if (selected_item.label != input.value && !force_selection)
                hidden.value = input.value;
        });  */

        // Set up accounttangle for scheduling (pick member auto-picks acct):
        if (typeof(window['ACCOUNTTANGLE']) != 'undefined' && 
                ACCOUNTTANGLE && (name.indexOf('member') > 1)) {
            var formsetid = name.split('-')[0];
            var accountfield = document.getElementById('id_'+formsetid+'-account');
            var accounthidden = document.getElementById('id_hidden_'+formsetid+'-account');
            autocomplete.itemSelectEvent.subscribe(function (type, args) {
                label = args[2].label;
                account = label.substring(label.indexOf('(')+1, label.length-1);
                accountfield.value = account;
                // coerce value to string, so it's not confused with account.id
                // the Z will be stripped off in scheduling/forms
                accounthidden.value = 'Z' + account;
            });
        }

        // Set up get cashier info (picking account fetches info):
        if (typeof(window['GETCASHIERINFO']) != 'undefined' &&  
                GETCASHIERINFO ) { // && (name == 'account')) {
            autocomplete.itemSelectEvent.subscribe(function (type, args) {
                var account_id = args[2].id;
                getAccountInfo(account_id);
            });
        }

        // Set up get cashier info (picking account fetches info):
        if (typeof(window['GETMEMBERINFO']) != 'undefined' &&  
                GETMEMBERINFO ) { 
            autocomplete.itemSelectEvent.subscribe(function (type, args) {
                var member_id = args[2].id;
                getMemberInfo(member_id);
            });
        }

        // Set up jump (picking member submits form, ie for searching):
        if (typeof(window['SUBMITONSELECT']) != 'undefined' &&
                SUBMITONSELECT ) {
            autocomplete.itemSelectEvent.subscribe(function (type, args) {
                SUBMITONSELECTFORM.submit();
            });
        }

    });
}

autocomplete = yui_autocomplete;
