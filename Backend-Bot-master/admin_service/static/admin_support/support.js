(function() {
  'use strict';

  function supportLink() {
    return document.querySelector('.navbar a[href="/admin/support/"],.main-header a[href="/admin/support/"]');
  }

  function updateBadge() {
    if (document.hidden) return;
    fetch('/admin/support/unread-count/', {
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
      .then(function(response) {
        if (!response.ok) throw new Error();
        return response.json();
      })
      .then(function(data) {
        var link = supportLink();
        if (!link) return;
        var badge = link.querySelector('.support-unread-badge');
        if (data.unread_messages > 0) {
          if (!badge) {
            badge = document.createElement('span');
            badge.className = 'support-unread-badge';
            link.appendChild(badge);
          }
          badge.textContent = data.unread_messages > 99 ? '99+' : data.unread_messages;
          badge.title = data.unread_conversations + ' непрочитанных диалогов';
          badge.setAttribute('aria-label', badge.title);
        } else if (badge) {
          badge.remove();
        }
      })
      .catch(function() {});
  }

  function scrollToBottom(behavior) {
    var container = document.getElementById('support-messages');
    if (!container) return;
    container.scrollTo({
      top: container.scrollHeight,
      behavior: behavior || 'auto',
    });
  }

  function autoResizeTextarea(textarea) {
    if (!textarea) return;
    textarea.addEventListener('input', function() {
      this.style.height = 'auto';
      this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
  }

  function handleReplyKeydown(textarea) {
    if (!textarea) return;
    textarea.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.form.submit();
      }
    });
  }

  function handleSearch(input, form) {
    if (!input || !form) return;
    var timeout;
    input.addEventListener('input', function() {
      clearTimeout(timeout);
      timeout = setTimeout(function() {
        form.submit();
      }, 500);
    });
  }

  function initWorkspace() {
    scrollToBottom('auto');

    var autoReadForm = document.getElementById('support-auto-read');
    if (autoReadForm) {
      autoReadForm.submit();
    }

    autoResizeTextarea(document.getElementById('support-reply'));
    handleReplyKeydown(document.getElementById('support-reply'));
    handleSearch(document.getElementById('support-q'), document.getElementById('support-search-form'));
  }

  document.addEventListener('visibilitychange', function() {
    if (!document.hidden) updateBadge();
  });

  document.addEventListener('DOMContentLoaded', function() {
    updateBadge();
    initWorkspace();
    window.setInterval(updateBadge, 15000);
  });
})();