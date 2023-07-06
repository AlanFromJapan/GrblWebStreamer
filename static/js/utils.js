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
        f.submit();
    }
}



//Updates the STATUS box
function updateCurrentStatus(){

    //https://stackoverflow.com/questions/36975619/how-to-call-a-rest-web-service-api-from-javascript
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
            var d = document.getElementById('currentstatus');
            //you got to love JS to use it. I don't.
            const regex = /\n/g;
            d.innerHTML = this.responseText.replace(regex, '<br/>');
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