import { connect, send } from './ws.js';
import { initOnboarding } from './onboarding.js';
import { showCard, hideCard, initPlanForm, initHelpForm, initHelpResponseForm, showVoteCards } from './cards.js';
import { initFeedback } from './feedback.js';
import { renderParticipants, renderGroups, addMessage, updateTimer, updateTurn, addOutputCard, renderCommitments } from './session.js';

// ─── State ───
let myId = null;
let isHost = false;
let currentState = null;
let totalDuration = 0;

// ─── Views ───
function showView(id) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

// ─── Join View ───
document.getElementById('btn-create').addEventListener('click', async () => {
  const nickname = document.getElementById('input-nickname').value.trim();
  if (!nickname) return alert('请输入昵称');

  const res = await fetch('/api/rooms', { method: 'POST' });
  const { code } = await res.json();
  connectAndJoin(code, nickname);
});

document.getElementById('btn-join').addEventListener('click', () => {
  const nickname = document.getElementById('input-nickname').value.trim();
  const code = document.getElementById('input-room-code').value.trim().toUpperCase();
  if (!nickname) return alert('请输入昵称');
  if (!code) return alert('请输入房间号');
  connectAndJoin(code, nickname);
});

function connectAndJoin(code, nickname) {
  connect(code, handleMessage);
  // Wait for connection then send join
  setTimeout(() => {
    send({ type: 'join', nickname });
  }, 500);
}

// ─── Lobby ───
document.getElementById('btn-start').addEventListener('click', () => {
  send({ type: 'start_session' });
});

// ─── Session input ───
document.getElementById('btn-send').addEventListener('click', sendChat);
document.getElementById('chat-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendChat();
});

function sendChat() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;
  send({ type: 'chat', text });
  input.value = '';
}

document.getElementById('btn-pass').addEventListener('click', () => {
  send({ type: 'pass_turn' });
});

document.getElementById('btn-next-turn').addEventListener('click', () => {
  send({ type: 'next_turn' });
});

// ─── Ended ───
document.getElementById('btn-new-session').addEventListener('click', () => {
  location.reload();
});

// ─── Init forms ───
initOnboarding();
initPlanForm();
initHelpForm();
initHelpResponseForm();
initFeedback();

// ─── WebSocket message handler ───
function handleMessage(data) {
  switch (data.type) {
    case 'joined':
      myId = data.participant_id;
      isHost = data.is_host;
      currentState = data.state;
      showLobby(data.state);
      break;

    case 'participant_joined':
      currentState = data.state;
      showLobby(data.state);
      break;

    case 'error':
      alert(data.message);
      break;

    case 'stage_change':
      currentState = data.state;
      handleStageChange(data.state);
      break;

    case 'show_onboarding':
      document.getElementById('onboarding-form').style.display = 'flex';
      break;

    case 'show_card':
      showCard(data.card);
      break;

    case 'show_plan_form':
      document.getElementById('plan-form').style.display = 'flex';
      break;

    case 'show_help_form':
      document.getElementById('help-form').style.display = 'flex';
      break;

    case 'show_feedback':
      document.getElementById('feedback-form').style.display = 'flex';
      break;

    case 'show_vote':
      if (currentState) {
        showVoteCards(data.outputs, currentState.participants, myId);
      }
      break;

    case 'ai_message':
      addMessage('ai', data.message.text);
      break;

    case 'user_message':
      addMessage('user', data.message.text, data.message.speaker_name);
      break;

    case 'timer_update':
      updateTimer(data.remaining, totalDuration);
      break;

    case 'turn_change':
      updateTurn(data.current_id, data.current_name);
      if (currentState) {
        renderParticipants('session-participants', currentState.participants, data.current_id);
      }
      // Show next-turn button for host
      const nextBtn = document.getElementById('btn-next-turn');
      if (isHost && data.current_id) {
        nextBtn.style.display = 'inline-block';
      } else {
        nextBtn.style.display = 'none';
      }
      break;

    case 'group_assign':
      if (currentState) {
        renderGroups(data.groups, currentState.participants, myId);
      }
      break;

    case 'participant_update':
      if (currentState) {
        currentState.participants[data.participant.id] = data.participant;
        renderParticipants('session-participants', currentState.participants);
      }
      break;

    case 'output_update':
      addOutputCard(data.sender_name, data.data);
      if (currentState) {
        if (!currentState.outputs) currentState.outputs = {};
        currentState.outputs[data.sender_id] = data.data;
      }
      break;

    case 'help_assignments':
      handleHelpAssignments(data);
      break;

    case 'help_response_update':
      addOutputCard(data.sender_name + ' (回应)', data.data);
      break;

    case 'vote_update':
      // Could highlight voted cards
      break;

    case 'commitments':
      renderCommitments(data.commitments);
      break;
  }
}

function showLobby(state) {
  showView('view-lobby');
  document.getElementById('lobby-room-code').textContent = state.code;

  const grid = document.getElementById('lobby-participants');
  grid.innerHTML = '';
  const colors = ['#6366f1','#ec4899','#f59e0b','#22c55e','#06b6d4','#f97316'];
  let i = 0;
  for (const [pid, p] of Object.entries(state.participants)) {
    const chip = document.createElement('div');
    chip.className = 'participant-chip';
    const color = colors[i % colors.length];
    chip.innerHTML = `<div class="avatar" style="background:${color}">${(p.nickname||'?')[0]}</div><span>${p.nickname}</span>`;
    grid.appendChild(chip);
    i++;
  }

  if (isHost) {
    document.getElementById('btn-start').style.display = 'inline-block';
    document.getElementById('lobby-hint').textContent = `${Object.keys(state.participants).length} 人已加入 — 点击开始`;
  } else {
    document.getElementById('btn-start').style.display = 'none';
    document.getElementById('lobby-hint').textContent = `${Object.keys(state.participants).length} 人已加入 — 等待房主开始...`;
  }
}

function handleStageChange(state) {
  currentState = state;
  const stage = state.stage;

  if (stage === 'ENDED') {
    showView('view-ended');
    if (state.commitments && state.commitments.length) {
      const el = document.getElementById('ended-commitments');
      el.innerHTML = '<h3>本周承诺</h3>';
      state.commitments.forEach(c => {
        const div = document.createElement('div');
        div.className = 'commitment-card';
        div.textContent = `${c.members.join(' + ')} — 一起执行 ${c.plan_owner} 的计划`;
        el.appendChild(div);
      });
    }
    return;
  }

  showView('view-session');
  document.getElementById('session-room-code').textContent = state.code;
  document.getElementById('stage-name').textContent = state.stage_name;

  // Set total duration for timer bar
  const durationMap = {
    'ONBOARDING': 180, 'S1_CHECKIN': 480, 'S2_MICRO': 720,
    'S3_MAIN_FILL': 240, 'S3_MAIN_REVIEW': 1860,
    'S4_HELP': 300, 'S4_HELP_RESPOND': 300,
    'S5_COMMIT': 300, 'S6_CLOSING': 120,
  };
  totalDuration = durationMap[stage] || 0;
  updateTimer(state.timer_remaining, totalDuration);

  renderParticipants('session-participants', state.participants, state.turn_order?.[state.turn_index]);

  // Hide all forms by default (they get shown by specific messages)
  hideAllForms();

  if (state.current_card) {
    showCard(state.current_card);
  } else {
    hideCard();
  }

  // Restore messages
  if (state.messages) {
    const feed = document.getElementById('message-feed');
    feed.innerHTML = '';
    state.messages.forEach(m => {
      addMessage(m.type, m.text, m.speaker_name);
    });
  }
}

function hideAllForms() {
  ['onboarding-form', 'plan-form', 'help-form', 'help-respond-form', 'vote-panel', 'feedback-form'].forEach(id => {
    document.getElementById(id).style.display = 'none';
  });
}

function handleHelpAssignments(data) {
  // Show the person I need to respond to
  const targetId = data.assignments[myId];
  if (targetId && data.requests[targetId]) {
    const targetName = currentState?.participants?.[targetId]?.nickname || targetId;
    document.getElementById('help-respond-target').innerHTML =
      `<p><strong>${targetName}</strong> 的请求：</p><p>${data.requests[targetId]}</p>`;
    document.getElementById('help-respond-form').style.display = 'flex';
  }
}
