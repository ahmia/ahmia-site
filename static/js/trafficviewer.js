var hs_searches_list = []
var searches_list = []

// downloads JSON stats
function getStats(file, list){
  var url = "/static/log/"+file
  $.getJSON( url, function( json ) {
    $.each(json.searches, function (index, result) {
      //item = {y: result.fields[order_by], label: result.fields.about+".onion"}
      key = Object.keys(result)[0]
      count = result[key]
      // key = "01/Jun/2014:16:48:17 +0200"
      // to
      // key = "Jun 01, 2014 16:48:17"
      key = key.replace(" +0200", "")
      key = key.split("/")
      key = key[1] + " " + key[0] + ", " + key[2].substring(0,4) + " " + key[2].substring(5)
      // new Date(year, month, day, hours, minutes, seconds, milliseconds)
      // or
      // new Date("October 13, 1975 11:13:00")
      date = new Date(key)
      item = { x: date, y: count }
      list.push(item);
    });
    // wait until every list is ready
    if( Math.abs(hs_searches_list.length - searches_list.length) < 24 ){
      //show the results
      viewer();
    }
  });
}

getStats("access.json", searches_list);
getStats("hs_access.json", hs_searches_list);

function viewer(){
  draw_chart();
}

function draw_chart(){
		var chart = new CanvasJS.Chart("chartContainer",
		{

			title:{
				text: "Search count / hour",
				fontSize: 30
			},
			axisX:{

				gridColor: "Silver",
				tickColor: "silver",
				valueFormatString: "DD/MMM HH"

			},                        
                        toolTip:{
                          shared:true
                        },
			theme: "theme2",
			axisY: {
				gridColor: "Silver",
				tickColor: "silver"
			},
			legend:{
				verticalAlign: "center",
				horizontalAlign: "right"
			},
			data: [
			{        
				type: "line",
				showInLegend: true,
				lineThickness: 2,
				name: "Searches using https://ahmia.fi/search/",
				markerType: "square",
				color: "#F08080",
				dataPoints: searches_list
			},
			{        
				type: "line",
				showInLegend: true,
				name: "Searches using http://msydqstlz2kzerdg.onion/search/",
				color: "#20B2AA",
				lineThickness: 2,
				dataPoints: hs_searches_list
			}

			
			],
          legend:{
            cursor:"pointer",
            itemclick:function(e){
              if (typeof(e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
              	e.dataSeries.visible = false;
              }
              else{
                e.dataSeries.visible = true;
              }
              chart.render();
            }
          }
		});

chart.render();
}