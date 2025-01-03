var btype = "STANDARD"
$(document).ready(function() {
    $('input[name="optradio"]').on('change', function () {
        if ($(this).val() === "standardbln") {
            var codeBlock = "<div class = \"input\">\n" +
                "                Ascent rate: <input id=\"asc\" type=\"text\" size=\"4\" name=\"asc\"> m/s <br/>\n" +
                "                </div>\n" +
                "                <div class = \"input\">\n" +
                "                Burst altitude: <input id=\"equil\" type=\"text\" size=\"5\" name=\"equil\"> m <br/>\n" +
                "                </div>\n" +
                "                <div class = \"input\">\n" +
                "                Descent rate: <input id=\"desc\" type=\"text\" size=\"4\" name=\"desc\"> m/s <br/>\n" +
                "                </div>"
            document.getElementById("contentwrap").innerHTML = codeBlock;
            document.getElementById("asc").value = 4;
            document.getElementById("equil").value = 30000;
            document.getElementById("desc").value = 8;
            btype = "STANDARD";
            document.getElementById("eqtimebtn").style.visibility = "visible";
        }
        else if ($(this).val() === "zpbbln") {
            var codeBlock = "<div class = \"input\">\n" +
                "                Ascent rate: <input id=\"asc\" type=\"text\" size=\"4\" name=\"asc\"> m/s <br/>\n" +
                "                </div>\n" +
                "                <div class = \"input\">\n" +
                "                Equilibrium altitude: <input id=\"equil\" type=\"text\" size=\"5\" name=\"equil\"> m <br/>\n" +
                "                </div>\n" + "<div class = \"input\">\n" +
                "                Time at Equilibrium: <input id=\"eqtime\" type=\"text\" size=\"4\" name=\"eqtime\"> h <br/>\n" +
                "                </div>\n" +
                "                <div class = \"input\">\n" +
                "                Descent rate: <input id=\"desc\" type=\"text\" size=\"4\" name=\"desc\"> m/s <br/>\n" +
                "                </div>"
            document.getElementById("contentwrap").innerHTML = codeBlock;
            document.getElementById("asc").value = 3.7;
            document.getElementById("equil").value = 29000;
            document.getElementById("eqtime").value = 1;
            document.getElementById("desc").value = 15;
            btype = "ZPB";
            document.getElementById("eqtimebtn").style.visibility = "visible";
        }
        else if ($(this).val() === "floatbln") {
            var codeBlock = "<div class = \"input\">\n" +
                "                Floating Coefficient: <input id=\"coeff\" type=\"text\" size=\"4\" name=\"coeff\"> <br/>\n" +
                "                </div>\n" +
                "                <div class = \"input\">\n" +
                "                Simulate for: <input id=\"dur\" type=\"text\" size=\"4\" name=\"dur\"> h <br/>\n" +
                "                </div>\n" +
                "                <div class = \"input\">\n" +
                "                Step Size: <input id=\"step\" type=\"text\" size=\"4\" name=\"step\"> m/s <br/>\n" +
                "                </div>"
            document.getElementById("contentwrap").innerHTML = codeBlock;
            document.getElementById("coeff").value = 0.5;
            document.getElementById("dur").value = 48;
            document.getElementById("step").value = 240;
            btype = "FLOAT";
            document.getElementById("eqtimebtn").style.visibility = "hidden";
            document.getElementById("timeremain").style.visibility = "hidden";
        }
    });

    // Initialize waypoints toggle
    var waypointsToggle = true;
    $('#toggle-event').change(function() {
        waypointsToggle = $(this).prop('checked');
        if (!waypointsToggle) {
            clearWaypoints();
        } else {
            showWaypoints();
        }
    });

    // Fetch current GEFS run time and status
    fetch(URL_ROOT + "/which")
        .then(res => res.text())
        .then((result) => {
            document.getElementById("run").textContent = result;
        })
        .catch(error => {
            console.error('Error fetching GEFS run time:', error);
            document.getElementById("run").textContent = "Error fetching run time";
        });

    fetch(URL_ROOT + "/status")
        .then(res => res.text())
        .then((result) => {
            document.getElementById("status").textContent = result;
            if (result === "Ready") {
                document.getElementById("status").style.color = "#00CC00";
            } else if (result === "Data refreshing. Sims may be slower than usual.") {
                document.getElementById("status").style.color = "#FFB900";
            } else {
                document.getElementById("status").style.color = "#CC0000";
            }
        })
        .catch(error => {
            console.error('Error fetching status:', error);
            document.getElementById("status").textContent = "Error fetching status";
            document.getElementById("status").style.color = "#CC0000";
        });

    // Set initial balloon parameters (important for standard mode which doesn't trigger change event)
    document.getElementById("asc").value = 4;
    document.getElementById("equil").value = 30000;
    document.getElementById("desc").value = 8;

    setMissions();
});

// Active missions configuration
let activeMissions = {
    'SSI-95': 68,
    'SSI-94': 69,
    'SSI-96': 70,
    'SSI-93': 67,
    'SSI-92': 66
};

let ssilist = Object.keys(activeMissions);
let CURRENT_MISSION = ssilist[0];

function setMissions() {
    document.getElementById("activeMission").innerText = ssilist[0];
    $('.dropdown-menu').empty();  // Clear existing missions first
    
    for (let mission of ssilist) {
        var newmiss = document.createElement("a");
        newmiss.className = "dropdown-item";
        newmiss.text = mission;
        newmiss.value = mission;
        newmiss.setAttribute('onClick', `setActiveMission('${mission}')`);
        $('.dropdown-menu').append(newmiss);
    }
}

function setActiveMission(msn) {
    if (activeMissions.hasOwnProperty(msn)) {
        CURRENT_MISSION = msn;
        document.getElementById("activeMission").innerText = CURRENT_MISSION;
    } else {
        console.error("Invalid mission selected:", msn);
    }
}
