(function () {
  'use strict';

  var BASE = 'https://ieekjkeayiclprdekxla.supabase.co/rest/v1';
  var KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImllZWtqa2VheWljbHByZGVreGxhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ4MzAxODQsImV4cCI6MjA5MDQwNjE4NH0.dAcUXetSteRXcUytAnkd3CEp_z6fg2nqhC3lrWoNPl0';
  var POLL_MS = 60000;
  var CACHE_PREFIX = 'lb_status_';

  var hdrs = {
    'apikey': KEY,
    'Authorization': 'Bearer ' + KEY
  };

  var lastSnapshotAt = null;
  var pollTimer = null;
  var goalMap = {};
  var taskCache = {};

  // --- Helpers ---

  function $(id) { return document.getElementById(id); }

  function escapeHtml(str) {
    if (!str) return '';
    var d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }

  function relativeTime(iso) {
    if (!iso) return '';
    var diff = (Date.now() - new Date(iso).getTime()) / 1000;
    if (diff < 0) return 'just now';
    if (diff < 60) return 'just now';
    if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
    if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
    return Math.floor(diff / 86400) + 'd ago';
  }

  function truncateToSentence(text, max) {
    if (!text) return '';
    if (text.length <= max) return text;
    var end = text.lastIndexOf('.', max);
    if (end < max * 0.5) end = max;
    return text.slice(0, end + 1);
  }

  // --- Cache ---

  function cacheSet(section, data) {
    try {
      localStorage.setItem(CACHE_PREFIX + section, JSON.stringify({
        data: data,
        fetched_at: new Date().toISOString()
      }));
    } catch (e) {
      try {
        localStorage.removeItem(CACHE_PREFIX + 'log');
        localStorage.setItem(CACHE_PREFIX + section, JSON.stringify({
          data: data,
          fetched_at: new Date().toISOString()
        }));
      } catch (e2) { /* give up */ }
    }
  }

  function cacheGet(section) {
    try {
      var raw = localStorage.getItem(CACHE_PREFIX + section);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch (e) { return null; }
  }

  // --- API ---

  function apiFetch(path) {
    return fetch(BASE + path, { headers: hdrs }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }

  function fetchSnapshot() {
    return apiFetch(
      '/snapshots?select=content,cycle_count,current_focus,active_goals,recent_outcomes,key_learnings,created_at&order=created_at.desc&limit=1'
    );
  }

  function fetchGoals() {
    return apiFetch(
      '/goals?status=in.(in_progress,pending)&select=id,title,description,status,priority,created_at,created_by&order=priority.asc,created_at.asc'
    );
  }

  function fetchLog() {
    return apiFetch(
      '/execution_log?select=action,summary,created_at,duration_ms,goal_id&order=created_at.desc&limit=20'
    );
  }

  function fetchLearnings() {
    return apiFetch(
      '/learnings?select=category,content,confidence,times_validated,created_at,goal_id&order=created_at.desc&limit=10'
    );
  }

  function fetchTasks(goalId) {
    return apiFetch(
      '/tasks?goal_id=eq.' + goalId +
      '&select=id,title,status,sort_order,attempts,max_attempts,blocked_reason,completed_at&order=sort_order.asc'
    );
  }

  // --- Render: Snapshot ---

  function renderSnapshot(data) {
    var snap = (data && data.length) ? data[0] : null;
    var cycleEl = $('status-cycle');
    var headlineEl = $('status-headline');
    var fullContentEl = $('status-full-content');
    var fullLogEl = $('status-full-log');
    var focusEl = $('status-focus');

    if (!snap) {
      cycleEl.textContent = 'Cycle #0';
      headlineEl.textContent = "Agent hasn't run yet";
      focusEl.textContent = 'Waiting for first cycle.';
      fullLogEl.hidden = true;
      return null;
    }

    cycleEl.textContent = 'Cycle #' + snap.cycle_count + ' \u00B7 updated ' + relativeTime(snap.created_at);

    var content = snap.content || '';
    var first = truncateToSentence(content, 220);
    headlineEl.textContent = first;

    if (content.length > 220) {
      fullLogEl.hidden = false;
      fullContentEl.textContent = content;
    } else {
      fullLogEl.hidden = true;
    }

    focusEl.textContent = snap.current_focus || '';
    lastSnapshotAt = snap.created_at;
    return snap;
  }

  // --- Render: Goals ---

  function renderGoals(goals, snapshotGoals) {
    var grid = $('status-goals-grid');

    if (!goals || !goals.length) {
      grid.innerHTML = '<p class="status-empty">No active goals right now \u2014 agent is between cycles.</p>';
      return;
    }

    var progressMap = {};
    if (snapshotGoals) {
      var sg = typeof snapshotGoals === 'string' ? JSON.parse(snapshotGoals) : snapshotGoals;
      sg.forEach(function (g) { progressMap[g.id] = g.progress_pct || 0; });
    }

    goalMap = {};
    goals.forEach(function (g) { goalMap[g.id] = g.title; });

    var html = '';
    goals.forEach(function (g) {
      var pct = progressMap[g.id] || 0;
      html +=
        '<div class="goal-card">' +
          '<span class="status-badge" data-status="' + escapeHtml(g.status) + '">' +
            escapeHtml(g.status.replace(/_/g, ' ')) +
          '</span>' +
          '<h3>' + escapeHtml(g.title) + '</h3>' +
          '<p class="goal-desc">' + escapeHtml(g.description || '') + '</p>' +
          '<div class="progress-bar"><div class="progress-bar__fill" style="width:' + pct + '%"></div></div>' +
          '<span class="progress-label">' + pct + '%</span>' +
          '<details data-goal-id="' + g.id + '">' +
            '<summary>Tasks</summary>' +
            '<div class="task-list-container"><p class="status-empty">Loading\u2026</p></div>' +
          '</details>' +
        '</div>';
    });
    grid.innerHTML = html;

    grid.querySelectorAll('details[data-goal-id]').forEach(function (det) {
      det.addEventListener('toggle', function () {
        if (!det.open) return;
        var gid = det.getAttribute('data-goal-id');
        if (taskCache[gid]) {
          renderTaskList(det, taskCache[gid]);
          return;
        }
        fetchTasks(gid).then(function (tasks) {
          taskCache[gid] = tasks;
          renderTaskList(det, tasks);
        }).catch(function () {
          var container = det.querySelector('.task-list-container');
          container.innerHTML =
            '<div class="status-error" role="status">Couldn\u2019t load tasks. <button type="button">Retry</button></div>';
          container.querySelector('button').addEventListener('click', function () {
            container.innerHTML = '<p class="status-empty">Loading\u2026</p>';
            fetchTasks(gid).then(function (tasks) {
              taskCache[gid] = tasks;
              renderTaskList(det, tasks);
            }).catch(function () {
              container.innerHTML = '<div class="status-error" role="status">Still unavailable.</div>';
            });
          });
        });
      });
    });
  }

  function renderTaskList(detailsEl, tasks) {
    var container = detailsEl.querySelector('.task-list-container');
    if (!tasks || !tasks.length) {
      container.innerHTML = '<p class="status-empty">No tasks yet.</p>';
      return;
    }
    var icons = { done: '\u2713', in_progress: '\u25B6', pending: '\u25CB', blocked: '\u2717' };
    var html = '<ul class="task-list">';
    tasks.forEach(function (t) {
      html +=
        '<li>' +
          '<span class="task-status-icon" data-status="' + escapeHtml(t.status) + '">' +
            (icons[t.status] || '\u25CB') +
          '</span> ' +
          escapeHtml(t.title) +
        '</li>';
    });
    html += '</ul>';
    container.innerHTML = html;
  }

  // --- Render: Execution Log ---

  function renderLog(entries) {
    var list = $('feed-list');

    if (!entries || !entries.length) {
      list.innerHTML = '<p class="status-empty">No recent activity yet.</p>';
      return;
    }

    var html = '';
    entries.forEach(function (e) {
      var goalRefHtml = '';
      if (e.goal_id && goalMap[e.goal_id]) {
        goalRefHtml = '<span class="goal-ref">' + escapeHtml(goalMap[e.goal_id]) + '</span>';
      }
      html +=
        '<div class="feed-item">' +
          '<span class="feed-item__time">' + relativeTime(e.created_at) + '</span>' +
          '<span class="action-pill" data-action="' + escapeHtml(e.action) + '">' +
            escapeHtml(e.action) +
          '</span>' +
          '<span class="feed-item__summary">' + escapeHtml(e.summary) + '</span>' +
          goalRefHtml +
        '</div>';
    });
    list.innerHTML = html;
  }

  // --- Render: Learnings ---

  function renderLearnings(learnings) {
    var grid = $('learnings-grid');

    if (!learnings || !learnings.length) {
      grid.innerHTML = '<p class="status-empty">No learnings yet.</p>';
      return;
    }

    var html = '';
    learnings.forEach(function (l) {
      var conf = Math.round((l.confidence || 0) * 100);
      var validated = l.times_validated > 0 ? ' \u00B7 validated ' + l.times_validated + 'x' : '';
      html +=
        '<div class="learning-card">' +
          '<span class="category-badge" data-category="' + escapeHtml(l.category) + '">' +
            escapeHtml((l.category || '').replace(/_/g, ' ')) +
          '</span>' +
          '<p class="learning-content">' + escapeHtml(l.content) + '</p>' +
          '<div class="confidence-bar"><div class="confidence-bar__fill" style="width:' + conf + '%"></div></div>' +
          '<span class="learning-meta">' + conf + '% confidence' + validated + '</span>' +
        '</div>';
    });
    grid.innerHTML = html;
  }

  // --- Section error ---

  function renderSectionError(containerId, sectionName, retryFn) {
    var el = $(containerId);
    if (!el) return;
    el.innerHTML =
      '<div class="status-error" role="status">Couldn\u2019t load ' +
      escapeHtml(sectionName) + '. <button type="button">Retry</button></div>';
    el.querySelector('button').addEventListener('click', retryFn);
  }

  // --- Cache render ---

  function renderFromCache() {
    var snapCached = cacheGet('snapshot');
    var goalsCached = cacheGet('goals');
    var logCached = cacheGet('log');
    var learningsCached = cacheGet('learnings');
    var snap = null;

    if (snapCached) {
      snap = renderSnapshot(snapCached.data);
      $('status-hero').classList.add('stale');
    }
    if (goalsCached) {
      renderGoals(goalsCached.data, snap ? snap.active_goals : null);
      $('status-goals-section').classList.add('stale');
    }
    if (logCached) {
      renderLog(logCached.data);
      $('status-feed-section').classList.add('stale');
    }
    if (learningsCached) {
      renderLearnings(learningsCached.data);
      $('status-learnings-section').classList.add('stale');
    }
  }

  function clearStale() {
    ['status-hero', 'status-goals-section', 'status-feed-section', 'status-learnings-section']
      .forEach(function (id) { $(id).classList.remove('stale'); });
  }

  // --- Fetch all ---

  function fetchAll() {
    var banner = $('status-banner');
    var refreshBtn = $('refresh-btn');
    refreshBtn.classList.add('loading');

    return Promise.all([
      fetchSnapshot().catch(function () { return null; }),
      fetchGoals().catch(function () { return null; }),
      fetchLog().catch(function () { return null; }),
      fetchLearnings().catch(function () { return null; })
    ]).then(function (results) {
      var snapshotData = results[0];
      var goalsData = results[1];
      var logData = results[2];
      var learningsData = results[3];

      var allFailed = !snapshotData && !goalsData && !logData && !learningsData;

      if (allFailed) {
        var cachedSnap = cacheGet('snapshot');
        if (cachedSnap) {
          banner.hidden = false;
          banner.textContent =
            'Live data is unavailable right now. Showing cached state from ' +
            relativeTime(cachedSnap.fetched_at) + '.';
        } else {
          banner.hidden = false;
          banner.textContent = 'Live data is unavailable right now.';
        }
        refreshBtn.classList.remove('loading');
        return;
      }

      banner.hidden = true;
      clearStale();

      var snap = null;
      if (snapshotData) {
        snap = renderSnapshot(snapshotData);
        cacheSet('snapshot', snapshotData);
      } else {
        renderSectionError('status-hero', 'snapshot', function () {
          fetchSnapshot().then(function (d) { renderSnapshot(d); cacheSet('snapshot', d); });
        });
      }

      if (goalsData) {
        renderGoals(goalsData, snap ? snap.active_goals : null);
        cacheSet('goals', goalsData);
      } else {
        renderSectionError('status-goals-grid', 'goals', function () {
          fetchGoals().then(function (d) { renderGoals(d, snap ? snap.active_goals : null); cacheSet('goals', d); });
        });
      }

      if (logData) {
        renderLog(logData);
        cacheSet('log', logData);
      } else {
        renderSectionError('feed-list', 'activity', function () {
          fetchLog().then(function (d) { renderLog(d); cacheSet('log', d); });
        });
      }

      if (learningsData) {
        renderLearnings(learningsData);
        cacheSet('learnings', learningsData);
      } else {
        renderSectionError('learnings-grid', 'learnings', function () {
          fetchLearnings().then(function (d) { renderLearnings(d); cacheSet('learnings', d); });
        });
      }

      refreshBtn.classList.remove('loading');
    }).catch(function () {
      refreshBtn.classList.remove('loading');
    });
  }

  // --- Polling ---

  function startPolling() {
    stopPolling();
    pollTimer = setInterval(fetchAll, POLL_MS);
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  // --- Init ---

  document.addEventListener('DOMContentLoaded', function () {
    renderFromCache();

    $('refresh-btn').addEventListener('click', function () {
      taskCache = {};
      fetchAll();
    });

    var toggle = document.querySelector('.nav-toggle');
    var links = document.querySelector('.nav-links');
    if (toggle && links) {
      toggle.addEventListener('click', function () {
        links.classList.toggle('active');
      });
    }

    fetchAll().then(function () {
      startPolling();
    });

    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'visible') {
        fetchAll();
        startPolling();
      } else {
        stopPolling();
      }
    });
  });
})();
