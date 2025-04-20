/**
 * Functions useful for the site in one JS to save on page sizes (save the electrons!)
 * 
 * 
*/

//Adds a confirmation popup before submitting the form (or just submit if pmessage == '')
function clickConfirm(pname, pvalue, pmessage="Sure ?") {
    if (pmessage == '' || confirm(pmessage)){
        var f = document.getElementById('theForm');

        var hiddenField = document.createElement('input');
        hiddenField.type = 'hidden';
        hiddenField.name = pname;
        hiddenField.value = pvalue;

        f.appendChild(hiddenField);


        //Adds all the range inputs to the form manually
        var ins = document.querySelectorAll('input[type=range]');
        for (var i = 0; i < ins.length; i++) {
            var input = ins[i];

            var hiddenField = document.createElement('input');
            hiddenField.type = 'hidden';
            hiddenField.name = input.id;
            hiddenField.value = input.value;
    
            f.appendChild(hiddenField);
        }

        f.submit();
    }
}


var latestStatus = null;

//Updates the STATUS box
function updateCurrentStatus(){

    //https://stackoverflow.com/questions/36975619/how-to-call-a-rest-web-service-api-from-javascript
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
            var d = document.getElementById('currentstatus');
            //you got to love JS to use it. I don't.
            const regex = /\n/g;
            latestStatus = JSON.parse(this.responseText);
            d.innerHTML = `<b>Current Status:</b>&nbsp;${latestStatus.status}<br/><b>Port:</b>&nbsp;${latestStatus.port}`
            }
    };
    xhttp.open("GET", "/status", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.send();
}


/* 
 * POOR MAN VERY BASIC REGEX SYNTAX HIGHLIGHTING v(^-^)v 
*/
//Taken from here (one of the solutions at the bottom)
//https://stackoverflow.com/questions/30910516/change-text-color-of-matching-text-from-input-in-javascript
function highlight(pattern, color) {
    var inputText = document.getElementById("filebody");
    var re = new RegExp(pattern, 'g');

    inputText.innerHTML = inputText.innerHTML.replace(re, function (match) {
                    return '<span style="color:'+color+ ';">' + match + '</span>';
                });
}



function zoomImage(original, result, fromx, fromy, tox, toy){
    console.log(`Zooming from ${fromx},${fromy} to ${tox},${toy}`);

    var result = document.getElementById(result);
    var original = document.getElementById(original);
    
    //by default images are 10px/mm (should be variable but too much added work for now)
    var pixPerMM = 10; 

    //produit en croix: result size is fixed, so ratio of the image zoomed in over the whole size gives the soomed size of the image
    var canvasWidth = result.clientWidth;
    var zoomedInWidth = Math.abs(tox-fromx)*pixPerMM;
    var imageOriginalWidth = original.naturalWidth;
    var imageZoomedWidth = Math.round((canvasWidth*imageOriginalWidth)/zoomedInWidth);
    var ratioW = imageZoomedWidth/imageOriginalWidth;

    var canvasHeight = result.clientHeight;
    var zoomedInHeight = Math.abs(toy-fromy)*pixPerMM;
    var imageOriginalHeight = original.naturalHeight;
    var imageZoomedHeight = Math.round((canvasHeight*imageOriginalHeight)/zoomedInHeight);
    var ratioH = imageZoomedHeight/imageOriginalHeight;

    console.log(`Canvas width: ${canvasWidth}, Image original width: ${imageOriginalWidth}, zoomed in width: ${zoomedInWidth}, image zoomed width: ${imageZoomedWidth}`);
    console.log(`Canvas height: ${canvasHeight}, Image original height: ${imageOriginalHeight}, zoomed in height: ${zoomedInHeight}, image zoomed height: ${imageZoomedHeight}`);

    //keep the smallest zoom and recalculate
    var zaRatio = Math.min(ratioW, ratioH);
    imageZoomedWidth = Math.round(imageOriginalWidth*zaRatio);
    imageZoomedHeight = Math.round(imageOriginalHeight*zaRatio);

    console.log(`Image zoomed width: ${imageZoomedWidth}, Image zoomed height: ${imageZoomedHeight}`);

    var posx = -Math.round(fromx*pixPerMM * zaRatio);
    if (zaRatio != ratioW){
        //not my preferred ratio, so I need to center the image in the canvas

        //width of the shown area, scaled to the zoomed image
        var zoomed = Math.round(Math.abs(tox - fromx)*pixPerMM * zaRatio);
        //slide the image to the center of the canvas
        posx = posx + (canvasWidth - zoomed) / 2;
    }

    //align to the TOP of what you want to zomm in so toY, and Y coords are from the bottom of the image so invert
    var posy = -Math.round((imageOriginalHeight - toy*pixPerMM ) * zaRatio);
    if (zaRatio != ratioH){
        //not my preferred ratio, so I need to center the image in the canvas

        //height of the shown area, scaled to the zoomed image
        var zoomed = Math.round(Math.abs(toy - fromy)*pixPerMM * zaRatio);
        //slide the image to the center of the canvas
        posy = posy + (canvasHeight - zoomed) / 2;
    }

    console.log(`Position x: ${posx}, Position y: ${posy}`);

    result.style.backgroundColor = 'white';
    result.style.backgroundImage = `url(${original.src})`;
    result.style.backgroundSize = `${imageZoomedWidth}px ${imageZoomedHeight}px`;
    result.style.backgroundRepeat = 'no-repeat';
    result.style.backgroundPosition = `${posx}px ${posy}px`;

    original.style.display = 'none';
}