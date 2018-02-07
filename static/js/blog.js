$(function(){
    $(".markdown").each(function(){
        var blogContent = $(this).text();
        var markedContent = marked(blogContent);
        $(this).html(markedContent);
    });
});


var url = document.location.href;
new Clipboard('.btn', {
    text: function() {
      return url;
    }
  });