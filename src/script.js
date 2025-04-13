var galleryInfo = [
    info("Brinley Zhao", "Clouds and Light", "Clouds and Light"), 
    info("Skylar Larsen", "Seasons in Moominvalley", "Seasons in Moominval"),
]; 

function info(artist, description, shortDesc){return {artist, description, shortDesc}}; // Replaced by deploy script

// First line will be deleted
// Info format is: { artist, description, shortDesc }

var screenSizeQuery = window.matchMedia("(max-width: 768px)");
screenSizeQuery.addListener(function(query){
    if(query.matches){
        hideModal();
    }
});

var modal;
var modalDisplay;
var modalInfo;
var galleryOverlay;
var galleryInfoDisplay;

function onload(){
    modal = document.getElementById("modal");
    modalDisplay = document.getElementById("piece");
    modalInfo = document.getElementById("modal-info");
    galleryOverlay = document.getElementById("gallery-overlay");
    galleryInfoDisplay = document.getElementsByClassName("gallery-info")[0];
    document.getElementById("exec").scrollLeft = 40;
}

function showModal(content, galleryId){
    content = content.cloneNode(true);
    content.onclick = null;
    content.classList.remove("gallery-media");

    modalDisplay.appendChild(content);
    var info = galleryInfo[galleryId];
    modalInfo.innerHTML = `${info.shortDesc}<br/><b>${info.artist}</b>`;
    modal.classList.add("modal");
}

function showOverlay(content, galleryId){
    content.onmouseenter = null;
    var overlay = galleryOverlay.cloneNode(true);
    overlay.style.display = "block";
    var infoDisplay = overlay.firstElementChild;

    content.appendChild(overlay);
    var info = galleryInfo[galleryId];
    infoDisplay.innerHTML = `${info.shortDesc}<br/><b>${info.artist}</b>`;

    content.onclick = function(){
        if(!screenSizeQuery.matches){
            showModal(content.querySelector(".gallery-media"), galleryId);
        }
    };

    setTimeout(function(){
        overlay.style.animation = "none";
    }, 200);
}

function hideModal(){
    modalDisplay.textContent = "";
    modal.classList.remove("modal");
};

window.addEventListener("click", function(e){
    if(e.target == modal){
        hideModal();
    }
});

window.addEventListener("keydown", hideModal);
