TOR2WEB_NODE_LIST = ['tor2web.fi',
    'tor2web.org',
    'onion.to',
    'tor2web.blutmagie.de',
    'onion.lt',
    'onion.lu',
    'onion.cab']

function ping(ip, callback) {

    if (!this.inUse) {
        this.status = ' - unchecked';
        this.inUse = true;
        this.callback = callback;
        this.ip = ip;
        var _that = this;
        this.img = new Image();
        this.img.onload = function () {
            _that.inUse = false;
            _that.callback(' - responded');

        };
        this.img.onerror = function (e) {
            if (_that.inUse) {
                _that.inUse = false;
                _that.callback(' - responded', e);
            }

        };
        this.start = new Date().getTime();
        this.img.src = "https://abc." + ip + "/antanistaticmap/tor2web-small.png";
        this.timer = setTimeout(function () {
            if (_that.inUse) {
                _that.inUse = false;
                _that.callback(' - timeout');
            }
        }, 5000);
    }
}

function pingAllNodes(){
 var PingModel = function (servers) {
    var self = this;
    var myServers = [];
    ko.utils.arrayForEach(servers, function (location) {
        myServers.push({
            name: location,
            status: ko.observable(' - unchecked')
        });
    });
    self.servers = ko.observableArray(myServers);
    ko.utils.arrayForEach(self.servers(), function (s) {
        s.status(' - checking');
        new ping(s.name, function (status, e) {
            s.status(status);
        });
    });
 };
 var komodel = new PingModel(TOR2WEB_NODE_LIST);
 ko.applyBindings(komodel);
}

function loadFilter(node){
  var url = "/static/log/" + node + "_md5filterlist.txt";
  var total = 0;
  var ol_list_element = $("#"+node.replace(".", ""));
  var h3 = ol_list_element.prev();
  $.get( url, function( data ) {
    if(data){
      var lines = data.split("\n");
      $.each(lines, function(n, line) {
	var content = '<li style="list-style-type: none; text-align: right;">' + line + '</li>';
	ol_list_element.append(content);
	++total;
      });
      h3.text( h3.text() + " - " + total );
    }
  });
}

$( document ).ready(function() {
  
  pingAllNodes();

  $.each(TOR2WEB_NODE_LIST, function( index, node ) {
    loadFilter(node);
  });
  
 $( "h3" ).click(function() {
   $(this).next().toggle();
 });

});