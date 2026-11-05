// Mobile action bar (Call | WhatsApp | Book).
// Kept out of the way while the page's own first button is on screen, so a phone
// never shows the same buttons twice. The hiding class is only added here, so if
// this script fails to run the bar just stays visible.
(function () {
  var bar = document.querySelector('.floating-cta-group');
  if (!bar || !('IntersectionObserver' in window)) return;
  // The first call-to-action of any kind in the page body: a button, or a call,
  // WhatsApp or booking link (the contact page uses big cards, not .btn).
  var sel = 'a.btn, button.btn, a[href^="tel:"], a[href*="wa.me/"], a[href*="book.bettercallwes.co.uk"]';
  var cta = Array.prototype.find.call(document.querySelectorAll(sel), function (el) {
    return !el.closest('header, footer, .floating-cta-group') && el.offsetParent !== null;
  });
  if (!cta) return;
  document.documentElement.classList.add('js-cta-bar');
  new IntersectionObserver(function (entries) {
    bar.classList.toggle('is-visible', !entries[0].isIntersecting);
  }).observe(cta);
})();
