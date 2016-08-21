(function($) {

  var formContainer = null;
  var flashMessageContainer = null;

  var flashMessages = {
    info: 'p.info',
    warn: 'p.warn',
    error: 'p.error',
    all: 'p.info, p.warn, p.error'
  };

  var hideMessages = function() {
    var selector = $(flashMessages.all, flashMessageContainer);
    selector.text('');
    selector.hide();
  };

  var showMessage = function(type, msg) {
    hideMessages();
    var selector = $(flashMessages[type], flashMessageContainer);
    selector.text(msg);
    selector.show();
  };

  var normalizeInput = function(onion) {
    onion = onion.replace('.onion', '');
    onion = onion.replace('http:', '');
    onion = onion.replace('https:', '');
    onion = onion.replace('//', '');
    onion = onion.replace('/', '');
    return onion.trim();
  };

  var showError = function() {
    showMessage('error', 'There was an error adding your onion.');
  };

  var showSuccess = function() {
    showMessage('info', 'Your onion has been added.');
  };

  var addService = function(evt) {
    hideMessages();
    evt.preventDefault();
    var onion = normalizeInput($('#addOnion input[name=onion]').val());
    $.post(
      $('#addOnion').attr('action'),
      { onion: onion })
     .done(function() { hideMessages(); showSuccess(); })
     .fail(function() { hideMessages(); showError(); });
  };

  $(document).ready(function() {
    flashMessageContainer = $('#flashMessage');
    //$('#addOnion').on('submit', addService);
    // don't hide if the server has a message
    if (!flashMessageContainer.hasClass('server')) {
      hideMessages();
    }
  });

})(window.jQuery);
