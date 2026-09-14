(function () {
  'use strict';

  var POLL_INTERVAL = 60000;
  var inFlight = false;

  function formatUpdated(value, failed) {
    if (failed) return 'Не удалось обновить · показаны последние данные';
    var date = value ? new Date(value) : new Date();
    if (Number.isNaN(date.getTime())) date = new Date();
    return 'Обновлено ' + date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  }

  function fetchJSON(url) {
    return fetch(url, {
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    }).then(function (response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    });
  }

  function updateEntity(container, data) {
    if (!data || typeof data !== 'object') throw new Error('Invalid stats payload');
    var total = container.querySelector('[data-stat="total"]');
    var recent = container.querySelector('[data-stat="new_24h"]');
    if (total && typeof data.total === 'number') total.textContent = data.total;
    if (recent && typeof data.new_24h === 'number') recent.textContent = '+' + data.new_24h;
    var updated = container.querySelector('[data-stats-updated]');
    if (updated) updated.textContent = formatUpdated(data.updated_at, false);
  }

  function refreshEntities() {
    var containers = document.querySelectorAll('.entity-stats[data-stats-endpoint]');
    containers.forEach(function (container) {
      if (container.dataset.statsLoading === '1') return;
      container.dataset.statsLoading = '1';
      fetchJSON(container.dataset.statsEndpoint)
        .then(function (data) { updateEntity(container, data); })
        .catch(function () {
          var updated = container.querySelector('[data-stats-updated]');
          if (updated) updated.textContent = formatUpdated(null, true);
        })
        .finally(function () { delete container.dataset.statsLoading; });
    });
  }

  function updateDashboard(root, data) {
    if (!data || !Array.isArray(data.cards) || !data.attention || !data.statuses) {
      throw new Error('Invalid dashboard payload');
    }
    data.cards.forEach(function (card) {
      var node = root.querySelector('[data-card-key="' + CSS.escape(card.key) + '"]');
      if (!node) return;
      var total = node.querySelector('[data-stat="total"]');
      var recent = node.querySelector('[data-stat="new_24h"]');
      if (total && typeof card.total === 'number') total.textContent = card.total;
      if (recent && typeof card.new_24h === 'number') recent.textContent = '+' + card.new_24h + ' за 24 часа';
    });
    Object.keys(data.attention).forEach(function (key) {
      var node = root.querySelector('[data-attention="' + CSS.escape(key) + '"]');
      if (node && typeof data.attention[key] === 'number') node.textContent = data.attention[key];
    });
    Object.keys(data.statuses).forEach(function (group) {
      var groupNode = root.querySelector('[data-status-group="' + CSS.escape(group) + '"]');
      if (!groupNode) return;
      var list = groupNode.querySelector('.ops-status-list');
      if (!list) return;
      var values = Object.keys(data.statuses[group]).map(function (status) {
        return Number(data.statuses[group][status]) || 0;
      });
      var maxValue = Math.max.apply(null, values.concat([1]));
      list.textContent = '';
      Object.keys(data.statuses[group]).forEach(function (status) {
        var count = Number(data.statuses[group][status]) || 0;
        var row = document.createElement('div');
        var label = document.createElement('span');
        var dot = document.createElement('i');
        var track = document.createElement('span');
        var bar = document.createElement('span');
        var value = document.createElement('strong');
        row.className = 'ops-status-row';
        row.dataset.statusKey = status;
        dot.setAttribute('aria-hidden', 'true');
        label.className = 'ops-status-row__label';
        track.className = 'ops-status-row__track';
        bar.className = 'ops-status-row__bar';
        bar.style.setProperty('--status-ratio', Math.max(4, count / maxValue * 100) + '%');
        label.appendChild(dot);
        label.appendChild(document.createTextNode(status));
        track.appendChild(bar);
        value.textContent = count;
        row.appendChild(label);
        row.appendChild(track);
        row.appendChild(value);
        list.appendChild(row);
      });
      if (!list.children.length) {
        var empty = document.createElement('p');
        empty.className = 'ops-empty';
        empty.textContent = 'Нет данных';
        list.appendChild(empty);
      }
    });
    var updated = root.querySelector('[data-dashboard-updated]');
    if (updated) updated.textContent = formatUpdated(data.updated_at, false);
  }

  function refreshDashboard() {
    var root = document.querySelector('[data-dashboard-endpoint]');
    if (!root || inFlight || document.hidden) return;
    inFlight = true;
    fetchJSON(root.dataset.dashboardEndpoint)
      .then(function (data) { updateDashboard(root, data); })
      .catch(function () {
        var updated = root.querySelector('[data-dashboard-updated]');
        if (updated) updated.textContent = formatUpdated(null, true);
      })
      .finally(function () { inFlight = false; });
  }

  function refreshAll() {
    if (document.hidden) return;
    refreshEntities();
    refreshDashboard();
  }

  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) refreshAll();
  });
  window.setInterval(refreshAll, POLL_INTERVAL);
})();
