function addNew(formsetPrefix, baseURL) {
  var totalForms = document.getElementById('id_' + formsetPrefix + 
      '-TOTAL_FORMS');
  var sUrl = baseURL + '?index=' + totalForms.value;
  totalForms.value = parseInt(totalForms.value) + 1;
  var callback = {
    success: function(o) {
      var newFieldsTable = document.createElement('table');
      newFieldsTable.innerHTML = o.responseText;
      var newFields = document.createElement('div');
      newFields.className = 'added';
      newFields.appendChild(newFieldsTable);
      var writeRoot = document.getElementById(o.argument[0] + '-writeroot');
      writeRoot.parentNode.insertBefore(newFields, writeRoot);
      newFields = writeRoot.previousSibling;
      //newFields.getElementsByTagName('select')[0].focus();
      
      /* We call autocomplete here to make sure that the new divs are marked with the right 
       * classes so autocomplete functions correctly.
       *
       * We call this twice - once for member divs and once for account divs. One of these calls
       * is unnecessary, and it might be ideal in the future to split this function into two separate functions someday:
       * addNewAccount and addNewMember
       */
      autocomplete('related_member-' + (totalForms.value - 1).toString() + '-member', '/membership/autocomplete/member_spiffy/', true);
      autocomplete('related_account-' + (totalForms.value - 1).toString() + '-account', '/membership/autocomplete/account_spiffy/', true);
    },
    failure: function(o) {},
    argument: [formsetPrefix],
  };
  YAHOO.util.Connect.asyncRequest('GET', sUrl, callback, null);
}

