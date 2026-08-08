let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let stream;

const recordBtn = document.getElementById('record-btn');
const statusSpan = document.getElementById('recording-status');
const audioPreview = document.getElementById('audio-preview');

recordBtn.addEventListener('click', async () => {
    if (!isRecording) {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    channelCount: 1,
                    sampleRate: 44100,
                } 
            });
            
            // Use webm — most widely supported
            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            audioChunks = [];
            
            mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };
            
            mediaRecorder.onstop = () => {
                if (audioChunks.length === 0) {
                    alert('No audio recorded. Please try again.');
                    return;
                }
                
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const audioUrl = URL.createObjectURL(audioBlob);
                audioPreview.src = audioUrl;
                audioPreview.style.display = 'block';
                
                const file = new File([audioBlob], 'recording.webm', { type: 'audio/webm' });
                const dt = new DataTransfer();
                dt.items.add(file);
                
                let fileInput = document.querySelector('input[name="audio_file"]');
                if (!fileInput) {
                    fileInput = document.createElement('input');
                    fileInput.type = 'file';
                    fileInput.name = 'audio_file';
                    fileInput.style.display = 'none';
                    document.getElementById('triage-form').appendChild(fileInput);
                }
                fileInput.files = dt.files;
                
                const kb = Math.round(file.size / 1024);
                statusSpan.textContent = '✅ Ready (' + kb + ' KB)';
                statusSpan.style.color = '#28a745';
            };
            
            mediaRecorder.start(500);
            isRecording = true;
            recordBtn.textContent = '⏹️ Stop Recording';
            recordBtn.classList.add('recording');
            statusSpan.textContent = '🔴 Recording... Speak clearly';
            statusSpan.style.color = '#dc3545';
            
        } catch (err) {
            console.error(err);
            alert('Microphone error. Please type symptoms instead.');
        }
    } else {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
        }
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        isRecording = false;
        recordBtn.textContent = '🎤 Start Recording';
        recordBtn.classList.remove('recording');
    }
});