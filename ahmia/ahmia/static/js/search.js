var glb_timeout = "";

(function ($) {
  // custom css expression for a case-insensitive contains()
  jQuery.expr[':'].Contains = function(a,i,m){
      return (a.textContent || a.innerText || "").toUpperCase().indexOf(m[3].toUpperCase())>=0;
  };
 
 
  function listFilter(list, input) { 
    $(input)
      .change( function () {
        var filter = $(this).val();
	filter = filter.replace(/^ +/gm, '');
        if(filter) {
          // this finds all links in a list that contain the input,
          // and hide the ones not containing the input while showing the ones that do
	  
	  // Hide
          var li_hide = $(list).find("li:not(:Contains(" + filter + "))");
	  li_hide.each(function( index ) {
	    li_hide[index].style.display = "none"
	  });
	  
	  // Show
          var li_show = $(list).find("li:Contains(" + filter + ")");
	  li_show.each(function( index ) {
	    li_show[index].style.display = "block"
	  });
	  
        } else {
	  // Show
          var li_show = $(list).find("li:Contains(" + filter + ")");
	  li_show.each(function( index ) {
	    li_show[index].style.display = "block"
	  });
        }
        showNumberOfResults();
	highlightText();
        return false;
      })
    .keyup( function () {
        // fire the above change event after every letter
        clearTimeout( glb_timeout ); // clear 
	glb_timeout = setTimeout( "makeSearch();", 2000 ); //wait until the user's writing is done
    });
  }
 
 
  //ondomready
  $(function () {
    var input = createSearch($("#search"));
    var searchTerm = readUrl();
    listFilter($("#list"), input);
    $("#torsearch").change();
  });
}(jQuery));

function makeSearch(){
  $("#torsearch").change();
}

function createSearch( header )
{
    // create and add the filter form to the header
    var form = $("<form>").attr({"class":"filterform","action":"#"}),
        input = $("<input>").attr({"class":"filterinput","id":"torsearch","type":"text","placeholder":"search term","autofocus":"autofocus"});
    $(form).append(input).appendTo(header);
    return input;
}

function highlightText()
{
  filter = $('input.filterinput').val();
  $('li').removeHighlight();
  filter = filter.replace(/^ +/gm, '');
  if( filter ) {     
        handleUrl( filter );
  	$(list).highlight(filter);
  }
}

function showNumberOfResults() {
  //show number of results in the end of the list
  var results = $("#list > *").filter(":visible").size();
  $("#totalresults").html(results);
}

function handleUrl( word )
{
  word = word.replace(/ /g,"%20");
  window.location.hash = "#/search="+word;
}

function readUrl()
{
  var term = window.location.hash.replace("#/search=","");
  term = term.replace(/%20/g," ");
  document.getElementById("torsearch").value = term;
  return term;
}


