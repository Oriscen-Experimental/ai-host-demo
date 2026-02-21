// Session view rendering

const AVATAR_COLORS = ['#6366f1','#ec4899','#f59e0b','#22c55e','#06b6d4','#f97316'];

export function renderParticipants(containerId, participants, currentTurnId) {
  const el = document.getElementById(containerId);
  el.innerHTML = '';
  let i = 0;
  for (const [pid, p] of Object.entries(participants)) {
    const div = document.createElement('div');
    div.className = 'participant-item' + (pid === currentTurnId ? ' active' : '');
    const color = AVATAR_COLORS[i % AVATAR_COLORS.length];
    div.innerHTML = `
      <div class="avatar" style="background:${color}">${(p.nickname || '?')[0]}</div>
      <span>${p.nickname}${p.is_host ? ' (房主)' : ''}</span>
      <span class="speak-badge">${p.speak_count || 0}</span>
    `;
    el.appendChild(div);
    i++;
  }
}

export function renderGroups(groups, participants, myId) {
  const display = document.getElementById('groups-display');
  const list = document.getElementById('groups-list');
  list.innerHTML = '';

  groups.forEach((group, i) => {
    const div = document.createElement('div');
    const isMyGroup = group.includes(myId);
    div.className = 'group-item' + (isMyGroup ? ' my-group' : '');
    const names = group.map(pid => {
      const p = participants[pid];
      return p ? p.nickname : pid;
    });
    div.textContent = `组${i+1}: ${names.join(' + ')}`;
    list.appendChild(div);
  });

  display.style.display = 'block';
}

export function addMessage(type, text, speakerName) {
  const feed = document.getElementById('message-feed');
  const div = document.createElement('div');
  div.className = `msg ${type}`;

  if (type === 'user') {
    div.innerHTML = `<div class="msg-name">${speakerName || ''}</div>${escapeHtml(text)}`;
  } else if (type === 'ai') {
    div.textContent = text;
  } else {
    div.textContent = text;
  }

  feed.appendChild(div);
  feed.scrollTop = feed.scrollHeight;
}

export function updateTimer(remaining, totalDuration) {
  const min = Math.floor(remaining / 60);
  const sec = remaining % 60;
  document.getElementById('timer-display').textContent =
    `${String(min).padStart(2,'0')}:${String(sec).padStart(2,'0')}`;

  if (totalDuration > 0) {
    const pct = (remaining / totalDuration) * 100;
    document.getElementById('timer-fill').style.width = `${pct}%`;
  }
}

export function updateTurn(currentId, currentName) {
  const indicator = document.getElementById('turn-indicator');
  if (currentId) {
    document.getElementById('turn-name').textContent = currentName || currentId;
    indicator.style.display = 'block';
  } else {
    indicator.style.display = 'none';
  }
}

export function addOutputCard(senderName, data) {
  const wall = document.getElementById('output-wall');
  const card = document.createElement('div');
  card.className = 'output-card';

  let fields = '';
  if (data.time) fields += `<div class="output-field">时间: ${escapeHtml(data.time)}</div>`;
  if (data.place) fields += `<div class="output-field">地点: ${escapeHtml(data.place)}</div>`;
  if (data.budget) fields += `<div class="output-field">预算: ${escapeHtml(data.budget)}</div>`;
  if (data.companion) fields += `<div class="output-field">同伴: ${escapeHtml(data.companion)}</div>`;
  if (data.invite) fields += `<div class="output-field">邀请: ${escapeHtml(data.invite)}</div>`;
  if (data.request) fields += `<div class="output-field">请求: ${escapeHtml(data.request)}</div>`;
  if (data.response) fields += `<div class="output-field">回应: ${escapeHtml(data.response)}</div>`;

  card.innerHTML = `<div class="output-name">${escapeHtml(senderName)}</div>${fields}`;
  wall.appendChild(card);
}

export function renderCommitments(commitments) {
  const wall = document.getElementById('commitments-wall');
  const list = document.getElementById('commitments-list');
  list.innerHTML = '';

  commitments.forEach(c => {
    const card = document.createElement('div');
    card.className = 'commitment-card';
    card.textContent = `${c.members.join(' + ')} — 一起执行 ${c.plan_owner} 的计划`;
    list.appendChild(card);
  });

  wall.style.display = commitments.length ? 'block' : 'none';
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
