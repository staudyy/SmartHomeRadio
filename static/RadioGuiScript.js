function post(data) {
    $.post("/chromecast", data)
        .fail(function(xhr, status, error) {
            document.getElementById("statusText").innerHTML = 'ERROR Vypnutý server';
            setVybranaText("")
        });
}

function sendRequest(action, url=null) {
    if (url !== null) {
        post({'action':action, 'url':url})
    } else {
        post({'action':action})
    }
}

function onDesign(){
    document.getElementById("statusText").innerHTML = 'Rádio zapnuté';
    document.getElementById("buttonOn").style.color = "#FF0000"
    document.getElementById("buttonOff").style.color = "#000000"
}

function offDesign(){
    document.getElementById("statusText").innerHTML = 'Rádio vypnuté';
    document.getElementById("buttonOff").style.color = "#FF0000"
    document.getElementById("buttonOn").style.color = "#000000"
}

function zapnut(){
    onDesign()
    sendRequest('url', getSelectedStanica().getAttribute("data-url"));
    sendRequest('play')
    setVybranaText(getSelectedStanica().textContent)
}
function vypnut(){
    offDesign()
    sendRequest('pause')
    setVybranaText("")

}

function connect(){
    sendRequest('connect')
}

function disconnect(){
    sendRequest('disconnect')
}

function stop(){
    sendRequest('stop')
}

$(document).ready(function(){
    staniceSetup()
    //sliderInput()
    loadSettings()
    //sliderChange()
})

function setVybranaText(text) {
    document.getElementById("vybrana").innerHTML = text;
}

function loadSettings() {
    //data = {"is_playing":"<Boolean>", "url":"<link>", "volume":<int>}
    $.get("/setup", function (data) {

    if (data.is_playing == true) {
        onDesign()

        setVybranaText(getStanicaByUrl(data.url).textContent)
    } else {
        offDesign()
    }

    if (data.volume >= 0) {
        slider = document.getElementById("volumeController")
        slider.value = data.volume
    }
    sliderInput()

    })
}

function staniceSetup() {
    const links =  [
        {"name":"Funrádio", "url":"https://stream.funradio.sk:18443/fun192.mp3"},
        {"name":"Európa 2", "url":"https://stream.bauermedia.sk/europa2-hi.mp3"},
        {"name":"Rádio Vlna", "url":"https://stream.radiovlna.sk/vlna-hi.mp3"},
        {"name":"Express", "url":"https://stream.bauermedia.sk/128.mp3"},
        {"name":"SRO 1", "url":"https://icecast.stv.livebox.sk/slovensko_128.mp3"},
        {"name":"Rádio Viva", "url":"https://stream.sepia.sk/viva320.mp3"},
        {"name":"Melody", "url":"https://stream.bauermedia.sk/melody-hi.mp3"},
        {"name":"Rádio Rock", "url":"https://stream.bauermedia.sk/rock-hi.mp3"}
    ];

    const staniceDiv = document.getElementById("stanice")
    for (let i = 0; i < links.length; i++) {
        const node = document.createElement("button");
        const textnode = document.createTextNode(links[i].name);
        node.setAttribute('data-url', links[i].url)
        node.setAttribute("data-selected", "false")
        node.setAttribute("class", getBootstrapString())
        node.setAttribute("onClick", "setSelectedStanica(this);")
        node.appendChild(textnode);
        staniceDiv.appendChild(node);
    }
    
    cookie = getCookie('stanica')
    const stanice = document.getElementById("stanice").children
    var success = false
    for (let i = 0; i < stanice.length; i++) {
        if (stanice[i].textContent == cookie) {
            setSelectedStanica(stanice[i])
            success = true
            break
        }
    }
    if (!success){
        console.log('neni cookie')
        setSelectedStanica(stanice[0])
    }

}

function getBootstrapString(active=false) {
    classes = [
        "list-group-item",
        "list-group-item-action"
    ]
    if (active) {
        classes.push("active")
    }
    return classes.join(" ")
}

function setSelectedStanica(selected) {
    const stanice = document.getElementById("stanice").children
    for (let i = 0; i < stanice.length; i++) {
        if (stanice[i].getAttribute("data-selected") == "true") {
            stanice[i].setAttribute("data-selected", "false")
            stanice[i].setAttribute("class", getBootstrapString())
        }
    }
    selected.setAttribute("data-selected", "true")
    selected.setAttribute("class", getBootstrapString(true))
    
    setCookie('stanica', selected.textContent, 365*5);
}
function getSelectedStanica(){
    const stanice = document.getElementById("stanice").children
    for (let i = 0; i < stanice.length; i++) {
        if (stanice[i].getAttribute("data-selected") == "true") {
            return stanice[i]
        }
    }
}
function getStanicaByUrl(url){
    const stanice = document.getElementById("stanice").children
    for (let i = 0; i < stanice.length; i++){
        if (stanice[i].getAttribute("data-url") == url) {
            return stanice[i]
        }
    }
}

function sliderInput() {
    slider = document.getElementById("volumeController")
    document.getElementById("volume").innerHTML = slider.value
}

function sliderChange() {
    slider = document.getElementById("volumeController")
    post({"action" : "volume", "value" : slider.value})
}


function setCookie(cname, cvalue, exdays){
    const d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    let expires = "expires="+d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
    let name = cname + "=";
    let ca = document.cookie.split(';');
    for(let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) == ' ') {
        c = c.substring(1);
      }
      if (c.indexOf(name) == 0) {
        return c.substring(name.length, c.length);
      }
    }
    return "";
  }
