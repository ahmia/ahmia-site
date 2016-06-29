
function include(file)
{

  var script  = document.createElement('script');
  script.src  = file;
  script.type = 'text/javascript';
  script.defer = true;

  document.getElementsByTagName('head').item(0).appendChild(script);

}

include('canvasjs.min.js');
$(function () {
  var info=new Array();
  $.ajax({
    type:'GET',
    async: false,
    url: 'https://ahmia.fi/stats/popularity?limit=100&offset=0&order_by=clicks',
    dataType: 'json',
    success: function(data){
      $.each(data,function(index, item){
        $.each(item, function(key, value){
          if(key=="fields"){
            info.push({about: this.about ,clicks: this.clicks ,tor2web: this.tor2web ,publinks: this.public_backlinks})
          }
        });
      });
    }
  });
  function compare(a,b) {
    if (a.about < b.about)
      return -1;
    if (a.about > b.about)
      return 1;
    return 0;
  }
  info.sort(compare);
  var dataPoints_clicks = [];
  for (var x = 0; x < info.length; x++) {
    dataPoints_clicks.push({ 
      y: info[x].clicks,
      label: info[x].about
    });
  }
  var dataPoints_tor2web = [];
  for (var x = 0; x < info.length; x++) {
    dataPoints_tor2web.push({ 
      y: info[x].tor2web,
      label: info[x].about
    });
  }
  var dataPoints_publinks = [];
  for (var x = 0; x < info.length; x++) {
    dataPoints_publinks.push({ 
      y: info[x].publinks,
      label: info[x].about
    });
  }
  var chart = new CanvasJS.Chart("chartContainer",
  {
    title:{
      text: "Popularity Graph",
      fontFamily: "robotoregular",
      fontColor: "#303030",
      fontSize: 30

    },
    animationEnabled: true,
    toolTip: {
      shared: true,
      content: function(e){
        var str = '';
        var total = 0 ;
        var str3;
        var str2 ;
        for (var i = 0; i < e.entries.length; i++){
          var  str1 = "<span style= 'color:#CB4335"+e.entries[i].dataSeries.color + "'> " + e.entries[i].dataSeries.name + ': ' + e.entries[i].dataPoint.y + "<br/>" ; 
          total = e.entries[i].dataPoint.y + total;
          str = str.concat(str1);
          str2 = "<span style = 'color:#229954; '><strong>"+ (e.entries[i].dataPoint.label) + "</strong></span><br/>";
        }
        total = Math.round(total*100)/100 
        str3 = "<span style = 'color:Tomato '>Total:</span><strong> " + total + "</strong> <br/>";

        return (str2.concat(str)).concat(str3); }

      },
      axisY:{
        title:"Visits",
        titleFontSize: 20,
        valueFormatString:"#0", 
        interval: 100000,
        gridColor: "#CACFD2",
        labelAngle: 20,
        labelFontSize: 15,
        tickColor: "#283747",
        interlacedColor: "#EBEDEF"

      },
      axisX: {
          //title:"Address",
          titleFontSize: 20,
          interval: 110,
          labelAngle: 90,
          labelFontSize: 8,
          valueFormatString: 'string'
        },
        legend: {
          fontSize: 15
        },
        backgroundColor: null,
        data: [
        {        
          type: "stackedColumn",       
          showInLegend:true,
          color: "#273746",
          name:"Clicks",
          dataPoints: dataPoints_clicks

        },
        {
          type: "stackedColumn",       
          showInLegend:true,
          name:"Tor2web",
          color: "#C81A45",
          dataPoints: dataPoints_tor2web
        },
        {        
          type: "stackedColumn",       
          showInLegend:true,
          name:"Public backlinks",
          color:"F4D03F",
          dataPoints: dataPoints_publinks
        }
        ]
      });

chart.render();
});