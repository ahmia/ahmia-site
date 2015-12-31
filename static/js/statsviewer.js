var tor2web_list = []
var clicks_list = []
var backlinks_list = []

// downloads JSON stats from the JSON API
function getStats(order_by, list){
  var limit = 100;
  var url = "/stats/popularity?limit=" + limit + "&order_by="+order_by
  $.getJSON( url, function( json ) {
    var ol_list_element = $("#"+order_by);
    $.each(json, function (index, result) {
      item = {y: result.fields[order_by], label: result.fields.about+".onion"}
      list.push(item);
      // show the first 10
      if(index < 10){
	var content = '<li style="list-style-type: none; text-align: right;">' + item.y;
	content = content + ' <a href="http://' + item.label + '/">' + item.label + '</a></li>';
	ol_list_element.append(content);
      }
    });
    // wait until every list is ready
    if(tor2web_list.length == limit && 
      clicks_list.length == limit && 
      backlinks_list.length == limit){
      //show the results
      viewer();
    }
  });
}

function viewer(){
  // calculate the intersection between these three lists
  var new_tor2web_list = [];
  var new_backlinks_list = [];
  var new_clicks_list = [];
  var intersection_size = 0;
  $.each(tor2web_list, function(t_index, tor2web) {
    if(intersection_size == 30){
      return false;
    }
    $.each(backlinks_list, function(b_index, backlinks) {
      if(backlinks.label == tor2web.label){
	$.each(clicks_list, function(c_index, clicks) {
	  if(clicks.label == tor2web.label){
	    var place = backlinks_list.length;
	    for(var i = 0; i<new_tor2web_list.length; ++i){
	      var sum1 = new_tor2web_list[i].y + new_backlinks_list[i].y + new_clicks_list[i].y;
	      var sum2 = tor2web.y + backlinks.y + clicks.y;
	      if(sum1 > sum2){
		place = i;
		break;
	      }
	    }
	    new_tor2web_list.splice(place, 0, tor2web);
	    new_backlinks_list.splice(place, 0, backlinks);
	    new_clicks_list.splice(place, 0, clicks);
	    ++intersection_size;
	  }
	});
      }
    });
  });
  tor2web_list = new_tor2web_list;
  backlinks_list = new_backlinks_list;
  clicks_list = new_clicks_list;
  show_bars(); 
}

// download the JSON stats
getStats("tor2web", tor2web_list);
getStats("clicks", clicks_list);
getStats("public_backlinks", backlinks_list);

// viewer function
function show_bars(){
  var chart = new CanvasJS.Chart("chartContainer", {
    title:{
      text:"Intersection of the different popularity sources"
    },
    axisX:{
      interval: 1,
      labelFontSize: 10,
      lineThickness: 0
    },
    axisY2:{
      valueFormatString: "0",
      lineThickness: 0	
    },
    toolTip: {
      shared: true
    },
    legend:{
      verticalAlign: "top",
      horizontalAlign: "center"
    },
    data: [
    {     
      type: "stackedBar",
      showInLegend: true,
      name: "Tor2web average visits",
      axisYType: "secondary",
      color: "#7E8F74",
      dataPoints: tor2web_list
    },
    {     
      type: "stackedBar",
      showInLegend: true,
      name: "Public WWW backlinks",
      axisYType: "secondary",
      color: "#FF9900",
      dataPoints: backlinks_list
    },
    {
      type: "stackedBar",
      showInLegend: true,
      name: "Total search results clicks",
      axisYType: "secondary",
      color: "#6699FF",
      dataPoints: clicks_list
    }
    ]
  });
  chart.render();
}