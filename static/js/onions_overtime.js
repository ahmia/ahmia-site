var data = [];

// downloads JSON over time stats
function getOverTimeData( onion ){
    var url = "/static/log/onion_site_history/" + onion + ".json"
    var dataPoints = [];
    var dataSeries = {
        visible: true,
        type: "line",
        showInLegend: true,
        markerType: "none",
        name: onion + ".onion"
        };
    $.getJSON( url, function( json ) {
      $.each(json, function (index, result) {
          for (var key in result) {
            if (result.hasOwnProperty(key)) {
                // add new date - visit count pair
                // fill the missing dates
                var time_stamp = key.split("-");
                // month must be 0-11
                // 0 -> Jan ... 11 -> Dec
                var month = parseInt(time_stamp[1])-1;
                var new_time = new Date(time_stamp[0], month, time_stamp[2]);
                dataPoints.push({
                    x: new_time,
                    y: result[key]
                });
            }
          }
      });
      dataSeries.dataPoints = dataPoints;
      data.push(dataSeries);
      $("input[value='" + onion + "']").prop('checked', true);
      viewer();
    });
}

function viewer(){
    var chart = new CanvasJS.Chart("chartContainer",
    {
        zoomEnabled: true,
        animationEnabled: true,
        title:{
            text: "Zoom-in by selecting area with mouse"
        },
        axisX :{
            labelAngle: -30
        },
        axisY :{
            includeZero: false
        },
        data: data
    });
    chart.render();
}

// When onion is selected using checkbox
var onion_check = function() {
    var onion = this.value;
    if ($(this).is (':checked'))
    {
        var found = false;
        // Check if we already have the data
        jQuery.each(data, function(index, value) {
            if ( this.name == onion + ".onion" ) {
                this.visible = true;
                found = true;
                viewer();
            }
        });
        // Get the JSON data
        if( !found ){
            getOverTimeData( onion ); // Get JSON
        }
    }
    // This option is not selected
    else {
        jQuery.each(data, function(index, value) {
            // Unselect this data
            if ( this.name == onion + ".onion" ) {
                this.visible = false;
                viewer();
            }
        });
    }
}

function createOnionOptionMenu(){
    var url = "/static/log/onion_site_history/onions.json";
    $.getJSON( url, function( json ) {
      $.each(json, function (index, result) {
          var content = '<input type="checkbox" value="' + result + '" />' + result + '.onion<br />';
          if( !isNaN(parseInt(result[0])) ) {
              $( "#select_onions_1" ).append( content );
          }
          else if( 97 <= result.charCodeAt(0) && result.charCodeAt(0) <= 104 ) {
              $( "#select_onions_2" ).append( content );
          }
          else if( 105 <= result.charCodeAt(0) && result.charCodeAt(0) <= 113 ) {
              $( "#select_onions_3" ).append( content );
          }
          else if( 114 <= result.charCodeAt(0) && result.charCodeAt(0) <= 122 ) {
              $( "#select_onions_4" ).append( content );
          }
          else {
              console.log("ERROR: " + result);
          }

      });
      $( "input" ).on( "click", onion_check );
      $('.uncheck:button').click(function(){
          $('input:checkbox').each( function(){
              if( $(this).is(':checked') ){
                  var onion = this.value;
                  jQuery.each(data, function(index, value) {
                      // Unselect this data
                      if ( this.name == onion + ".onion" ) {
                          this.visible = false;
                          $("input[value='" + onion + "']").prop('checked', false);
                      }
                  });
              }
          });
          viewer();
      });
  });
}

// When HTML is loaded
$( document ).ready(function() {
    createOnionOptionMenu();
});
