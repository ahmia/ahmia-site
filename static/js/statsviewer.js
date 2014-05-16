var tor2web_list = []
var clicks_list = []
var backlinks_list = []

// downloads JSON stats from the JSON API
function getStats(order_by, list){
  var limit = 30;
  var url = "/stats/popularity?limit=" + limit + "&order_by="+order_by
  $.getJSON( url, function( json ) {
    $.each(json, function (index, result) {
      item = {y: result.fields[order_by], label: result.fields.about}
      list.push(item);
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

// download the JSON stats
getStats("tor2web", tor2web_list);
getStats("clicks", clicks_list);
getStats("public_backlinks", backlinks_list);

// viewer function
function viewer(){
  var chart = new CanvasJS.Chart("chartContainer", {
    title:{
      text:"The most popular hidden services"
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
      name: "Tor2web visits",
      axisYType: "secondary",
      color: "#7E8F74",
      dataPoints: tor2web_list
    },
    {     
      type: "stackedBar",
      showInLegend: true,
      name: "Backlinks from public WWW",
      axisYType: "secondary",
      color: "#F0E6A7",
      dataPoints: backlinks_list
    },
    {
      type: "stackedBar",
      showInLegend: true,
      name: "Search results clicks",
      axisYType: "secondary",
      color: "#EBB88A",
      dataPoints: clicks_list
    }
    ]
  });
  chart.render();
}