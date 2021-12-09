function rate(){
    if (document.getElementById('star1').checked) {
        location.href = "/user_rate/5.0";
    }
    else if (document.getElementById('star2').checked) {
        location.href = "/user_rate/4.0";
    }
    else if (document.getElementById('star3').checked) {
        location.href = "/user_rate/3.0";
    }
    else if (document.getElementById('star4').checked) {
        location.href = "/user_rate/2.0";
    }
    else if (document.getElementById('star5').checked) {
        location.href = "/user_rate/1.0";
    }
}