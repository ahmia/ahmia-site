$( document ).ready(function() {
   // Download JSON stats
   $.getJSON("/static/log/nonweb_services.json",
   function(data) {
       var div1 = $("#ports_div1");
       var div2 = $("#ports_div2");
       var div3 = $("#ports_div3");
       var div4 = $("#ports_div4");
       // Build HTML lists
       $.each(data, function(key, val) {
           var new_div = $('<div></div>');
           var h3 = $('<h3>' + key + '</h3>');
           h3.appendTo(new_div);
           var ul = $('<ul style="list-style-type: none; padding: 0px;"></ul>');
           ul.appendTo(new_div);
           $.each(val, function(k, v){
               $('<li>'+v+'</li>').appendTo(ul);
           });
           // Append to div that height is the smallest
           // Looks better
           var div = div1;
           if( div.height() > div2.height() ){
               div = div2;
           }
           if( div.height() > div3.height() ){
               div = div3;
           }
           if( div.height() > div4.height() ){
               div = div4;
           }
           new_div.appendTo(div);
       });
   });
});
