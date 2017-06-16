
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

function dd_get_university_faculties(university_pk) {
  var req = new XMLHttpRequest();
  req.onreadystatechange = function() {
    var response;
    if (req.readyState == 4) {
      if (req.status != 200) {
      } else {
        response = JSON.parse(req.responseText);
        document.getElementById("dd-faculties").innerHTML = response.res;
      }
    }
  }
  req.open('POST', '/_university_faculties/');
  req.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  var post_vars = 'university_pk=' + String(university_pk);
  req.send(post_vars);
  return false;
}

function dd_add_new_education() {
  var forma = document.getElementById("dd-edit-education-form");
  var req = new XMLHttpRequest();
  req.onreadystatechange = function() {
    var response;
    if (req.readyState == 4) {
      if (req.status != 200) {
      } else {
        response = JSON.parse(req.responseText);
        document.getElementById("dd-result").innerHTML = response.res;
      }
    }
  }
  req.open('POST', '/_submit_add_education/');
  req.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  try {
    console.log(forma.dd_faculty_input.value);
    var values = {
      university_pk: forma.dd_university_input.value,
      faculty_pk: forma.dd_faculty_input.value
    }
    var post_vars = 'values='+JSON.stringify(values);
    req.send(post_vars);
  } catch(e) {
    if (e instanceof TypeError) {
      document.getElementById("dd-result").innerHTML = "You need to specify faculty.";
    }
  }
  return false;
}
