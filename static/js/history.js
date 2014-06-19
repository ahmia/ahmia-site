function filter_hses() {
  var lis = $("li");
  
  lis.each(function( index ) {
    lis[index].style.display = "none";
  });
  
  var selection = $("form input:radio:checked").val();
  var classselection = '.' + selection;
  
  var selected_lis = lis.filter(classselection);
  
  selected_lis.each(function( index ) {
    selected_lis[index].style.display = "block"
  });
}


$(document).ready(function() {
  
  // Gets the number of elements representing HSes
  var onlinecount = $('.online').length
  var offlinecount = $('.offline').length
  // Total number of HSes
  var total = parseInt(onlinecount) + parseInt(offlinecount);
  
  // Build filtering buttons
  var filter_form = $("form");
  
  var online_selection = '<input type="radio" name="status" value="online"> <strong class="color12">Online</strong> (' + onlinecount + ')';
  var offline_selection = '<input type="radio" name="status" value="offline"> <strong class="color1">Offline</strong> (' + offlinecount + ')';
  var all_selection = '<input type="radio" name="status" value="hs_site" checked="checked"> <strong>All</strong> (' + total + ')';
  
  filter_form.append( all_selection );
  filter_form.append( online_selection );
  filter_form.append( offline_selection );
  
  filter_form.change(function() {
    filter_hses();
  });
  
});
