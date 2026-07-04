// Interview Logic
const statusBadge = document.getElementById('status-badge');
const subtitle = document.getElementById('ai-subtitle');
const waves = document.getElementById('waves');
const video = document.getElementById('webcam-video');
const btnStart = document.getElementById('btn-start-answer');
const btnStop = document.getElementById('btn-stop-answer');
const transcriptSpan = document.getElementById('live-transcript');
const recordingDot = document.getElementById('recording-dot');

let currentQuestionId = null;
let recognition = null;
let finalTranscript = "";
let mediaRecorder = null;
let recordedChunks = [];
let videoUploadPromise = null;
let videoUploadResolve = null;

// Initialize Web Speech API
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    
    recognition.onresult = (event) => {
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript + ' ';
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }
        transcriptSpan.innerHTML = finalTranscript + '<i style="color:#64748b;">' + interimTranscript + '</i>';
    };
    
    recognition.onerror = (event) => {
        console.error("Speech recognition error", event.error);
    };
} else {
    alert("Speech recognition is not supported in this browser. Please use Google Chrome or Edge.");
}

async function init() {
    try {
        // Request Camera & Mic
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        video.srcObject = stream;
        
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) recordedChunks.push(e.data);
        };
        mediaRecorder.onstop = async () => {
            console.log("Recording stopped. Uploading video...");
            const blob = new Blob(recordedChunks, { type: 'video/webm' });
            const formData = new FormData();
            formData.append('video', blob, `interview_${interviewId}.webm`);
            const token = localStorage.getItem('token');
            try {
                await fetch(`/api/interview/${interviewId}/upload_video`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` },
                    body: formData
                });
                console.log("Video uploaded successfully.");
            } catch(e) {
                console.error("Video upload failed", e);
            }
            if (videoUploadResolve) videoUploadResolve();
        };
        mediaRecorder.start();
        recordingDot.style.display = 'block';

        // Wait a second for camera layout to settle, then start
        setTimeout(() => {
            speak("Hello! Welcome to IntelliHire AI. I have carefully analyzed your resume. Based on your profile, I have prepared a personalized interview. Whenever you are ready, we will begin.", () => {
                fetchNextQuestion();
            });
        }, 1500);

    } catch(e) {
        alert("Camera and Microphone access is required for the interview.");
    }
}

// Text to Speech Function
function speak(text, callback) {
    statusBadge.innerText = "AI is speaking...";
    subtitle.innerText = `"${text}"`;
    waves.style.display = 'block';
    
    const synth = window.speechSynthesis;
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Attempt to use a professional female voice
    const voices = synth.getVoices();
    let voice = voices.find(v => v.name.includes("Google UK English Female") || v.name.includes("Google US English Female"));
    if (!voice) {
        voice = voices.find(v => v.name.includes("Female") || v.name.includes("female"));
    }
    if (voice) utterance.voice = voice;
    
    utterance.onend = () => {
        waves.style.display = 'none';
        if (callback) callback();
    };
    
    synth.speak(utterance);
}

// Fetch Questions
async function fetchNextQuestion() {
    statusBadge.innerText = "Analyzing Resume...";
    subtitle.innerText = "Generating next question...";
    try {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/interview/${interviewId}/next_question`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        
        if (data.question_id) {
            currentQuestionId = data.question_id;
            setTimeout(() => {
                speak(data.text, () => {
                    statusBadge.innerText = "Waiting for your answer...";
                    btnStart.style.display = 'inline-block';
                    btnStop.style.display = 'none';
                    btnStart.disabled = false;
                });
            }, 1000); // Slight pause for realism
        } else {
            // Finished
            finishInterview();
        }
    } catch(e) {
        console.error(e);
    }
}

async function finishInterview() {
    speak("Thank you for your time. The interview is now complete. Your results will be available on your dashboard shortly.", async () => {
        statusBadge.innerText = "Saving Interview...";
        subtitle.innerText = "Please wait while we upload your recording...";
        
        videoUploadPromise = new Promise(resolve => videoUploadResolve = resolve);
        
        if(mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        } else {
            if (videoUploadResolve) videoUploadResolve();
        }
        
        await videoUploadPromise;
        
        const token = localStorage.getItem('token');
        await fetch(`/api/interview/${interviewId}/finish`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        window.location.href = '/dashboard';
    });
}

// Event Listeners for Answer buttons
btnStart.addEventListener('click', () => {
    btnStart.style.display = 'none';
    btnStop.style.display = 'inline-block';
    btnStop.disabled = false;
    statusBadge.innerText = "Listening...";
    
    finalTranscript = "";
    transcriptSpan.innerHTML = "<i>Listening...</i>";
    if(recognition) recognition.start();
});

btnStop.addEventListener('click', async () => {
    if (finalTranscript.trim() === "") {
        alert("We didn't hear anything. Please make sure your microphone is working, or type your answer below.");
        document.getElementById('fallback-container').style.display = 'block';
        if(recognition) {
            try { recognition.stop(); } catch(e) { }
        }
        return; // Prevent submission, wait for fallback
    }
    
    document.getElementById('fallback-container').style.display = 'none';
    btnStop.style.display = 'none';
    btnStart.style.display = 'inline-block';
    btnStart.disabled = true; // disable until next question is spoken
    
    if(recognition) {
        try { recognition.stop(); } catch(e) { console.log(e); }
    }
    
    statusBadge.innerText = "Evaluating response...";
    subtitle.innerText = "Evaluating your answer...";
    
    await submitAnswer(finalTranscript);
});

document.getElementById('btn-submit-text').addEventListener('click', async () => {
    const textVal = document.getElementById('fallback-text').value;
    if(textVal.trim() === "") {
        alert("Please type an answer.");
        return;
    }
    
    document.getElementById('fallback-container').style.display = 'none';
    btnStop.style.display = 'none';
    btnStart.style.display = 'inline-block';
    btnStart.disabled = true;
    
    document.getElementById('fallback-text').value = ""; // clear for next time
    
    statusBadge.innerText = "Evaluating response...";
    subtitle.innerText = "Evaluating your answer...";
    
    await submitAnswer(textVal);
});

async function submitAnswer(answerText) {
    try {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/interview/${interviewId}/submit_answer`, {
            method: 'POST',
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json' 
            },
            body: JSON.stringify({
                question_id: currentQuestionId,
                answer: answerText
            })
        });
        const evaluation = await res.json();
        
        // AI Recruiter feedback
        speak(evaluation.feedback || "Thank you for that explanation.", () => {
            fetchNextQuestion();
        });
        
    } catch(e) {
        console.error(e);
    }
}

// Initialize voices and start
window.speechSynthesis.onvoiceschanged = () => {
    // voices are loaded
};

document.addEventListener('DOMContentLoaded', init);
