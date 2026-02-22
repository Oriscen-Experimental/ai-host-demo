import { send } from './ws.js';

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let stream = null;

export function initVoice() {
  const btn = document.getElementById('btn-voice');
  const status = document.getElementById('voice-status');

  if (!btn) return;

  // 按下开始录音
  btn.addEventListener('mousedown', startRecording);
  btn.addEventListener('touchstart', (e) => {
    e.preventDefault();
    startRecording();
  });

  // 松开停止录音
  btn.addEventListener('mouseup', stopRecording);
  btn.addEventListener('mouseleave', stopRecording);
  btn.addEventListener('touchend', (e) => {
    e.preventDefault();
    stopRecording();
  });

  async function startRecording() {
    if (isRecording) return;

    try {
      // 请求麦克风权限
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // 选择支持的 MIME 类型
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

        // 停止所有音频轨道
        if (stream) {
          stream.getTracks().forEach(track => track.stop());
          stream = null;
        }
      };

      mediaRecorder.start();
      isRecording = true;

      // 更新UI
      btn.classList.add('recording');
      btn.textContent = '录音中...';
      if (status) status.style.display = 'block';

    } catch (error) {
      console.error('麦克风访问失败:', error);
      alert('需要允许麦克风权限才能使用语音功能');
    }
  }

  function stopRecording() {
    if (!isRecording || !mediaRecorder) return;

    mediaRecorder.stop();
    isRecording = false;

    // 恢复UI
    btn.classList.remove('recording');
    btn.textContent = '按住说话';
    if (status) status.style.display = 'none';
  }
}

async function sendAudio(blob, mimeType) {
  // 转换为 base64
  const reader = new FileReader();
  reader.onloadend = () => {
    const base64Audio = reader.result; // 包含 data URL 前缀
    send({
      type: 'voice_message',
      audio: base64Audio,
      mimeType: mimeType.split(';')[0], // 只取主类型
    });
  };
  reader.readAsDataURL(blob);
}

export function handleVoiceTranscription(data) {
  // 可以在这里处理语音转录的回调
  // 目前转录结果会作为普通消息显示
  console.log('[Voice] Transcription received:', data);
}
