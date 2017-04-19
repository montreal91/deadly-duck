
const ACTIVE_CLASS_NAME = "active";


function dd_select_tab(evt, tab_name) {
    // Make clicked nav active
    var ul_fiend_nav = document.getElementById("dd-friends-nav");
    var nav_positions = ul_fiend_nav.children;
    for (var i = 0; i < nav_positions.length; i++) {
        nav_positions[i].classList.remove(ACTIVE_CLASS_NAME);
    }
    evt.currentTarget.parentElement.classList.add(ACTIVE_CLASS_NAME);

    var tab_content = document.getElementsByClassName("dd-tab-content");
    for (var i = 0; i < tab_content.length; i++) {
        tab_content[i].style.display = "none";
    }
    document.getElementById(tab_name).style.display = "block";
}

function send_ajax_request() {
    // console.log($SCRIPT_ROOT);
    // forma = document.getElementById("my_form");
    var req = new XMLHttpRequest();
    req.onreadystatechange = function() {
        if (req.readyState == 4) {
            if (req.status != 200) {
            } else {
                var response = JSON.parse(req.responseText);
                document.getElementById("dd-result").innerHTML = response.result;
                // document.getElementById("clicks").innerHTML = response.clicks;
                return false;
            }
        }
    }
    req.open('POST', '/_foo/');
    req.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    // var un = forma.my_text.value;
    var post_vars = 'text='+'lol';
    req.send(post_vars);
    return false;
}
