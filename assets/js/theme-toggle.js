(function () {
  var root = document.documentElement;

  function current() {
    var stored = null;
    try { stored = localStorage.getItem('theme'); } catch (e) {}
    return stored === 'light' || stored === 'dark' ? stored : 'system';
  }

  function apply(choice) {
    if (choice === 'system') {
      root.removeAttribute('data-theme');
      try { localStorage.removeItem('theme'); } catch (e) {}
    } else {
      root.setAttribute('data-theme', choice);
      try { localStorage.setItem('theme', choice); } catch (e) {}
    }
    document.querySelectorAll('.theme-toggle__btn').forEach(function (btn) {
      btn.classList.toggle('active', btn.dataset.themeChoice === choice);
    });
  }

  document.querySelectorAll('.theme-toggle__btn').forEach(function (btn) {
    btn.addEventListener('click', function () { apply(btn.dataset.themeChoice); });
  });

  apply(current());
})();
