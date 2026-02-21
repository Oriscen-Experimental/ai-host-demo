import { send } from './ws.js';

export function initFeedback() {
  const awkward = document.getElementById('fb-awkward');
  const awkwardVal = document.getElementById('fb-awkward-val');
  awkward.addEventListener('input', () => { awkwardVal.textContent = awkward.value; });

  const ret = document.getElementById('fb-return');
  const retVal = document.getElementById('fb-return-val');
  ret.addEventListener('input', () => { retVal.textContent = ret.value; });

  document.getElementById('btn-submit-feedback').addEventListener('click', () => {
    const data = {
      awkward: parseInt(awkward.value),
      return_willingness: parseInt(ret.value),
      best_stage: document.getElementById('fb-best').value,
    };
    send({ type: 'submit_feedback', data });
    document.getElementById('feedback-form').style.display = 'none';
  });
}
