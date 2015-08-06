(function($) {
  $(document).ready(function() {
    $('ol.searchResults li').each(function() {
      $(this).find('a.reportAbuse').on('click', evtReportAbuse);
    });
    /* $(this).find(':not(a)').on('click', $.proxy(
        function(e) {
          // todo scope into navigationKeyCapture
          // or otherwise catch tor browser/usage
          if ($(this).attr('href')) {
            var setLink = $(this).attr('href');
            window.location = setLink;
          } else {
            // fall back to h4 a:link if some issue
            var headingLink = $(this).find('h4 a').attr('href');
            window.location = headingLink;
          }
        }, this));
    });
    navigationKeyCapture.listItems = $('ol.searchResults li');
    if (navigationKeyCapture.listItems.length) {
      navigationKeyCapture.maxIndex = navigationKeyCapture.listItems.length - 1;
      for (var i=0; i < navigationKeyCapture.listItems.length; i++) {
        var item = $(navigationKeyCapture.listItems[i]);
        if (item.hasClass('selectedItem')) {
          navigationKeyCapture.selectedItem = i;
          $(navigationKeyCapture.listItems[navigationKeyCapture.selectedItem]).focus();
        }
        break;
      }
    }
    $('#id_q').focus(function() {
      navigationKeyCapture.stopTracking();
    });
    $('#id_q').blur(function() {
      navigationKeyCapture.startTracking();
    });
    navigationKeyCapture.startTracking();
    */
  });

  // abuse reporting endpoint
  var evtReportAbuse = function(evt) {
    evt.preventDefault();
    var abusiveOnion = $(this).attr('data-href');
    var currentLink  = $(this);
    var successMsg   = $(this).siblings('.abuseReportReceived');
    var errorMsg     = $(this).siblings('.abuseReportError');
    successMsg.hide().removeClass('hidden');
    errorMsg.hide().removeClass('hidden');
    $.post('/blacklist/report', { onion: abusiveOnion })
     .done(function() { currentLink.hide(); successMsg.show(); })
     .fail(function() { currentLink.hide(); errorMsg.show(); });
  };

  // shortcuts for keycodes
  var KEY = {
    ArrowUp:      38,
    ArrowDown:    40,
    ArrowLeft:    37,
    ArrowRight:   39,
    Enter:        13
  };


  /**
   * THIS IS NOT A KEYLOGGER.
   *
   * All this code does is capture your arrow keys and
   * enter to make it easier to select search results
   * with your keyboard. Nothing is ever transmitted to
   * the Ahmia servers.
   **/
  var navigationKeyCapture = {};
  $.extend(navigationKeyCapture, {

    listItems: [],
    selectedItem: 0,
    maxIndex: 0,

    event_trackKeyPressEvent: function(evt) {
      if (evt && evt.keyCode) {
        switch (evt.keyCode) {
          case KEY.ArrowUp:
            this.navigateUp();
            break;
          case KEY.ArrowDown:
            this.navigateDown();
            break;
          case KEY.ArrowLeft:
            this.navigateUp();
            break;
          case KEY.ArrowRight:
            this.navigateDown();
            break;
          case KEY.Enter:
            this.select();
            break;
        }
      }
    },

    navigateUp: function() {
      var next = this.selectedItem - 1;
      if (next >= 0) {
        $(this.listItems[this.selectedItem]).removeClass('selected');
        this.selectedItem = next;
        $(this.listItems[this.selectedItem]).addClass('selected');
      }
    },

    navigateDown: function() {
      var next = this.selectedItem + 1;
      if (next <= this.maxIndex) {
        $(this.listItems[this.selectedItem]).removeClass('selected');
        this.selectedItem = next;
        $(this.listItems[this.selectedItem]).addClass('selected');
      }
      this.setScrollPosition();
    },

    setScrollPosition: function() {
      var selected = $(this.listItems[this.selectedItem]);
      var offset_y = selected.height();
      if (typeof selected.scrollTo === 'function') {
        $.scrollTo(selected, undefined, { interrupt: true, offset: { top: offset_y }});
      }
    },

    select: function() {
      var selected  = $(this.listItems[this.selectedItem]);
      if (selected && selected.attr('data-href')) {
        // todo detect tor browser bundle, change URI depending
        // on if using tor browser bundle or prompt user for insecure
        // access
        window.location = selected.attr('data-href');
      }
    },

    startTracking: function() {
      $(this.listItems[this.selectedItem]).addClass('selected');
      $(document).bind('keyup.navigationKeyCapture',
        $.proxy(this.event_trackKeyPressEvent, this));
    },

    stopTracking: function() {
      $(document).unbind('keyup.navigationKeyCapture');
    }
  });

})(window.jQuery);
