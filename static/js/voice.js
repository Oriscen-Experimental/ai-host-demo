import { send } from './ws.js';

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let stream = null;

export function initVoice() {
  const btn = document.getElementById('btn-voice');
  const status = document.getElementById('voice-status');

  if (!btn) return;

  // Press to start recording
  btn.addEventListener('mousedown', startRecording);
  btn.addEventListener('touchstart', (e) => {
    e.preventDefault();
    startRecording();
  });

  // Release to stop recording
  btn.addEventListener('mouseup', stopRecording);
  btn.addEventListener('mouseleave', stopRecording);
  btn.addEventListener('touchend', (e) => {
    e.preventDefault();
    stopRecording();
  });

  async function startRecording() {
    if (isRecording) return;

    try {
      // Request microphone permission
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Choose supported MIME type
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';

      mediaRecorder = new MediaRecorder(stream, { mimeType });
      audioChunks = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: mimeType });
        audioChunks = [];
        await sendAudio(audioBlob, mimeType);

        // Stop all audio tracks
        if (stream) {
          stream.getTracks().forEach(track => track.stop());
          stream = null;
        }
      };

      mediaRecorder.start();
      isRecording = true;

      // Update UI
      btn.classList.add('recording');
      btn.textContent = 'Recording...';
      if (status) status.style.display = 'block';

    } catch (error) {
      console.error('Microphone access failed:', error);
      alert('Microphone permission required for voice function');
    }
  }

  function stopRecording() {
    if (!isRecording || !mediaRecorder) return;

    mediaRecorder.stop();
    isRecording = false;

    // Restore UI
    btn.classList.remove('recording');
    btn.textContent = 'Hold to speak';
    if (status) status.style.display = 'none';
  }
}

async function sendAudio(blob, mimeType) {
  // Convert to base64
  const reader = new FileReader();
  reader.onloadend = () => {
    const base64Audio = reader.result; // Includes data URL prefix
    send({
      type: 'voice_message',
      audio: base64Audio,
      mimeType: mimeType.split(';')[0], // Only take main type
    });
  };
  reader.readAsDataURL(blob);
}

export function handleVoiceTranscription(data) {
  // Handle voice transcription callback here
  // Currently transcription result is displayed as regular message
  console.log('[Voice] Transcription received:', data);
}
