class AudioRecorder {
  constructor() {
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.isRecording = false;
    this.setupRecordButton();
  }

  setupRecordButton() {
    const recordButton = document.getElementById('recordButton');
    recordButton.addEventListener('mousedown', () => this.startRecording());
    recordButton.addEventListener('mouseup', () => this.stopRecording());
    recordButton.addEventListener('mouseleave', () => {
      if (this.isRecording) {
        this.stopRecording();
      }
    });
  }

  async startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.mediaRecorder = new MediaRecorder(stream);
      this.audioChunks = [];

      this.mediaRecorder.addEventListener('dataavailable', (event) => {
        this.audioChunks.push(event.data);
      });

      this.mediaRecorder.addEventListener('stop', () => {
        this.processRecording();
      });

      this.mediaRecorder.start();
      this.isRecording = true;
      document.getElementById('recordButton').classList.add('recording');
    } catch (err) {
      console.error('Error accessing microphone:', err);
      alert('Error accessing microphone. Please ensure you have granted microphone permissions.');
    }
  }

  stopRecording() {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
      this.isRecording = false;
      document.getElementById('recordButton').classList.remove('recording');
      this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
  }

  async processRecording() {
    const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('audio', audioBlob);

    try {
      document.getElementById('transcriptionOutput').textContent = 'Processing...';
      const response = await fetch('/api/process_audio', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      if (data.success) {
        document.getElementById('transcriptionOutput').textContent = `Transcribed: "${data.transcription}"`;
        
        sessionStorage.setItem('poemResult', JSON.stringify(data));
        
        setTimeout(() => {
          window.location.href = '/result';
        }, 1500);
      } else {
        document.getElementById('transcriptionOutput').textContent = data.error || 'Error processing audio';
      }
    } catch (error) {
      console.error('Error:', error);
      document.getElementById('transcriptionOutput').textContent = 'Error processing audio. Please try again.';
    }
  }
}

// Initialize the recorder when the page loads
document.addEventListener('DOMContentLoaded', () => {
  new AudioRecorder();
}); 