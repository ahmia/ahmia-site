(function($, window) {

  var Ahmia = {};
  $.extend(Ahmia, {

    isLikelyTBB: function() {
      // from check.torproject.org utils.go
      var valid_regexes = [
        "^Mozilla/5\.0 \(Windows NT 6\.1; rv:[\d]+\.0\) Gecko/20100101 Firefox/[\d]+\.0$" ];
      for (var i=0; i<valid_regexes.length; i++) {
        var re = new RegExp(valid_regexes[i]);
        var result = re.test(Ahmia.userAgent());
        if (result === true) return true;
      }
      return false;
    },

    userAgent: function() {
      return (window.navigator && navigator.userAgent) ? navigator.userAgent : 'none';
    }
  });

  window.Ahmia = Ahmia;

})(window.jQuery, window);
