import { send } from './ws.js';

export function initOnboarding() {
  // Range sliders display value
  const energy = document.getElementById('ob-energy');
  const energyVal = document.getElementById('ob-energy-val');
  energy.addEventListener('input', () => { energyVal.textContent = energy.value; });

  document.getElementById('btn-submit-onboarding').addEventListener('click', () => {
    const data = {
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
