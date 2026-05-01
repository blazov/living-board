(function () {
  'use strict';

  var BASE = 'https://ieekjkeayiclprdekxla.supabase.co/rest/v1';
  var KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImllZWtqa2VheWljbHByZGVreGxhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ4MzAxODQsImV4cCI6MjA5MDQwNjE4NH0.dAcUXetSteRXcUytAnkd3CEp_z6fg2nqhC3lrWoNPl0';

  var hdrs = { 'apikey': KEY, 'Authorization': 'Bearer ' + KEY };

  function $(id) { return document.getElementById(id); }

  function escapeHtml(str) {
    if (!str) return '';
    var d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }

  function apiFetch(path) {
    return fetch(BASE + path, { headers: hdrs }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }

  function renderStats(goals, tasks, learnings, snapshot, logEntries) {
    var cycleCount = snapshot ? snapshot.cycle_count : logEntries.length;
    var firstDate = logEntries.length ? new Date(logEntries[logEntries.length - 1].created_at) : null;
    var days = firstDate ? Math.ceil((Date.now() - firstDate.getTime()) / 86400000) : 0;
    var goalsDone = goals.filter(function (g) { return g.status === 'done'; }).length;
    var tasksDone = tasks.filter(function (t) { return t.status === 'done'; }).length;
    var tasksTotal = tasks.length;
    var rate = tasksTotal > 0 ? Math.round((tasksDone / tasksTotal) * 100) : 0;

    $('stat-cycles').textContent = cycleCount;
    $('stat-days').textContent = days;
    $('stat-goals').textContent = goalsDone + '/' + goals.length;
    $('stat-tasks').textContent = tasksDone;
    $('stat-learnings').textContent = learnings.length;
    $('stat-rate').textContent = rate + '%';
  }

  function renderActivityChart(logEntries) {
    var dayMap = {};
    logEntries.forEach(function (e) {
      var day = e.created_at.slice(0, 10);
      dayMap[day] = (dayMap[day] || 0) + 1;
    });

    if (!logEntries.length) {
      $('activity-chart').innerHTML = '<p class="status-empty">No activity data.</p>';
      return;
    }

    var firstDay = new Date(logEntries[logEntries.length - 1].created_at.slice(0, 10));
    var lastDay = new Date(logEntries[0].created_at.slice(0, 10));
    var days = [];
    var d = new Date(firstDay);
    while (d <= lastDay) {
      days.push(d.toISOString().slice(0, 10));
      d.setDate(d.getDate() + 1);
    }

    var maxCount = 0;
    days.forEach(function (day) {
      var c = dayMap[day] || 0;
      if (c > maxCount) maxCount = c;
    });

    var html = '<div class="activity-bars">';
    days.forEach(function (day) {
      var count = dayMap[day] || 0;
      var pct = maxCount > 0 ? (count / maxCount) * 100 : 0;
      var label = day.slice(5);
      html +=
        '<div class="activity-bar-col" title="' + day + ': ' + count + ' actions">' +
          '<div class="activity-bar" style="height:' + pct + '%">' +
            (count > 0 ? '<span class="activity-bar__count">' + count + '</span>' : '') +
          '</div>' +
          '<span class="activity-bar__label">' + label + '</span>' +
        '</div>';
    });
    html += '</div>';
    $('activity-chart').innerHTML = html;
  }

  function renderBreakdown(containerId, statusCounts, total) {
    var colors = {
      done: '#4dd4ae',
      in_progress: '#6c8aff',
      pending: '#9498a8',
      blocked: '#e06a6a'
    };
    var labels = {
      done: 'Done',
      in_progress: 'In Progress',
      pending: 'Pending',
      blocked: 'Blocked'
    };

    var barHtml = '<div class="stacked-bar">';
    var legendHtml = '<div class="breakdown-legend">';
    var order = ['done', 'in_progress', 'pending', 'blocked'];

    order.forEach(function (status) {
      var count = statusCounts[status] || 0;
      if (count === 0) return;
      var pct = total > 0 ? (count / total) * 100 : 0;
      barHtml +=
        '<div class="stacked-bar__segment" style="width:' + pct + '%;background:' + colors[status] + '" title="' + labels[status] + ': ' + count + '"></div>';
      legendHtml +=
        '<span class="legend-item">' +
          '<span class="legend-dot" style="background:' + colors[status] + '"></span>' +
          labels[status] + ': ' + count + ' (' + Math.round(pct) + '%)' +
        '</span>';
    });

    barHtml += '</div>';
    legendHtml += '</div>';
    $(containerId).innerHTML = barHtml + legendHtml;
  }

  function renderCategoryChart(learnings) {
    var catMap = {};
    learnings.forEach(function (l) {
      var cat = l.category || 'other';
      catMap[cat] = (catMap[cat] || 0) + 1;
    });

    var cats = Object.keys(catMap).sort(function (a, b) { return catMap[b] - catMap[a]; });
    var maxCount = cats.length ? catMap[cats[0]] : 0;

    var catColors = {
      operational: '#4dd4ae',
      meta: '#c48cff',
      strategy: '#ffb454',
      domain_knowledge: '#6c8aff',
      content_strategy: '#ff6b9d',
      market_intelligence: '#54d4ff',
      platform_knowledge: '#8da4ff',
      api_mechanics: '#4dd4ae',
      other: '#9498a8'
    };

    var html = '';
    cats.forEach(function (cat) {
      var count = catMap[cat];
      var pct = maxCount > 0 ? (count / maxCount) * 100 : 0;
      var color = catColors[cat] || '#9498a8';
      var label = cat.replace(/_/g, ' ');
      html +=
        '<div class="cat-row">' +
          '<span class="cat-row__label">' + escapeHtml(label) + '</span>' +
          '<div class="cat-row__bar-wrap">' +
            '<div class="cat-row__bar" style="width:' + pct + '%;background:' + color + '"></div>' +
          '</div>' +
          '<span class="cat-row__count">' + count + '</span>' +
        '</div>';
    });

    $('category-chart').innerHTML = html || '<p class="status-empty">No learnings data.</p>';
  }

  function renderConfidenceDistribution(learnings) {
    var buckets = [
      { label: '90-100%', min: 0.9, max: 1.01, count: 0 },
      { label: '80-89%', min: 0.8, max: 0.9, count: 0 },
      { label: '70-79%', min: 0.7, max: 0.8, count: 0 },
      { label: '60-69%', min: 0.6, max: 0.7, count: 0 },
      { label: '< 60%', min: 0, max: 0.6, count: 0 }
    ];

    learnings.forEach(function (l) {
      var c = l.confidence || 0;
      for (var i = 0; i < buckets.length; i++) {
        if (c >= buckets[i].min && c < buckets[i].max) {
          buckets[i].count++;
          break;
        }
      }
    });

    var maxCount = 0;
    buckets.forEach(function (b) { if (b.count > maxCount) maxCount = b.count; });

    var html = '';
    buckets.forEach(function (b) {
      var pct = maxCount > 0 ? (b.count / maxCount) * 100 : 0;
      html +=
        '<div class="cat-row">' +
          '<span class="cat-row__label">' + b.label + '</span>' +
          '<div class="cat-row__bar-wrap">' +
            '<div class="cat-row__bar" style="width:' + pct + '%;background:var(--accent)"></div>' +
          '</div>' +
          '<span class="cat-row__count">' + b.count + '</span>' +
        '</div>';
    });

    $('confidence-dist-chart').innerHTML = html || '<p class="status-empty">No data.</p>';
  }

  function fetchAll() {
    return Promise.all([
      apiFetch('/goals?select=id,title,status,priority,created_at').catch(function () { return []; }),
      apiFetch('/tasks?select=id,status,goal_id,completed_at,created_at').catch(function () { return []; }),
      apiFetch('/execution_log?select=action,created_at&order=created_at.asc').catch(function () { return []; }),
      apiFetch('/learnings?select=category,confidence,created_at').catch(function () { return []; }),
      apiFetch('/snapshots?select=cycle_count,created_at&order=created_at.desc&limit=1').catch(function () { return []; })
    ]).then(function (results) {
      var goals = results[0];
      var tasks = results[1];
      var logEntries = results[2];
      var learnings = results[3];
      var snapshot = results[4] && results[4].length ? results[4][0] : null;

      renderStats(goals, tasks, learnings, snapshot, logEntries);
      renderActivityChart(logEntries);

      var goalStatusCounts = {};
      goals.forEach(function (g) { goalStatusCounts[g.status] = (goalStatusCounts[g.status] || 0) + 1; });
      renderBreakdown('goals-breakdown', goalStatusCounts, goals.length);

      var taskStatusCounts = {};
      tasks.forEach(function (t) { taskStatusCounts[t.status] = (taskStatusCounts[t.status] || 0) + 1; });
      renderBreakdown('tasks-breakdown', taskStatusCounts, tasks.length);

      renderCategoryChart(learnings);
      renderConfidenceDistribution(learnings);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var toggle = document.querySelector('.nav-toggle');
    var links = document.querySelector('.nav-links');
    if (toggle && links) {
      toggle.addEventListener('click', function () {
        links.classList.toggle('active');
      });
    }

    fetchAll();
  });
})();
