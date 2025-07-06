const noti = document.getElementById('noti');
const notificationDropdown = document.querySelector('.notification-dropdown');

function barraNoti() {
    notificationDropdown.style.display = notificationDropdown.style.display === 'block' ? 'none' : 'block';
}

document.addEventListener('click', function(event) {
    if (!notificationDropdown.contains(event.target) && !noti.contains(event.target)){
        notificationDropdown.style.display = 'none';
    }
});

noti.addEventListener('click', barraNoti);