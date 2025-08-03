document.addEventListener('DOMContentLoaded', () => {
  const room = document.createElement('div');
  room.id = 'living-room';
  room.innerHTML = `
    <img src="assets/sofa.svg" id="sofa" class="interactive" alt="sofa">
    <img src="assets/tv.svg" id="tv" class="interactive" data-link="art-gallery.html" alt="tv">
    <img src="assets/lamp.svg" id="lamp" class="interactive" data-link="info.html" alt="lamp">
    <img src="assets/mushroom2.png" id="mushroom-left" class="mushroom" alt="mushroom">
    <img src="assets/mushroom3.png" id="mushroom-right" class="mushroom" alt="mushroom">
    <a id="nav-art" class="nav-box" data-link="art-gallery.html">THE ART</a>
    <a id="nav-shop" class="nav-box" data-link="shop.html">THE SHOP</a>
    <a id="nav-info" class="nav-box" data-link="info.html">THE INFO CENTRE</a>
  `;
  document.body.appendChild(room);

  const interactives = room.querySelectorAll('.interactive, .nav-box');

  interactives.forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      room.classList.add('lights-on');
      el.classList.add('ooze');
      const link = el.getAttribute('data-link');
      if (link) {
        setTimeout(() => {
          window.location.href = link;
        }, 500);
      }
    });
  });
});
