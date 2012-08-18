(function(){
  function getHandler(width, height, img, req){
    return function(){
      if(req.readyState === 4){
        img.setAttribute('width', width);
        img.setAttribute('height', height);
        img.setAttribute('src', req.responseText);
      }
    }
  }
  function requestImage(width, height, img, i){
    var req = new XMLHttpRequest();
    req.open('GET', 'http://localhost:5000/image/'+width+'/'+height+'?cache='+Date.now()+''+i);
    req.onreadystatechange = getHandler(width, height, img, req);
    req.send();
  }
  var images = document.getElementsByTagName('img');
  for(var i=0; i<images.length; i++){
    if(images[i].clientWidth > 10 && images[i].clientHeight > 10){
      requestImage(images[i].clientWidth, images[i].clientHeight, images[i], i);
    }
  }
})();
