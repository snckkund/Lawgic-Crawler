// ─── Voice Input (preserved from original) ───
function startDictation() {
    const micBtn = document.getElementById('mic-btn');

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = "en-US";

        micBtn.classList.add('recording');
        micBtn.textContent = '⏺ Recording...';
        recognition.start();

        recognition.onresult = function(e) {
            document.getElementById('case').value += " " + e.results[0][0].transcript;
            recognition.stop();
        };

        recognition.onend = function() {
            micBtn.classList.remove('recording');
            micBtn.textContent = '🎤 Speak';
        };

        recognition.onerror = function(e) {
            micBtn.classList.remove('recording');
            micBtn.textContent = '🎤 Speak';
        };
    } else {
        alert("Voice input is supported only in Chrome and Edge browsers.");
    }
}

// ─── File Upload Display ───
function handleFileSelect(input) {
    const fileNameEl = document.getElementById('file-name');
    if (input.files && input.files[0]) {
        fileNameEl.textContent = '📎 ' + input.files[0].name;
        fileNameEl.style.display = 'block';
    } else {
        fileNameEl.textContent = '';
        fileNameEl.style.display = 'none';
    }
}

// ─── Loading State ───
const loadingSteps = [
    { text: 'Analyzing case description...', delay: 0 },
    { text: 'Matching BNS sections...', delay: 1500 },
    { text: 'Generating legal analysis...', delay: 3000 },
    { text: 'Searching similar cases...', delay: 5000 },
    { text: 'Ranking results...', delay: 8000 },
];

function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.add('active');

    const stepsContainer = document.getElementById('loading-steps');
    stepsContainer.innerHTML = '';

    loadingSteps.forEach((step, index) => {
        const stepEl = document.createElement('div');
        stepEl.className = 'loading-step';
        stepEl.innerHTML = `<span class="step-icon">○</span> ${step.text}`;
        stepsContainer.appendChild(stepEl);

        setTimeout(() => {
            if (index > 0) {
                const prevStep = stepsContainer.children[index - 1];
                prevStep.classList.remove('active');
                prevStep.classList.add('done');
                prevStep.querySelector('.step-icon').textContent = '✓';
            }
            stepEl.classList.add('active');
            stepEl.querySelector('.step-icon').textContent = '◉';
        }, step.delay);
    });
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.remove('active');
}

// ─── Form Submission with Loading ───
function handleFormSubmit(form) {
    const textarea = form.querySelector('textarea');
    const fileInput = form.querySelector('input[type="file"]');

    if (textarea.value.trim().length < 5 && (!fileInput.files || fileInput.files.length === 0)) {
        alert('Please provide a case description or upload an image.');
        return false;
    }

    showLoading();
    return true;
}

// ─── Expand/Collapse Case Summaries ───
function toggleCaseSummary(btn) {
    const summary = btn.previousElementSibling;
    if (summary.classList.contains('expanded')) {
        summary.classList.remove('expanded');
        btn.textContent = 'Show more ↓';
    } else {
        summary.classList.add('expanded');
        btn.textContent = 'Show less ↑';
    }
}

// ─── Confidence Score Extraction ───
function parseConfidence(text) {
    const patterns = [
        /Confidence\s*(?:Level)?[:\s]*(\d+)\s*%/i,
        /(\d+)\s*%\s*confidence/i,
        /confidence[:\s]*(\d+)/i,
    ];
    for (const pattern of patterns) {
        const match = text.match(pattern);
        if (match) return parseInt(match[1], 10);
    }
    return -1;
}

// ─── Initialize on DOM load ───
document.addEventListener('DOMContentLoaded', function() {
    const analysisEl = document.querySelector('.analysis-content');
    const confidenceBar = document.getElementById('confidence-fill');

    if (analysisEl && confidenceBar) {
        const confidence = parseConfidence(analysisEl.textContent);
        if (confidence >= 0) {
            confidenceBar.style.width = confidence + '%';
            document.getElementById('confidence-value').textContent = confidence + '%';
        } else {
            const confidenceSection = document.getElementById('confidence-section');
            if (confidenceSection) confidenceSection.style.display = 'none';
        }
    }

    hideLoading();
});
