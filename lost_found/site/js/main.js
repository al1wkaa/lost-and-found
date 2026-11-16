// Lost & Found — минимальный интерактив без библиотек
(function () {
  'use strict';

  // Показ/скрытие пароля (иконка глаза)
  document.querySelectorAll('.pass-field__eye').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var input = document.getElementById(btn.dataset.eye);
      if (!input) return;
      var show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.setAttribute('aria-label', show ? 'Скрыть пароль' : 'Показать пароль');
      btn.setAttribute('aria-pressed', show ? 'true' : 'false');
    });
  });

  // Чипы-фильтры: переключение активного состояния
  document.querySelectorAll('.chips').forEach(function (group) {
    group.addEventListener('click', function (e) {
      var chip = e.target.closest('.chip');
      if (!chip) return;
      group.querySelectorAll('.chip').forEach(function (c) {
        var active = c === chip;
        c.classList.toggle('chip--active', active);
        c.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
    });
  });

  // Переключатель типа объявления на странице подачи
  var toggleGroup = document.querySelector('.submit-card__toggle');
  if (toggleGroup) {
    toggleGroup.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-toggle]');
      if (!btn) return;
      toggleGroup.querySelectorAll('[data-toggle]').forEach(function (b) {
        var active = b === btn;
        b.classList.toggle('btn--primary', active);
        b.classList.toggle('btn--secondary', !active);
        b.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
    });
  }

  // Поле даты: показывает календарь при фокусе
  document.querySelectorAll('[data-date-input]').forEach(function (input) {
    input.addEventListener('focus', function () { input.type = 'date'; });
    input.addEventListener('blur', function () {
      if (!input.value) input.type = 'text';
    });
  });

  // «Прочитать все» — снимает отметку непрочитанных уведомлений
  var markAll = document.getElementById('mark-all-read');
  if (markAll) {
    markAll.addEventListener('click', function () {
      document.querySelectorAll('.notif--unread').forEach(function (n) {
        n.classList.remove('notif--unread');
      });
    });
  }

  // Кнопки «Скопировать» на странице контактов
  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var input = document.getElementById(btn.dataset.copy);
      if (!input) return;
      var done = function () {
        var old = btn.textContent;
        btn.textContent = 'Скопировано';
        setTimeout(function () { btn.textContent = old; }, 1500);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(input.value).then(done);
      } else {
        input.select();
        document.execCommand('copy');
        done();
      }
    });
  });

  // Проверка обязательных полей: подсветка и aria-invalid
  document.querySelectorAll('form').forEach(function (form) {
    var fields = form.querySelectorAll('[required]');

    var clearError = function (input) {
      input.style.borderColor = '';
      input.removeAttribute('aria-invalid');
    };

    fields.forEach(function (input) {
      var evt = input.type === 'checkbox' ? 'change' : 'input';
      input.addEventListener(evt, function () { clearError(input); });
    });

    form.addEventListener('submit', function (e) {
      var ok = true;
      fields.forEach(function (input) {
        var empty = input.type === 'checkbox' ? !input.checked : !input.value.trim();
        if (!empty) {
          clearError(input);
          return;
        }
        input.style.borderColor = 'var(--red)';
        input.setAttribute('aria-invalid', 'true');
        ok = false;
      });
      if (!ok) e.preventDefault();
    });
  });
})();