var btype = 'STANDARD';
var map;
var rawpathcache = [];
var circleslist = [];
var currpaths = new Array();
var waypointsToggle = true;

function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 8,
        center: {lat: 37.4275, lng: -122.1697}, // Stanford area
        mapTypeId: google.maps.MapTypeId.TERRAIN
    });

    google.maps.event.addListener(map, 'click', function(event) {
        displayCoordinates(event.latLng);
    });

    setDefaultDate();
}

function setDefaultDate() {
    const validDate = {
        year: 2024,
        month: 12,  // December
        day: 31,
        hour: 12,
        minute: 0
    };
    
    document.getElementById('yr').value = validDate.year;
    document.getElementById('mo').value = validDate.month;
    document.getElementById('day').value = validDate.day;
    document.getElementById('hr').value = validDate.hour;
    document.getElementById('mn').value = validDate.minute;
    
    // Allow date selection within valid range
    document.getElementById('yr').disabled = false;
    document.getElementById('mo').disabled = false;
    document.getElementById('day').disabled = false;
    document.getElementById('hr').disabled = false;
    document.getElementById('mn').disabled = false;
    
    // Set reasonable defaults for other fields if empty
    if (!document.getElementById('lat').value) {
        document.getElementById('lat').value = '37.4275';
    }
    if (!document.getElementById('lon').value) {
        document.getElementById('lon').value = '-122.1697';
    }
    if (!document.getElementById('alt').value) {
        document.getElementById('alt').value = '0';
    }
    if (!document.getElementById('equil').value) {
        document.getElementById('equil').value = '30000';
    }
    if (!document.getElementById('asc').value) {
        document.getElementById('asc').value = '5';
    }
    if (!document.getElementById('desc').value) {
        document.getElementById('desc').value = '10';
    }
}

function makepaths(btype, allpaths) {
    rawpathcache.push(allpaths);
    for (index in allpaths) {
        var pathpoints = [];
        for (point in allpaths[index]) {
            var position = {
                lat: allpaths[index][point][1],
                lng: allpaths[index][point][2],
            };
            pathpoints.push(position);
        }
        var drawpath = new google.maps.Polyline({
            path: pathpoints,
            geodesic: true,
            strokeColor: getcolor(index),
            strokeOpacity: 1.0,
            strokeWeight: 2
        });
        drawpath.setMap(map);
        currpaths.push(drawpath);
    }
}

function clearWaypoints() {
    for (var i = 0; i < circleslist.length; i++) {
        circleslist[i].setMap(null);
    }
    circleslist = [];
}

function showWaypoints() {
    for (i in rawpathcache) {
        allpaths = rawpathcache[i];
        for (index in allpaths) {
            for (point in allpaths[index]) {
                (function() {
                    var position = {
                        lat: allpaths[index][point][1],
                        lng: allpaths[index][point][2],
                    };
                    if (waypointsToggle) {
                        var circle = new google.maps.Circle({
                            strokeColor: getcolor(index),
                            strokeOpacity: 0.8,
                            strokeWeight: 2,
                            fillColor: getcolor(index),
                            fillOpacity: 0.35,
                            map: map,
                            center: position,
                            radius: 300,
                            clickable: true
                        });
                        circleslist.push(circle);
                        var date = new Date(allpaths[index][point][0] * 1000);
                        var hours = date.getHours();
                        var minutes = "0" + date.getMinutes();
                        var seconds = "0" + date.getSeconds();

                        var formattedTime = hours + ':' + minutes.substr(-2) + ':' + seconds.substr(-2);
                        var infowindow = new google.maps.InfoWindow({
                            content: "Altitude: " + allpaths[index][point][3] + "m \n \n \n Time: " + formattedTime
                        });
                        circle.addListener("mouseover", function() {
                            infowindow.setPosition(circle.getCenter());
                            infowindow.open(map);
                        });
                        circle.addListener("mouseout", function() {
                            infowindow.close(map);
                        });
                    }
                }());
            }
        }
    }
}

function showpath(path) {
    switch (btype) {
        case 'STANDARD':
            var rise = path[0];
            var equil = [];
            var fall = path[2];
            var fpath = [];
            break;
        case 'ZPB':
            var rise = path[0];
            var equil = path[1];
            var fall = path[2];
            var fpath = [];
            break;
        case 'FLOAT':
            var rise = [];
            var equil = [];
            var fall = [];
            var fpath = path;
    }
    var allpaths = [rise, equil, fall, fpath];
    makepaths(btype, allpaths);
}

function getcolor(index) {
    switch (index) {
        case '0':
            return '#DC143C';  // Red for rise
        case '1':
            return '#0000FF';  // Blue for equilibrium
        case '2':
            return '#000000';  // Black for fall
        case '3':
            return '#000000';  // Black for other paths
    }
}

async function simulate() {
    // Validate date before proceeding
    const currentDate = new Date(
        document.getElementById('yr').value,
        document.getElementById('mo').value - 1,
        document.getElementById('day').value,
        document.getElementById('hr').value,
        document.getElementById('mn').value
    );
    
    // Using our current GEFS cycle data range
    const validStart = new Date(2024, 11, 31, 12, 0); // Dec 31, 2024 12Z
    const validEnd = new Date(2025, 0, 15, 0, 0);    // Jan 15, 2025
    
    if (currentDate < validStart || currentDate > validEnd) {
        alert('Simulation available for Dec 31, 2024 12Z through Jan 15, 2025');
        return;
    }
    
    clearWaypoints();
    for (path in currpaths) { currpaths[path].setMap(null); }
    currpaths = new Array();
    rawpathcache = new Array();
    console.log("Clearing");

    allValues = [];
    var time = toTimestamp(Number(document.getElementById('yr').value),
        Number(document.getElementById('mo').value),
        Number(document.getElementById('day').value),
        Number(document.getElementById('hr').value),
        Number(document.getElementById('mn').value));
    var lat = document.getElementById('lat').value;
    var lon = document.getElementById('lon').value;
    var alt = document.getElementById('alt').value;
    var url = "";
    allValues.push(time, alt);

    switch (btype) {
        case 'STANDARD':
            var equil = document.getElementById('equil').value;
            var asc = document.getElementById('asc').value;
            var desc = document.getElementById('desc').value;
            url = URL_ROOT + "/singlezpb?timestamp=" +
                time + "&lat=" + lat + "&lon=" + lon + "&alt=" + alt + "&equil=" + equil + "&eqtime=" + 0 + "&asc=" + asc + "&desc=" + desc;
            allValues.push(equil, asc, desc);
            break;
        case 'ZPB':
            var equil = document.getElementById('equil').value;
            var eqtime = document.getElementById('eqtime').value;
            var asc = document.getElementById('asc').value;
            var desc = document.getElementById('desc').value;
            url = URL_ROOT + "/singlezpb?timestamp=" +
                time + "&lat=" + lat + "&lon=" + lon + "&alt=" + alt + "&equil=" + equil + "&eqtime=" + eqtime + "&asc=" + asc + "&desc=" + desc;
            allValues.push(equil, eqtime, asc, desc);
            break;
        case 'FLOAT':
            var coeff = document.getElementById('coeff').value;
            var step = document.getElementById('step').value;
            var dur = document.getElementById('dur').value;
            url = URL_ROOT + "/singlepredict?timestamp=" +
                time + "&lat=" + lat + "&lon=" + lon + "&alt=" + alt + "&rate=0&coeff=" + coeff + "&step=" + step + "&dur=" + dur;
            allValues.push(coeff, step, dur);
            break;
    }

    var onlyonce = true;
    if (checkNumPos(allValues) && checkasc(asc, alt, equil)) {
        for (i = 1; i < 21; i++) {
            var url2 = url + "&model=" + i;
            console.log(url2);
            await fetch(url2).then(res => res.json()).then(function(resjson) {
                if (resjson === "error") {
                    if (onlyonce) {
                        alert("ERROR: Please make sure your entire flight is within the forecast window (Dec 31 - Jan 15).");
                        onlyonce = false;
                    }
                } else {
                    showpath(resjson);
                }
            });
        }
        onlyonce = true;
    }
    if (waypointsToggle) { showWaypoints(); }
}
