TOR2WEB_NODE_LIST = ['tor2web.fi',
    'tor2web.org',
    'onion.to',
    'tor2web.blutmagie.de',
    'onion.lt',
    'onion.lu',
    'onion.cab']
    
FILTERS = {}

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
        }, 10000);
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
  var node_name = node.replace(".", "");
  var ol_list_element = $("#"+node_name);
  var h3 = ol_list_element.prev();
  $.get( url, function( data ) {
    if(data){
      var lines = data.split("\n");
      lines.sort();
      $.each(lines, function(n, line) {
	var content = '<li style="list-style-type: none; text-align: right;">' + line + '</li>';
	ol_list_element.append(content);
	++total;
      });
      h3.text( h3.text() + " - " + total );
      var content = '<label class="nostyle" for="' + node_name + '">' + node + '</label>';
      content = content + '<input type="checkbox" name="node" value="' + node_name + '" id="' + node_name + '">';
      $("#setform").append(content);
      FILTERS[node_name] = lines;
    }
  });
}

function generateList() {
  var setOption = $("form input:radio:checked").val();
  var filtering = [];
  var ul_element = $("#generatedlist");
  ul_element.empty();
  var init = true;
  $( "form input:checkbox:checked" ).each(function() {
      var node_name = $(this).val();
      var md5list = FILTERS[node_name];
      if(init){
	init = false;
	filtering = md5list;
      }
      else if( setOption == "sum" ){
	filtering.push.apply(filtering, md5list);
      }
      else if( setOption == "intersection" ){
	  filtering = intersection(md5list, filtering);
      }
      else if( setOption == "difference" ){
	filtering = diff(md5list, filtering);
      }
  });
  
  var finallist = [];
  
  // Remove Duplicates from the array 
  $.each(filtering, function(i, el){
    if($.inArray(el, finallist) === -1) finallist.push(el);
  });
  
  // Show the results
  $.each(finallist, function(n, line) {
    var content = "<li>" + line + "</li>";
    ul_element.append(content);
  });
}


// Finds the intersection of two arrays
function intersection(a, b) {
    var t;
    if (b.length > a.length) t = b, b = a, a = t; // indexOf to loop over shorter
    return a.filter(function (e) {
        if (b.indexOf(e) !== -1) return true;
    });
}


function diff(array1, array2)
{
  var difference = [];
  jQuery.grep(array2, function(el) {
        if (jQuery.inArray(el, array1) == -1) difference.push(el);
  });
  return difference;
}


$(document).ready(function() {
  
  pingAllNodes();

  $.each(TOR2WEB_NODE_LIST, function(index, node) {
    loadFilter(node);
  });
  
  $("h3").click(function() {
    $(this).next().toggle();
  });

  $("#setform").change(function() {
    generateList();
  });
  
});