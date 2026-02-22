import { send } from './ws.js';

export function initOnboarding() {
  // Range sliders display value
  const energy = document.getElementById('ob-energy');
  const energyVal = document.getElementById('ob-energy-val');
  energy.addEventListener('input', () => { energyVal.textContent = energy.value; });

  document.getElementById('btn-submit-onboarding').addEventListener('click', () => {
    const data = {
      // New fields
      age: document.getElementById('ob-age').value,
      gender: document.getElementById('ob-gender').value,
      goal: document.getElementById('ob-goal').value,
      interest: document.getElementById('ob-interest').value,
      intro: document.getElementById('ob-intro')?.value || '',
      // Original fields
      energy: parseInt(energy.value),
      shy: document.getElementById('ob-shy').value,
      prefer: document.getElementById('ob-prefer').value,
      support: document.getElementById('ob-support').value,
      lang: document.getElementById('ob-lang').value,
      action: document.getElementById('ob-action').value,
    };
    send({ type: 'submit_onboarding', data });
    document.getElementById('onboarding-form').style.display = 'none';
  });
}
