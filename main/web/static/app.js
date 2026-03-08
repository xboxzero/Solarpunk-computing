// Solarpunk Wearable - Web IDE Client
// Runs in Safari on iPhone. Communicates via HTTP + WebSocket.

(function() {
  'use strict';

  // --- Tab switching ---
  const tabs = document.querySelectorAll('.tab');
  const panels = document.querySelectorAll('.panel');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(tab.dataset.tab).classList.add('active');
    });
  });

  // --- WebSocket ---
  let ws = null;
  let wsRetry = 0;

  function wsConnect() {
    const host = window.location.hostname || '192.168.4.1';
    ws = new WebSocket('ws://' + host + '/ws');

    ws.onopen = function() {
      wsRetry = 0;
      termPrint('Connected to node\n', 'out');
    };

    ws.onmessage = function(e) {
      const data = e.data;
      // Check if it's a mesh message
      if (data.startsWith('[mesh:')) {
        addChatMessage(data);
      }
      termPrint(data + '\n', 'out');
    };

    ws.onclose = function() {
      termPrint('Disconnected. Reconnecting...\n', 'err');
      wsRetry++;
      setTimeout(wsConnect, Math.min(wsRetry * 1000, 5000));
    };

    ws.onerror = function() {
      ws.close();
    };
  }

  function wsSend(msg) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(msg);
    } else {
      termPrint('Not connected\n', 'err');
    }
  }

  // --- Terminal ---
  const termOutput = document.getElementById('termOutput');
  const termInput = document.getElementById('termInput');
  const cmdHistory = [];
  let historyIdx = -1;

  function termPrint(text, cls) {
    const span = document.createElement('span');
    span.className = cls || 'out';
    span.textContent = text;
    termOutput.appendChild(span);
    termOutput.scrollTop = termOutput.scrollHeight;
  }

  termInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      const cmd = termInput.value.trim();
      if (!cmd) return;

      termPrint('$ ' + cmd + '\n', 'cmd');
      cmdHistory.unshift(cmd);
      historyIdx = -1;
      termInput.value = '';

      // Send via WebSocket for real-time response
      wsSend(cmd);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (historyIdx < cmdHistory.length - 1) {
        historyIdx++;
        termInput.value = cmdHistory[historyIdx];
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIdx > 0) {
        historyIdx--;
        termInput.value = cmdHistory[historyIdx];
      } else {
        historyIdx = -1;
        termInput.value = '';
      }
    }
  });

  // Print welcome message
  termPrint('Solarpunk Wearable Computer\n', 'out');
  termPrint("Type 'help' for commands\n\n", 'out');

  // --- Editor ---
  const codeEditor = document.getElementById('codeEditor');
  const editorOutput = document.getElementById('editorOutput');
  const runBtn = document.getElementById('runBtn');

  // Tab key inserts spaces in editor
  codeEditor.addEventListener('keydown', function(e) {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = this.selectionStart;
      const end = this.selectionEnd;
      this.value = this.value.substring(0, start) + '  ' + this.value.substring(end);
      this.selectionStart = this.selectionEnd = start + 2;
    }
  });

  runBtn.addEventListener('click', function() {
    const code = codeEditor.value;
    if (!code.trim()) return;

    editorOutput.textContent = 'Running...';
    editorOutput.style.color = 'var(--muted)';

    fetch('/api/run', {
      method: 'POST',
      body: code,
    })
    .then(r => r.json())
    .then(data => {
      editorOutput.textContent = data.output || '(no output)';
      editorOutput.style.color = data.ok ? 'var(--accent)' : 'var(--error)';
    })
    .catch(err => {
      editorOutput.textContent = 'Error: ' + err.message;
      editorOutput.style.color = 'var(--error)';
    });
  });

  // --- Mesh ---
  const peerList = document.getElementById('peerList');
  const chatMessages = document.getElementById('chatMessages');
  const chatInput = document.getElementById('chatInput');
  const chatSend = document.getElementById('chatSend');

  function addChatMessage(text) {
    const div = document.createElement('div');
    div.className = 'chat-msg';
    div.textContent = text;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  chatSend.addEventListener('click', function() {
    const msg = chatInput.value.trim();
    if (!msg) return;
    chatInput.value = '';

    fetch('/api/mesh/send', { method: 'POST', body: msg })
      .then(() => addChatMessage('[you] ' + msg))
      .catch(err => addChatMessage('[error] ' + err.message));
  });

  chatInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') chatSend.click();
  });

  function refreshPeers() {
    fetch('/api/mesh/peers')
      .then(r => r.json())
      .then(peers => {
        if (peers.length === 0) {
          peerList.innerHTML = '<p class="muted">No peers found yet</p>';
          document.getElementById('peersIcon').textContent = '0 peers';
          return;
        }

        document.getElementById('peersIcon').textContent = peers.length + ' peer' + (peers.length > 1 ? 's' : '');

        peerList.innerHTML = peers.map(p =>
          '<div class="peer-card">' +
            '<div>' +
              '<div class="peer-name">' + escHtml(p.name) + '</div>' +
              '<div class="peer-meta">' + p.mac + ' | ' + p.rssi + 'dBm | ' + p.hops + ' hop(s)</div>' +
            '</div>' +
            '<span class="peer-battery">' + p.battery + '%</span>' +
          '</div>'
        ).join('');
      })
      .catch(() => {});
  }

  // --- Status ---
  function refreshStatus() {
    fetch('/api/status')
      .then(r => r.json())
      .then(s => {
        const battClass = s.battery > 50 ? 'good' : s.battery > 20 ? 'warn' : 'bad';
        document.getElementById('batteryIcon').textContent = s.battery + '%';

        document.getElementById('statusInfo').innerHTML =
          statCard('Battery', s.battery + '%', battClass) +
          statCard('Solar', s.solar_mv + 'mV', s.solar_mv > 1000 ? 'good' : 'warn') +
          statCard('Peers', s.peers, 'good') +
          statCard('Heap', Math.round(s.free_heap / 1024) + 'KB', s.free_heap > 50000 ? 'good' : 'warn') +
          statCard('Uptime', formatUptime(s.uptime), 'good') +
          statCard('Version', s.version, 'good');
      })
      .catch(() => {});
  }

  function statCard(label, value, cls) {
    return '<div class="stat-card">' +
      '<div class="stat-label">' + label + '</div>' +
      '<div class="stat-value ' + cls + '">' + value + '</div>' +
    '</div>';
  }

  function formatUptime(secs) {
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    return h + 'h ' + m + 'm';
  }

  function escHtml(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  // --- Init ---
  wsConnect();
  refreshStatus();
  refreshPeers();

  // Periodic refresh
  setInterval(refreshStatus, 5000);
  setInterval(refreshPeers, 10000);

})();
