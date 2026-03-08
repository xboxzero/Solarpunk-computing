// Solarpunk Terminal v2
// Single prompt, everything via commands, WebSocket for real-time

var T = document.getElementById('term');
var I = document.getElementById('input');
var F = document.getElementById('prompt');

var ws = null;
var hist = [];
var hi = -1;
var authToken = localStorage.getItem('sp-token') || '';

function out(text, cls) {
  var el = document.createElement('div');
  el.className = 'line ' + (cls || '');
  el.textContent = text;
  T.appendChild(el);
  while (T.children.length > 500) T.removeChild(T.firstChild);
  T.scrollTop = T.scrollHeight;
}

function wsConnect() {
  var proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(proto + '//' + location.host + '/ws');

  ws.onopen = function() {
    out('connected', 'sys');
  };

  ws.onmessage = function(e) {
    try {
      var d = JSON.parse(e.data);
      switch (d.type) {
        case 'output':
          var lines = d.text.split('\\n');
          for (var i = 0; i < lines.length; i++) {
            if (lines[i]) out(lines[i]);
          }
          break;
        case 'mesh':
          out('[' + d.from + '] ' + d.text, 'mesh');
          break;
        case 'peer':
          break;
        case 'result':
          out('[' + d.from + '] ' + (d.ok ? '' : 'ERR ') + d.output, 'result');
          break;
        case 'agent':
          out(d.text, d.cls || 'agent-think');
          break;
        default:
          out(d.text || JSON.stringify(d), 'info');
      }
    } catch (_) {
      out(e.data, 'info');
    }
  };

  ws.onclose = function() {
    out('disconnected', 'sys');
    setTimeout(wsConnect, 2000);
  };

  ws.onerror = function() { ws.close(); };
}

function exec(cmd) {
  out('> ' + cmd, 'cmd');
  if (!cmd.trim()) return;

  hist.unshift(cmd);
  if (hist.length > 50) hist.pop();
  hi = -1;

  if (cmd === 'clear') { T.innerHTML = ''; return; }
  if (cmd.startsWith('auth ')) {
    authToken = cmd.substring(5).trim();
    localStorage.setItem('sp-token', authToken);
    out('token saved', 'sys');
    return;
  }

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(cmd);
    return;
  }

  var headers = { 'Content-Type': 'text/plain' };
  if (authToken) headers['Authorization'] = 'Bearer ' + authToken;
  fetch('/api/run', { method: 'POST', headers: headers, body: cmd })
    .then(function(r) {
      if (r.status === 401) { out('auth required: auth <token>', 'err'); return null; }
      return r.json();
    })
    .then(function(j) {
      if (!j) return;
      if (j.output) {
        var lines = j.output.split('\\n');
        for (var i = 0; i < lines.length; i++) {
          if (lines[i]) out(lines[i], j.ok ? '' : 'err');
        }
      }
    })
    .catch(function() { out('connection error', 'err'); });
}

F.onsubmit = function(e) {
  e.preventDefault();
  var cmd = I.value;
  I.value = '';
  exec(cmd);
};

I.addEventListener('keydown', function(e) {
  if (e.key === 'ArrowUp') {
    e.preventDefault();
    if (hi < hist.length - 1) { hi++; I.value = hist[hi]; }
  } else if (e.key === 'ArrowDown') {
    e.preventDefault();
    if (hi > 0) { hi--; I.value = hist[hi]; }
    else { hi = -1; I.value = ''; }
  }
});

document.addEventListener('click', function(e) {
  if (e.target === T || e.target === document.body) I.focus();
});

out('solarpunk wearable v0.3.0', 'sys');
out('AES-256-GCM mesh | AI agent | multi-hop routing', 'sys');
out('type help for commands', 'sys');
out('', '');

wsConnect();

setInterval(function() {
  fetch('/api/status').then(function(r) { return r.json(); }).then(function(s) {
    document.title = s.node + ' ' + s.battery + '% ' + s.peers + 'p';
  }).catch(function() {});
}, 10000);
