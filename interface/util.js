//Maps initialization
var element = document.getElementById("map");
var map = new google.maps.Map(element, {
    center: new google.maps.LatLng(37.4, -121.5),
    zoom: 9,
    mapTypeId: "OSM",
    zoomControl: false,
    gestureHandling: 'greedy'
});

google.maps.event.addListener(map, 'click', function (event) {
    displayCoordinates(event.latLng);
});

//Define OSM map type pointing at the OpenStreetMap tile server
map.mapTypes.set("OSM", new google.maps.ImageMapType({
    getTileUrl: function(coord, zoom) {
        // "Wrap" x (longitude) at 180th meridian properly
        // NB: Don't touch coord.x: because coord param is by reference, and changing its x property breaks something in Google's lib
        var tilesPerGlobe = 1 << zoom;
        var x = coord.x % tilesPerGlobe;
        if (x < 0) {
            x = tilesPerGlobe+x;
        }
        // Wrap y (latitude) in a like manner if you want to enable vertical infinite scrolling
        return "https://tile.openstreetmap.org/" + zoom + "/" + x + "/" + coord.y + ".png";
    },
    tileSize: new google.maps.Size(256, 256),
    name: "OpenStreetMap",
    maxZoom: 18
}));

// Functions for displaying things
function displayCoordinates(pnt) {
    var lat = pnt.lat();
    lat = lat.toFixed(4);
    var lng = pnt.lng();
    lng = lng.toFixed(4);
    document.getElementById("lat").value = lat;
    document.getElementById("lon").value = lng;
    getElev();
}

function getElev() {
    let lat = document.getElementById("lat").value;
    let lng = document.getElementById("lon").value;
    fetch(URL_ROOT + "/elev?lat=" + lat + "&lon=" + lng)
        .then(res => res.json())
        .then((result) => {
            document.getElementById("alt").value = result;
        })
        .catch(error => {
            console.error('Error fetching elevation:', error);
            document.getElementById("alt").value = 0;  // Fallback to 0 if error
        });
}

function getTimeremain() {
    let alt = parseFloat(document.getElementById("alt").value);
    let eqalt = parseFloat(document.getElementById("equil").value);
    
    if (isNaN(alt) || isNaN(eqalt)) {
        document.getElementById("timeremain").textContent = "Invalid altitude values";
        return;
    }
    
    if (alt < eqalt) {
        let ascr = parseFloat(document.getElementById("asc").value);
        if (isNaN(ascr) || ascr === 0) {
            document.getElementById("timeremain").textContent = "Invalid ascent rate";
            return;
        }
        let time = (eqalt - alt)/(3600*ascr);
        document.getElementById("timeremain").textContent = time.toFixed(2) + " hr ascent remaining";
    }
    else {
        let descr = parseFloat(document.getElementById("desc").value);
        if (isNaN(descr) || descr === 0) {
            document.getElementById("timeremain").textContent = "Invalid descent rate";
            return;
        }
        let lat = document.getElementById("lat").value;
        let lng = document.getElementById("lon").value;
        fetch(URL_ROOT + "/elev?lat=" + lat + "&lon=" + lng)
            .then(res => res.json())
            .then((ground) => {
                let time = (alt - ground)/(3600*descr);
                document.getElementById("timeremain").textContent = time.toFixed(2) + " hr descent remaining";
            })
            .catch(error => {
                console.error('Error calculating descent time:', error);
                document.getElementById("timeremain").textContent = "Error calculating time";
            });
    }
}

async function habmc() {
    let activemissionurl = "https://stanfordssi.org/transmissions/recent";
    const proxyurl = "https://cors-anywhere.herokuapp.com/";
    try {
        const response = await fetch(proxyurl + activemissionurl);
        const contents = await response.text();
        habmcshow(contents);
        getTimeremain();
    } catch (error) {
        console.error("Can't access " + activemissionurl + ". Error:", error);
        alert("Unable to fetch HABMC data. Server may be unavailable.");
    }
}

function toTimestamp(year, month, day, hour, minute) {
    var datum = new Date(Date.UTC(year, month-1, day, hour, minute));
    return datum.getTime()/1000;
}

function checkNumPos(numlist) {
    for (var each in numlist) {
        if (isNaN(numlist[each]) || Math.sign(numlist[each]) === -1 || !numlist[each]) {
            alert("ATTENTION: All values should be positive numbers, check your inputs again!");
            return false;
        }
    }
    return true;
}

function checkasc(asc, alt, equil) {
    if (alt < equil && asc === "0") {
        alert("ATTENTION: Ascent rate is 0 while balloon altitude is below its descent ready altitude");
        return false;
    }
    return true;
}

function habmcshow(data) {
    try {
        let jsondata = JSON.parse(data);
        let checkmsn = activeMissions[CURRENT_MISSION];
        
        let foundTransmission = false;
        for (let transmission in jsondata) {
            if (jsondata[transmission]['mission'] === checkmsn) {
                console.log(jsondata[transmission]);
                habmcshoweach(jsondata[transmission]);
                foundTransmission = true;
                break;
            }
        }
        
        if (!foundTransmission) {
            console.log("No transmissions found for mission:", CURRENT_MISSION);
        }
    } catch (error) {
        console.error("Error processing HABMC data:", error);
    }
}

function habmcshoweach(data2) {
    // Check if we have valid data
    if (!data2 || !data2["Human Time"]) {
        console.error("Invalid transmission data");
        return;
    }

    try {
        let datetime = data2["Human Time"];
        var res = (datetime.substring(0,11)).split("-");
        var res2 = (datetime.substring(11,20)).split(":");
        var hourutc = parseInt(res2[0]) + 7;// Fix this for daylight savings...
        
        if (hourutc >= 24) {
            document.getElementById("hr").value = hourutc - 24;
            document.getElementById("day").value = parseInt(res[2]) + 1;
        } else {
            document.getElementById("hr").value = hourutc;
            document.getElementById("day").value = parseInt(res[2]);
        }
        
        document.getElementById("mn").value = parseInt(res2[1]);
        document.getElementById("yr").value = parseInt(res[0]);
        document.getElementById("mo").value = parseInt(res[1]);
        
        // Update coordinates and create map marker
        let lat = parseFloat(data2["latitude"]);
        let lon = parseFloat(data2["longitude"]);
        
        if (isNaN(lat) || isNaN(lon)) {
            console.error("Invalid coordinates in transmission");
            return;
        }
        
        document.getElementById("lat").value = lat;
        document.getElementById("lon").value = lon;
        
        let position = {
            lat: lat,
            lng: lon,
        };
        
        // Create circle on map
        var circle = new google.maps.Circle({
            strokeColor: '#FF0000',
            strokeOpacity: 0.8,
            strokeWeight: 2,
            fillColor: '#FF0000',
            fillOpacity: 0.35,
            map: map,
            center: position,
            radius: 5000,
            clickable: true
        });
        
        // Create info window with flight data
        var infoContent = `Altitude: ${data2["altitude_gps"]}m<br>`;
        if (data2["groundSpeed"]) infoContent += `Ground speed: ${data2["groundSpeed"]}`;
        if (data2["direction"]) infoContent += data2["direction"];
        if (data2["ascentRate"]) infoContent += `<br>Ascent rate: ${data2["ascentRate"]}`;
        
        var infowindow = new google.maps.InfoWindow({
            content: infoContent
        });

        // Add mouse event listeners
        circle.addListener("mouseover", function() {
            infowindow.setPosition(circle.getCenter());
            infowindow.open(map);
        });
        
        circle.addListener("mouseout", function() {
            infowindow.close(map);
        });
        
        // Pan map to current position
        map.panTo(new google.maps.LatLng(lat, lon));

        // Update altitude and rates
        let alt = parseFloat(data2["altitude_gps"]);
        document.getElementById("alt").value = alt;
        
        let rate = parseFloat(data2["ascentRate"]);
        if (!isNaN(rate)) {
            if (rate > 0) {
                document.getElementById("asc").value = rate;
            } else {
                document.getElementById("equil").value = alt;
                document.getElementById("desc").value = -rate;
                if (document.getElementById("eqtime")) {
                    document.getElementById("eqtime").value = 0;
                }
            }
        }
    } catch (error) {
        console.error("Error processing individual transmission:", error);
    }
}
