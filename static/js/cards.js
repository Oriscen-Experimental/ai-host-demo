import { send } from './ws.js';

export function showCard(card) {
  const banner = document.getElementById('card-banner');
  document.getElementById('card-title').textContent = card.title;
  document.getElementById('card-goal').textContent = card.goal;
  const steps = document.getElementById('card-steps');
  steps.innerHTML = '';
  card.steps.forEach(s => {
    const li = document.createElement('li');
    li.textContent = s;
    steps.appendChild(li);
  });
  banner.style.display = 'block';
}

export function hideCard() {
  document.getElementById('card-banner').style.display = 'none';
}

export function initPlanForm() {
  document.getElementById('btn-submit-plan').addEventListener('click', () => {
    const data = {
      time: document.getElementById('plan-time').value,
      place: document.getElementById('plan-place').value,
      budget: document.getElementById('plan-budget').value,
      companion: document.getElementById('plan-companion').value,
      invite: document.getElementById('plan-invite').value,
    };
    send({ type: 'submit_output', data });
    document.getElementById('plan-form').style.display = 'none';
  });
}

export function initHelpForm() {
  document.getElementById('btn-submit-help').addEventListener('click', () => {
    const request = document.getElementById('help-request-text').value.trim();
    if (!request) return;
    send({ type: 'submit_output', data: { request } });
    document.getElementById('help-form').style.display = 'none';
  });
}

export function initHelpResponseForm() {
  document.getElementById('btn-submit-help-response').addEventListener('click', () => {
    const response = document.getElementById('help-response-text').value.trim();
    if (!response) return;
    send({ type: 'submit_help_response', data: { response } });
    document.getElementById('help-respond-form').style.display = 'none';
  });
}

export function showVoteCards(outputs, participants, myId) {
  const panel = document.getElementById('vote-panel');
  const container = document.getElementById('vote-cards');
  container.innerHTML = '';

  for (const [pid, data] of Object.entries(outputs)) {
    if (pid === myId) continue; // don't vote for yourself
    const p = participants[pid];
    const card = document.createElement('div');
    card.className = 'vote-card';
    card.dataset.pid = pid;
    card.innerHTML = `
      <div class="output-name">${p ? p.nickname : pid}</div>
      <div class="output-field">Time: ${data.time || '-'}</div>
      <div class="output-field">Location: ${data.place || '-'}</div>
      <div class="output-field">Budget: ${data.budget || '-'}</div>
      <div class="output-field">Companion: ${data.companion || '-'}</div>
      <div class="output-field">Invitation: ${data.invite || '-'}</div>
    `;
    card.addEventListener('click', () => {
      container.querySelectorAll('.vote-card').forEach(c => c.classList.remove('voted'));
      card.classList.add('voted');
      send({ type: 'vote', target_id: pid });
    });
    container.appendChild(card);
  }
  panel.style.display = 'block';
}
