
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
    // console.log(tab_content);
    for (var i = 0; i < tab_content.length; i++) {
        tab_content[i].style.display = "none";
    }
    document.getElementById(tab_name).style.display = "block";
}
