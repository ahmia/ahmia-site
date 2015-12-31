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
  
  var online_selection = '<label class="nostyle" for="online"><strong class="color12">Online</strong> (' + onlinecount + ')</label>';
  online_selection = online_selection + '<input type="radio" name="status" id="online" value="online">';
  var offline_selection = '<label class="nostyle" for="offline"><strong class="color1">Offline</strong> (' + offlinecount + ')</label>';
  offline_selection = offline_selection + '<input type="radio" name="status" id="offline" value="offline">';
  var all_selection = '<label class="nostyle" for="hs_site"><strong>All</strong> (' + total + ')</label>';
  all_selection = all_selection + '<input type="radio" name="status" id="hs_site" value="hs_site" checked="checked">';
  
  filter_form.append( all_selection );
  filter_form.append( online_selection );
  filter_form.append( offline_selection );
  
  filter_form.change(function() {
    filter_hses();
  });
  
});
