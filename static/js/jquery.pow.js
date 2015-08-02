(function($) {
  $.fn.proofOfWork = function(opts) {

    var debug = function() {};
    var options = {};
    var defaultOptions = {
      debug: false,
      fieldNames: {
        workFactor: 'pow_work_factor',
        workType:   'pow_work_type',
        workPrefix: 'pow_work_prefix',
        workItem:   'pow_work_item',
        collisionValue: 'pow_collision_value',
        spentTokens: 'pow_spent_tokens'
      }
    };

    var getSHA = function(bitLevel, text) {
      if (window.jsSHA) {
        var h = new jsSHA('SHA-'+bitLevel, 'TEXT');
        h.update(text);
        return h.getHash('HEX');
      }
    };

    var getFormValues = function() {
      if (options.$target) {
        var workFactorInput =
          $('input[name="'+options.fieldNames.workFactor+'"]', options.$target).val();
        var workTypeInput   =
          $('input[name="'+options.fieldNames.workType+'"]', options.$target).val();
        var workPrefix      =
          $('input[name="'+options.fieldNames.workPrefix+'"]', options.$target).val();
        var collisionValue  =
          $('input[name="'+options.fieldNames.collisionValue+'"]', options.$target).val();
        var spentTokens     =
          $('input[name="'+options.fieldNames.spentTokens+'"]', options.$target).val();
        if (workFactorInput) options.workFactor = parseInt(workFactorInput);
        if (workTypeInput)   options.workType   = parseInt(workTypeInput);
        if (workPrefix)      options.workPrefix = workPrefix;
        if (collisionValue)  options.collisionValue = collisionValue;
        if (spentTokens)     options.spentTokens = spentTokens.split(',');
      }
    };

    var meetsWorkFactor = function(hash) {
      for (var i=0; i<options.workFactor; i++) {
        if (hash[i] !== options.collisionValue) return false;
      }
      return true;
    };

    var isUnspent = function(hash) {
      for (var i=0; i<options.spentTokens.length; i++) {
        if (hash === options.spentTokens[i]) return false;
      }
      return true;
    };

    var getProofOfWork = function() {
      var i = 0;
      var currentHash;
      while (true) {
        currentHash = getSHA(options.workType, options.workPrefix + i);
        if (meetsWorkFactor(currentHash) && isUnspent(currentHash)) {
          return [currentHash, i];
        }
        i++;
      }
    };

    var evtOnSubmit = function(e) {
      e.preventDefault();
      var workValue = getProofOfWork();
      if (workValue[1]) {
        debug('Found proof of work!', workValue);
        $('input[name="' + options.fieldNames.workItem + '"]', options.$target)
          .val(workValue[0]);
      }
      e.off('submit.proofOfWork');
      // submit now that we have the POW
      options.$target.submit();
    };

    options = $.extend({}, defaultOptions, opts);
    debug = (options.debug === true) ? console.log.bind(console) : function() {};
    if (!($(this).length && $(this).get(0).tagName === 'FORM')) {
      debug('ProofOfWork expects to be called only on form elements.');
      return;
    }
    options.$target = $(this);
    getFormValues();
    options.$target.on('submit.proofOfWork', evtOnSubmit);

    debug('jquery.pow initialized');
    debug(options);
  };
})(window.jQuery);
