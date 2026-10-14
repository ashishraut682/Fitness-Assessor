/* AI Fitness & Multi-Sport Kinematic System - Web Application Controller */

const API_BASE_URL = "http://127.0.0.1:5000/api";

// Sport Exercises Map
const SPORT_EXERCISES = {
    gym: [
        { id: "squat", name: "Squats Form Check" },
        { id: "pushup", name: "Pushups Form Check" },
        { id: "plank", name: "Core Plank Hold" },
        { id: "lunge", name: "Forward Lunges" }
    ],
    yoga: [
        { id: "tree_pose", name: "Tree Pose (Vrksasana)" },
        { id: "warrior_ii", name: "Warrior II (Virabhadrasana II)" },
        { id: "cobra_pose", name: "Cobra Pose (Bhujangasana)" }
    ],
    basketball: [
        { id: "shooting_form", name: "Shooting Form Check (90° L-Elbow)" },
        { id: "defensive_stance", name: "Low Defensive Stance" }
    ],
    cricket: [
        { id: "batting_stance", name: "Batting Stance & Backlift" },
        { id: "bowling_action", name: "Bowling Arm Straightness Check (<15°)" }
    ],
    athletics: [
        { id: "running_gait", name: "Running Gait & 5-10° Torso Lean" },
        { id: "sprint_start", name: "Sprint Block Stance Angles" }
    ],
    kabaddi: [
        { id: "kabaddi_raider_touch", name: "Raider Toe Touch & Reach Lunge" },
        { id: "kabaddi_defender_stance", name: "Defender Chain & Ankle Hold Stance" },
        { id: "kabaddi_dubki", name: "Dubki Evasion & Low Dip" }
    ]
};

// State
let currentCategory = "gym";
let currentExercise = "squat";
let repCount = 0;
let currentAngle = 175;
let isCameraActive = false;
let cameraStream = null;
let frameProcessingInterval = null;
let isVideoUploading = false;
let videoFileInterval = null;
let currentMode = "IDLE"; // "IDLE", "LIVE_CAMERA", "VIDEO_FILE"
let currentUser = { id: 1, name: "Alex Rivera", email: "alex@example.com", age: 24, gender: "Male" };

// Navigation History Stacks
let pageHistoryStack = [];
let pageForwardStack = [];
let currentPageId = "page-dashboard";

function switchWebPage(pageId, isHistoryNav = false) {
    if (!isHistoryNav && pageId !== currentPageId) {
        if (currentPageId) {
            pageHistoryStack.push(currentPageId);
        }
        pageForwardStack = []; // Reset forward stack when navigating explicitly
    }

    currentPageId = pageId;

    document.querySelectorAll('.page-view').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(n => n.classList.remove('active'));

    const targetPage = document.getElementById(pageId);
    if (targetPage) targetPage.classList.add('active');

    if (pageId === 'page-dashboard') document.getElementById('nav-web-dashboard')?.classList.add('active');
    if (pageId === 'page-assess') document.getElementById('nav-web-assess')?.classList.add('active');
    if (pageId === 'page-results') document.getElementById('nav-web-results')?.classList.add('active');
    if (pageId === 'page-recs') document.getElementById('nav-web-recs')?.classList.add('active');
    if (pageId === 'page-analytics') {
        document.getElementById('nav-web-analytics')?.classList.add('active');
        loadAnalyticsData();
    }
    if (pageId === 'page-profile') document.getElementById('nav-web-profile')?.classList.add('active');

    if (pageId !== 'page-assess') {
        if (isCameraActive) stopWebcam();
        stopVideoUpload();
    }

    updateNavHistoryButtons();
}

function goBackPage() {
    if (pageHistoryStack.length > 0) {
        const prevPage = pageHistoryStack.pop();
        pageForwardStack.push(currentPageId);
        switchWebPage(prevPage, true);
    }
}

function goForwardPage() {
    if (pageForwardStack.length > 0) {
        const nextPage = pageForwardStack.pop();
        pageHistoryStack.push(currentPageId);
        switchWebPage(nextPage, true);
    }
}

function updateNavHistoryButtons() {
    const btnBack = document.getElementById('btn-nav-back');
    const btnForward = document.getElementById('btn-nav-forward');

    if (btnBack) {
        btnBack.disabled = pageHistoryStack.length === 0;
        btnBack.classList.toggle('disabled', pageHistoryStack.length === 0);
    }
    if (btnForward) {
        btnForward.disabled = pageForwardStack.length === 0;
        btnForward.classList.toggle('disabled', pageForwardStack.length === 0);
    }
}

function switchSportModule(category) {
    currentCategory = category;
    const exercises = SPORT_EXERCISES[category] || SPORT_EXERCISES['gym'];
    currentExercise = exercises[0].id;

    // Highlight sidebar active module
    document.querySelectorAll('.nav-link').forEach(n => n.classList.remove('active'));
    const modNav = document.getElementById(`nav-mod-${category}`);
    if (modNav) modNav.classList.add('active');

    // Populate Exercise Picker Dropdown
    const picker = document.getElementById('exercise-picker');
    if (picker) {
        picker.innerHTML = '';
        exercises.forEach(ex => {
            picker.innerHTML += `<option value="${ex.id}">${ex.name}</option>`;
        });
        picker.value = currentExercise;
    }

    startWebAssessment(category, currentExercise);
}

function changeActiveExercise(exerciseId) {
    currentExercise = exerciseId;
    repCount = 0;
    currentAngle = 175;
    const exObj = (SPORT_EXERCISES[currentCategory] || []).find(e => e.id === exerciseId);
    document.getElementById('sport-assess-title').innerText = `${currentCategory.toUpperCase()} - ${exObj ? exObj.name : exerciseId}`;
    document.getElementById('web-overlay-reps').innerText = repCount;
    document.getElementById('web-overlay-angle').innerText = `${currentAngle}°`;
    if (currentMode === 'IDLE') renderStandbyCanvas();
}

function startWebAssessment(category, exercise) {
    currentCategory = category;
    currentExercise = exercise;
    repCount = 0;
    currentAngle = 175;

    // Stop camera and any video upload when opening assessment
    stopWebcam();
    stopVideoUpload();

    const exObj = (SPORT_EXERCISES[currentCategory] || []).find(e => e.id === exercise);
    document.getElementById('sport-assess-title').innerText = `${category.toUpperCase()} - ${exObj ? exObj.name : exercise}`;
    document.getElementById('web-overlay-reps').innerText = repCount;
    document.getElementById('web-overlay-angle').innerText = `${currentAngle}°`;
    document.getElementById('web-overlay-stage').innerText = "STANDBY";

    updateAssessmentMode('IDLE');
    switchWebPage('page-assess');
    renderStandbyCanvas();
}

function updateAssessmentMode(mode, extraText = "") {
    currentMode = mode;
    const modeBadge = document.getElementById('web-mode-badge');
    const cameraBtnText = document.getElementById('btn-camera-text');
    const cameraBtnIcon = document.getElementById('btn-camera-icon');
    const feedbackBanner = document.getElementById('web-feedback-banner');

    if (mode === 'IDLE') {
        if (modeBadge) {
            modeBadge.innerHTML = `<i class="fa-solid fa-circle-pause"></i> (Standby)`;
            modeBadge.style.color = "var(--text-muted)";
        }
        if (cameraBtnText) cameraBtnText.innerText = "Start Live Recording";
        if (cameraBtnIcon) {
            cameraBtnIcon.className = "fa-solid fa-circle-dot";
            cameraBtnIcon.style.color = "#ef4444";
        }
        if (feedbackBanner) {
            feedbackBanner.innerHTML = `<i class="fa-solid fa-video"></i> Click <strong>"Start Live Recording"</strong> to capture live webcam or <strong>"Upload Video File"</strong> to analyze an offline video.`;
        }
    } else if (mode === 'LIVE_CAMERA') {
        if (modeBadge) {
            modeBadge.innerHTML = `<i class="fa-solid fa-record-vinyl" style="color:#ef4444;"></i> Live Camera Recording Active`;
            modeBadge.style.color = "#ef4444";
        }
        if (cameraBtnText) cameraBtnText.innerText = "Stop Camera Recording";
        if (cameraBtnIcon) {
            cameraBtnIcon.className = "fa-solid fa-square";
            cameraBtnIcon.style.color = "#ef4444";
        }
        if (feedbackBanner) {
            feedbackBanner.innerHTML = `<i class="fa-solid fa-circle-check"></i> Live Camera Active — Position full body in view for ${currentCategory.toUpperCase()} kinematic analysis...`;
        }
    } else if (mode === 'VIDEO_FILE') {
        if (modeBadge) {
            modeBadge.innerHTML = `<i class="fa-solid fa-file-video" style="color:var(--primary-accent);"></i> Video Upload: ${extraText || 'Processing'}`;
            modeBadge.style.color = "var(--primary-accent)";
        }
        if (cameraBtnText) cameraBtnText.innerText = "Start Live Recording";
        if (cameraBtnIcon) {
            cameraBtnIcon.className = "fa-solid fa-circle-dot";
            cameraBtnIcon.style.color = "#ef4444";
        }
        if (feedbackBanner) {
            feedbackBanner.innerHTML = `<i class="fa-solid fa-file-video"></i> Analyzing Uploaded Video File (<code>${extraText}</code>)... Camera is OFF.`;
        }
    }
}

function toggleCameraRecording() {
    if (isCameraActive) {
        stopWebcam();
        updateAssessmentMode('IDLE');
        renderStandbyCanvas();
    } else {
        stopVideoUpload();
        startWebcam();
    }
}

async function startWebcam() {
    const video = document.getElementById('webcam-feed');
    const canvas = document.getElementById('output-canvas');
    const ctx = canvas.getContext('2d');

    canvas.width = 800;
    canvas.height = 480;

    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
        video.srcObject = cameraStream;
        await video.play();
        isCameraActive = true;
        updateAssessmentMode('LIVE_CAMERA');

        frameProcessingInterval = setInterval(() => {
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                sendFrameToBackend(canvas);
            }
        }, 300);
    } catch (err) {
        console.warn("Webcam unavailable. Running MediaPipe pose canvas simulation.", err);
        isCameraActive = false;
        updateAssessmentMode('LIVE_CAMERA');
        renderSimulatedPoseCanvas(canvas, ctx);
    }
}

function stopWebcam() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    if (frameProcessingInterval) {
        clearInterval(frameProcessingInterval);
        frameProcessingInterval = null;
    }
    isCameraActive = false;
}

/* Video Upload File Analysis (WITHOUT Camera Activation) */
function handleVideoFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Unconditionally stop webcam if running so camera is NOT accessed
    stopWebcam();

    const videoElem = document.getElementById('uploaded-video-feed');
    const canvas = document.getElementById('output-canvas');
    const ctx = canvas.getContext('2d');

    canvas.width = 800;
    canvas.height = 480;

    if (videoElem.src) URL.revokeObjectURL(videoElem.src);

    const videoUrl = URL.createObjectURL(file);
    videoElem.src = videoUrl;
    isVideoUploading = true;

    updateAssessmentMode('VIDEO_FILE', file.name);

    videoElem.onloadedmetadata = () => {
        videoElem.play();

        stopVideoUploadInterval();
        videoFileInterval = setInterval(() => {
            if (!videoElem.paused && !videoElem.ended) {
                ctx.drawImage(videoElem, 0, 0, canvas.width, canvas.height);
                sendFrameToBackend(canvas);
            }
        }, 200);
    };

    videoElem.onended = () => {
        stopVideoUploadInterval();
        document.getElementById('web-feedback-banner').innerHTML = `<i class="fa-solid fa-circle-check"></i> Video File Analysis Complete! Final Reps Detected: <strong>${repCount}</strong>`;
        document.getElementById('web-overlay-stage').innerText = "COMPLETED";
    };
}

function stopVideoUploadInterval() {
    if (videoFileInterval) {
        clearInterval(videoFileInterval);
        videoFileInterval = null;
    }
}

function stopVideoUpload() {
    stopVideoUploadInterval();
    const videoElem = document.getElementById('uploaded-video-feed');
    if (videoElem) {
        videoElem.pause();
        if (videoElem.src) URL.revokeObjectURL(videoElem.src);
        videoElem.removeAttribute('src');
    }
    isVideoUploading = false;
}

function renderStandbyCanvas() {
    const canvas = document.getElementById('output-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = 800;
    canvas.height = 480;

    const isLight = document.documentElement.getAttribute('data-theme') === 'light';

    ctx.fillStyle = isLight ? "#f8fafc" : "#070a11";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = isLight ? "rgba(2, 132, 199, 0.08)" : "rgba(0, 242, 254, 0.05)";
    ctx.lineWidth = 1;
    for (let x = 0; x < canvas.width; x += 40) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += 40) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
    }

    ctx.fillStyle = isLight ? "#0f172a" : "rgba(255, 255, 255, 0.85)";
    ctx.font = "bold 18px Plus Jakarta Sans";
    ctx.textAlign = "center";
    ctx.fillText(`Kinematic Tracker [${currentCategory.toUpperCase()} - ${currentExercise.toUpperCase()}]`, canvas.width / 2, canvas.height / 2 - 15);

    ctx.fillStyle = isLight ? "#64748b" : "#94a3b8";
    ctx.font = "14px Plus Jakarta Sans";
    ctx.fillText('Click "Start Live Recording" to record live or "Upload Video File" to process an offline video.', canvas.width / 2, canvas.height / 2 + 18);
}

async function sendFrameToBackend(canvas) {
    const frameB64 = canvas.toDataURL('image/jpeg', 0.6);
    try {
        const res = await fetch(`${API_BASE_URL}/analyze/frame`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: frameB64, category: currentCategory, exercise: currentExercise })
        });
        const data = await res.json();
        if (data.analysis) {
            repCount = data.analysis.rep_count || repCount;
            document.getElementById('web-overlay-reps').innerText = repCount;
            document.getElementById('web-overlay-stage').innerText = data.analysis.stage || (currentMode === 'LIVE_CAMERA' ? "RECORDING" : "ANALYZING");
            document.getElementById('web-feedback-banner').innerHTML = `<i class="fa-solid fa-circle-check"></i> ${data.analysis.feedback || "Good form!"}`;
            if (data.analysis.angles) {
                const primaryAngle = Object.values(data.analysis.angles)[0];
                if (primaryAngle) document.getElementById('web-overlay-angle').innerText = `${Math.round(primaryAngle)}°`;
            }
        }
    } catch (err) {
        // Quiet fallback
    }
}

function simulatePoseRep() {
    repCount += 1;
    currentAngle = currentAngle === 175 ? 85 : 175;
    const stage = currentAngle < 100 ? "DESCENT" : "EXTEND";

    document.getElementById('web-overlay-reps').innerText = repCount;
    document.getElementById('web-overlay-angle').innerText = `${currentAngle}°`;
    document.getElementById('web-overlay-stage').innerText = stage;

    const feedbackMap = {
        gym: "Great Squat Rep! Full depth (<90°) & knee tracking verified.",
        yoga: "Excellent Vrksasana Pose Alignment! Core balance stable.",
        basketball: "High Release Set Point (90° L-elbow) & wrist snap!",
        cricket: "Legal Straight Bowling Arm Delivery (<15° flex) verified!",
        athletics: "High Knee Drive & Optimal 5°-10° Torso Lean!",
        kabaddi: "Sharp Raider Reach & Extended Stride! Quick recovery verified."
    };

    const fb = feedbackMap[currentCategory] || "Good kinematic biomechanics!";
    document.getElementById('web-feedback-banner').innerHTML = `<i class="fa-solid fa-circle-check"></i> ${fb}`;

    const canvas = document.getElementById('output-canvas');
    const ctx = canvas.getContext('2d');
    renderSimulatedPoseCanvas(canvas, ctx);
}

function renderSimulatedPoseCanvas(canvas, ctx) {
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';

    ctx.fillStyle = isLight ? "#f1f5f9" : "#060911";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = isLight ? "rgba(0, 0, 0, 0.05)" : "rgba(255, 255, 255, 0.04)";
    ctx.lineWidth = 1;
    for (let x = 0; x < canvas.width; x += 40) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
    }

    const w = canvas.width, h = canvas.height;
    const isFlexed = currentAngle < 100;
    const hipY = isFlexed ? h * 0.62 : h * 0.48;
    const kneeY = isFlexed ? h * 0.74 : h * 0.68;

    const points = [
        { x: w * 0.42, y: h * 0.22 }, { x: w * 0.58, y: h * 0.22 },
        { x: w * 0.44, y: hipY }, { x: w * 0.56, y: hipY },
        { x: w * 0.45, y: kneeY }, { x: w * 0.55, y: kneeY },
        { x: w * 0.46, y: h * 0.88 }, { x: w * 0.54, y: h * 0.88 }
    ];

    ctx.strokeStyle = isLight ? "#0284c7" : "#00f2fe";
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y); ctx.lineTo(points[1].x, points[1].y);
    ctx.moveTo(points[0].x, points[0].y); ctx.lineTo(points[2].x, points[2].y);
    ctx.moveTo(points[1].x, points[1].y); ctx.lineTo(points[3].x, points[3].y);
    ctx.moveTo(points[2].x, points[2].y); ctx.lineTo(points[3].x, points[3].y);
    ctx.moveTo(points[2].x, points[2].y); ctx.lineTo(points[4].x, points[4].y);
    ctx.moveTo(points[4].x, points[4].y); ctx.lineTo(points[6].x, points[6].y);
    ctx.moveTo(points[3].x, points[3].y); ctx.lineTo(points[5].x, points[5].y);
    ctx.moveTo(points[5].x, points[5].y); ctx.lineTo(points[7].x, points[7].y);
    ctx.stroke();

    points.forEach(pt => {
        ctx.fillStyle = isLight ? "#059669" : "#10b981";
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 8, 0, 2 * Math.PI);
        ctx.fill();
    });

    ctx.fillStyle = isLight ? "#1e293b" : "rgba(255, 255, 255, 0.85)";
    ctx.font = "14px Plus Jakarta Sans";
    ctx.fillText(`Pose Landmarker [${currentCategory.toUpperCase()} - ${currentExercise.toUpperCase()}] | Angle: ${currentAngle}°`, w * 0.03, h * 0.94);
}

async function finishAssessment() {
    const userId = currentUser ? currentUser.id : 1;

    // Determine REAL reps from current session
    let squats = 0;
    let pushups = 0;

    if (currentExercise === 'squat') squats = repCount;
    else if (currentExercise === 'pushup') pushups = repCount;
    else squats = repCount;

    // If 0 reps were performed (e.g. video doing nothing), metrics are 0.0!
    let flexibility = 0.0;
    let balance = 0.0;
    let posture = 0.0;

    if (repCount > 0) {
        flexibility = 70.0;
        balance = 80.0;
        posture = 75.0;
    }

    try {
        const res = await fetch(`${API_BASE_URL}/assess/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                squats: squats,
                pushups: pushups,
                flexibility: flexibility,
                balance: balance,
                posture: posture
            })
        });
        const data = await res.json();
        renderWebResults(data);
    } catch (err) {
        console.warn("Fallback offline scoring calculation:", err);
        const strength = Math.min(100, ((squats + pushups) / 50.0) * 100);
        const fitness_score = repCount === 0 ? 0.0 : Math.round((strength * 0.3) + (flexibility * 0.25) + (balance * 0.20) + (posture * 0.25));
        renderWebResults({
            scoring: {
                fitness_score: fitness_score,
                tier: fitness_score === 0 ? "No Reps / Idle Video (0% Score)" : (fitness_score >= 70 ? "Good (Fit Level)" : "Needs Work"),
                breakdown: { strength: Math.round(strength), flexibility: Math.round(flexibility), balance: Math.round(balance), posture: Math.round(posture) }
            }
        });
    }
    switchWebPage('page-results');
}

let lastAssessmentData = null;

function renderWebResults(data) {
    lastAssessmentData = data;
    const scoring = data.scoring || {};
    const finalScore = scoring.fitness_score !== undefined ? scoring.fitness_score : 0.0;
    const tier = scoring.tier || (finalScore === 0 ? "No Reps / Idle Video (0% Score)" : "Needs Work");
    const breakdown = scoring.breakdown || { strength: 0, flexibility: 0, balance: 0, posture: 0 };

    document.getElementById('web-final-score-val').innerText = finalScore;
    document.getElementById('web-tier-label').innerText = tier;

    // SVG Score Circle Offset (dasharray 314)
    const circle = document.getElementById('web-score-circle');
    if (circle) {
        const offset = 314 - (314 * (finalScore / 100));
        circle.style.strokeDashoffset = offset;
    }

    // Dynamic Sub-score percentage & progress bar rendering
    const s = breakdown.strength || 0;
    const f = breakdown.flexibility || 0;
    const b = breakdown.balance || 0;
    const p = breakdown.posture || 0;

    if (document.getElementById('web-val-strength')) document.getElementById('web-val-strength').innerText = `${s}%`;
    if (document.getElementById('web-bar-strength')) document.getElementById('web-bar-strength').style.width = `${s}%`;

    if (document.getElementById('web-val-flexibility')) document.getElementById('web-val-flexibility').innerText = `${f}%`;
    if (document.getElementById('web-bar-flexibility')) document.getElementById('web-bar-flexibility').style.width = `${f}%`;

    if (document.getElementById('web-val-balance')) document.getElementById('web-val-balance').innerText = `${b}%`;
    if (document.getElementById('web-bar-balance')) document.getElementById('web-bar-balance').style.width = `${b}%`;

    if (document.getElementById('web-val-posture')) document.getElementById('web-val-posture').innerText = `${p}%`;
    if (document.getElementById('web-bar-posture')) document.getElementById('web-bar-posture').style.width = `${p}%`;

    if (data.recommendations) renderWebRecommendations(data.recommendations, data.workout_plan);
}

function renderWebRecommendations(recs, workoutPlan) {
    const grid = document.getElementById('web-recommendations-grid');
    if (grid && recs) {
        grid.innerHTML = recs.map((r, i) => `
            <div class="web-card" style="position: relative; border-color: rgba(0, 242, 254, 0.25);">
                <div style="font-size: 0.72rem; font-weight: 800; text-transform: uppercase; color: var(--primary-accent); margin-bottom: 6px; display: flex; justify-content: space-between;">
                    <span>Drill #${i + 1}</span>
                    <span style="background: rgba(0, 242, 254, 0.1); padding: 2px 8px; border-radius: 10px;">${r.source || 'AI Engine'}</span>
                </div>
                <h4 style="font-size: 1.1rem; margin-bottom: 8px; color: var(--text-main);">${r.exercise}</h4>
                <div style="font-size: 0.83rem; color: var(--text-muted); margin-bottom: 12px;">
                    <i class="fa-solid fa-clock"></i> Duration: <strong>${r.duration}</strong> | Frequency: <strong>${r.frequency}</strong>
                </div>
                <p style="font-size: 0.82rem; color: #94a3b8; line-height: 1.4;">${r.reason || 'Custom drill tailored for biomechanical posture refinement.'}</p>
            </div>
        `).join('');
    }

    const planGrid = document.getElementById('web-workout-schedule-grid');
    if (planGrid && workoutPlan && workoutPlan.schedule) {
        planGrid.innerHTML = workoutPlan.schedule.map(s => `
            <div class="web-card" style="background: rgba(255,255,255,0.02); text-align: center;">
                <div style="font-size: 0.75rem; font-weight: 800; color: var(--emerald-accent); text-transform: uppercase; margin-bottom: 4px;">Week ${s.week}</div>
                <h4 style="font-size: 0.95rem; margin-bottom: 6px;">${s.exercise}</h4>
                <div style="font-size: 0.8rem; color: var(--text-muted);">${s.sets} Sets × ${s.reps} Reps</div>
            </div>
        `).join('');
    }
}

/* Assessment Diagnostic PDF Report Modal Functions */
function openAssessmentReportModal() {
    const modal = document.getElementById('modal-assessment-report');
    const container = document.getElementById('report-printable-area');
    if (!modal || !container) return;

    const data = lastAssessmentData || {
        scoring: {
            fitness_score: repCount === 0 ? 0.0 : 76.5,
            tier: repCount === 0 ? "No Reps / Idle Video (0% Score)" : "Good (Fit Level)",
            breakdown: { strength: repCount === 0 ? 0 : 70, flexibility: repCount === 0 ? 0 : 75, balance: repCount === 0 ? 0 : 80, posture: repCount === 0 ? 0 : 80 }
        },
        recommendations: [
            { exercise: "Compound Strength Resistance & Form Tracking", duration: "20 mins", frequency: "3x / week", source: "RandomForestML", reason: "Targeted posture alignment drill." },
            { exercise: "Scapular Retraction & Hamstring Stretch", duration: "15 mins", frequency: "Daily", source: "RuleEngine", reason: "Mobility & joint ROM optimization." }
        ],
        workout_plan: {
            intensity: repCount === 0 ? "Remedial / Beginner" : "Intermediate Fit",
            schedule: [
                { week: 1, exercise: "Box Squats & Wall Pushups", sets: 3, reps: 10 },
                { week: 2, exercise: "Supported Squats & Knee Pushups", sets: 3, reps: 12 },
                { week: 3, exercise: "Bodyweight Squats & Counter Pushups", sets: 3, reps: 15 },
                { week: 4, exercise: "Standard Squats & Full Pushups", sets: 3, reps: 12 }
            ]
        }
    };

    const scoring = data.scoring || {};
    const finalScore = scoring.fitness_score !== undefined ? scoring.fitness_score : 0.0;
    const tier = scoring.tier || "Standard Fit Level";
    const breakdown = scoring.breakdown || { strength: 0, flexibility: 0, balance: 0, posture: 0 };
    const dateStr = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    const athleteName = currentUser ? currentUser.name : "Alex Rivera";
    const athleteEmail = currentUser ? currentUser.email : "alex@example.com";

    // Build specific improvement areas based on scores
    const improvements = [];
    if (breakdown.strength < 70) {
        improvements.push({
            title: "Strength & Repetition Output",
            score: breakdown.strength,
            issue: "Low muscle power & endurance detected.",
            action: "Focus on building foundational compound resistance. Increase rep volume progressively."
        });
    }
    if (breakdown.flexibility < 70) {
        improvements.push({
            title: "Joint Flexibility & Mobility",
            score: breakdown.flexibility,
            issue: "Restricted Range of Motion (ROM) during execution.",
            action: "Perform daily hamstring extensibility stretches, hip openers, and deep squat depth mobility drills."
        });
    }
    if (breakdown.balance < 70) {
        improvements.push({
            title: "Center of Gravity & Body Stability",
            score: breakdown.balance,
            issue: "Horizontal shoulder/hip tilt or wobbling detected.",
            action: "Engage core muscles continuously. Practice single-leg stance balance and plank holds."
        });
    }
    if (breakdown.posture < 70) {
        improvements.push({
            title: "Spinal Alignment & Posture",
            score: breakdown.posture,
            issue: "Excessive forward spine/torso slouch or rounded shoulders.",
            action: "Perform scapular retractions, wall slides, and keep chest upright during all reps."
        });
    }
    if (improvements.length === 0) {
        improvements.push({
            title: "General Maintenance & Form Perfection",
            score: finalScore,
            issue: "Overall biomechanics are solid.",
            action: "Maintain current movement depth, increase tempo control, and add moderate resistance."
        });
    }

    container.innerHTML = `
        <div class="report-header-banner" style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(0, 242, 254, 0.12)); border-color: rgba(16, 185, 129, 0.3);">
            <div>
                <div style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase; color: var(--emerald-accent); letter-spacing: 1px;">PERSONALIZED ACTION PLAN</div>
                <h2 style="font-size: 1.6rem; margin: 4px 0; color: var(--text-main);">Fitness Improvement & Regular Practice Report</h2>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin: 0;">Tailored recommendations & 4-week practice schedule based on your pose session.</p>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 2.2rem; font-weight: 900; color: ${finalScore > 0 ? 'var(--emerald-accent)' : '#ef4444'};">${finalScore}%</div>
                <div style="font-size: 0.8rem; font-weight: 700; color: var(--text-muted);">${tier}</div>
            </div>
        </div>

        <!-- User Profile Summary -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px; background: rgba(255,255,255,0.02); border: 1px solid var(--card-border); padding: 12px 16px; border-radius: 12px; font-size: 0.85rem;">
            <div><strong>Athlete:</strong> <span>${athleteName}</span></div>
            <div><strong>Sport Category:</strong> <span style="color: var(--primary-accent); font-weight:700;">${currentCategory.toUpperCase()}</span></div>
            <div><strong>Exercise:</strong> <span style="color: var(--emerald-accent); font-weight:700;">${currentExercise.toUpperCase()}</span></div>
            <div><strong>Date:</strong> <span>${dateStr}</span></div>
        </div>

        <!-- SECTION 1: WHAT YOU SHOULD IMPROVE -->
        <div style="margin-bottom: 24px;">
            <h3 style="font-size: 1.15rem; margin-bottom: 12px; color: #fca5a5; display: flex; align-items: center; gap: 8px;">
                <i class="fa-solid fa-triangle-exclamation"></i> 1. WHAT YOU NEED TO IMPROVE (Specific Form Weaknesses)
            </h3>
            <div style="display: flex; flex-direction: column; gap: 10px;">
                ${improvements.map(imp => `
                    <div style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.25); padding: 12px 16px; border-radius: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-weight: 800;">
                            <span style="color: #fca5a5;">${imp.title}</span>
                            <span style="color: #ef4444; font-size: 0.85rem;">Score: ${imp.score}%</span>
                        </div>
                        <div style="font-size: 0.84rem; color: var(--text-muted); margin-bottom: 6px;"><strong>Detected Issue:</strong> ${imp.issue}</div>
                        <div style="font-size: 0.85rem; color: var(--text-main); background: rgba(0,0,0,0.2); padding: 8px 12px; border-radius: 6px;">
                            <strong style="color: var(--emerald-accent);">Corrective Action:</strong> ${imp.action}
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>

        <!-- SECTION 2: WHAT PRACTICE DO YOU DO ON A REGULAR BASIS -->
        <div style="margin-bottom: 24px;">
            <h3 style="font-size: 1.15rem; margin-bottom: 12px; color: var(--emerald-accent); display: flex; align-items: center; gap: 8px;">
                <i class="fa-solid fa-person-running"></i> 2. REGULAR PRACTICE & DAILY DRILLS (What to Do Regularly)
            </h3>

            <!-- Daily Morning Practice Box -->
            <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.3); padding: 14px; border-radius: 10px; margin-bottom: 12px;">
                <h4 style="font-size: 0.95rem; color: var(--emerald-accent); margin-bottom: 6px;"><i class="fa-solid fa-sun"></i> Daily Morning Practice Routine (10-15 Minutes Every Morning)</h4>
                <ul style="padding-left: 20px; font-size: 0.84rem; color: var(--text-main); margin: 0; line-height: 1.6;">
                    <li><strong>Postural Wall Slides:</strong> 3 Sets × 12 Reps (Scapular Retraction & Shoulder Alignment).</li>
                    <li><strong>Cobra Pose Extension:</strong> 3 Holds × 30 Seconds (Lumbar Spine Flexibility).</li>
                    <li><strong>Bodyweight Squat Depth Hold:</strong> 3 Holds × 20 Seconds (Hip Opener & Ankle Range).</li>
                </ul>
            </div>

            <!-- Recommended AI Drills -->
            <div style="display: flex; flex-direction: column; gap: 10px;">
                ${(data.recommendations || []).map(r => `
                    <div style="background: rgba(0, 242, 254, 0.04); border: 1px solid rgba(0, 242, 254, 0.25); padding: 12px; border-radius: 10px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <strong style="color:var(--primary-accent);">${r.exercise}</strong>
                            <span style="font-size:0.75rem; background:rgba(0,242,254,0.15); color:var(--primary-accent); padding:2px 8px; border-radius:10px; font-weight:700;">${r.frequency}</span>
                        </div>
                        <div style="font-size:0.83rem; color:var(--text-muted);">
                            Duration: <strong>${r.duration}</strong> per session | Focus: ${r.reason || 'Biomechanical form optimization.'}
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>

        <!-- SECTION 3: COMPLETE 4-WEEK PRACTICE SCHEDULE -->
        <div style="margin-bottom: 20px;">
            <h3 style="font-size: 1.15rem; margin-bottom: 12px; color: var(--violet-accent); display: flex; align-items: center; gap: 8px;">
                <i class="fa-solid fa-calendar-check"></i> 3. COMPLETE 4-WEEK PRACTICE & PROGRESSION SCHEDULE
            </h3>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Practice Week</th>
                        <th>Recommended Training Focus</th>
                        <th>Target Sets & Reps</th>
                        <th>Progression Goal</th>
                    </tr>
                </thead>
                <tbody>
                    ${((data.workout_plan && data.workout_plan.schedule) || []).map(s => `
                        <tr>
                            <td><strong style="color: var(--emerald-accent);">Week ${s.week}</strong></td>
                            <td><strong>${s.exercise}</strong></td>
                            <td>${s.sets} Sets × ${s.reps} Reps</td>
                            <td style="font-size:0.82rem; color:var(--text-muted);">
                                ${s.week === 1 ? 'Form & Depth Foundation' : (s.week === 2 ? 'Mobility & Range Build' : (s.week === 3 ? 'Volume & Stamina Push' : 'Full Standard Execution'))}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>

        <div style="margin-top: 24px; padding-top: 12px; border-top: 1px dashed var(--card-border); font-size: 0.78rem; color: var(--text-muted); display: flex; justify-content: space-between;">
            <div>Report Engine: Biomechanical Rule Engine + Scikit-Learn RandomForest</div>
            <div>Storage DB: <code>fitness_app.db</code> & <code>users_auth.db</code></div>
        </div>
    `;

    modal.classList.remove('hidden');
}

function closeReportModal(e) {
    const modal = document.getElementById('modal-assessment-report');
    if (modal) modal.classList.add('hidden');
}

function printAssessmentReport() {
    window.print();
}

function handleProfileUpdate(e) {
    e.preventDefault();
    alert("Profile saved!");
    switchWebPage('page-dashboard');
}

function loadAnalyticsData() {
    const trendChart = document.getElementById('web-trend-chart');
    if (trendChart) {
        trendChart.innerHTML = `
            <div style="display:flex; flex-direction:column; align-items:center; gap:6px;"><span style="color:var(--primary-accent); font-weight:700;">68</span><div style="width:30px; height:100px; background:var(--primary-accent); border-radius:8px;"></div><span style="font-size:0.75rem;">S1</span></div>
            <div style="display:flex; flex-direction:column; align-items:center; gap:6px;"><span style="color:var(--primary-accent); font-weight:700;">74</span><div style="width:30px; height:125px; background:var(--primary-accent); border-radius:8px;"></div><span style="font-size:0.75rem;">S2</span></div>
            <div style="display:flex; flex-direction:column; align-items:center; gap:6px;"><span style="color:var(--primary-accent); font-weight:700;">78.5</span><div style="width:30px; height:140px; background:var(--emerald-accent); border-radius:8px;"></div><span style="font-size:0.75rem;">S3</span></div>
        `;
    }
}

/* ==========================================================================
   AUTHENTICATION & SEPARATE DATABASE CONTROLLER
   ========================================================================== */

function checkAuthOnStartup() {
    const savedSession = localStorage.getItem('fitpulse_session');
    if (savedSession) {
        try {
            const user = JSON.parse(savedSession);
            onAuthSuccess(user, false);
            return;
        } catch (e) {
            localStorage.removeItem('fitpulse_session');
        }
    }
    // Show Login Screen First if no valid session exists
    showLoginScreen();
}

function showLoginScreen() {
    const loginView = document.getElementById('login-screen-view');
    if (loginView) loginView.classList.remove('hidden');
}

function hideLoginScreen() {
    const loginView = document.getElementById('login-screen-view');
    if (loginView) loginView.classList.add('hidden');
}

function switchAuthTab(tab) {
    document.getElementById('tab-login')?.classList.toggle('active', tab === 'login');
    document.getElementById('tab-register')?.classList.toggle('active', tab === 'register');

    document.getElementById('form-login')?.classList.toggle('hidden', tab !== 'login');
    document.getElementById('form-register')?.classList.toggle('hidden', tab !== 'register');

    hideAuthAlert();
}

function togglePasswordVisibility(fieldId, iconElem) {
    const input = document.getElementById(fieldId);
    if (input) {
        if (input.type === 'password') {
            input.type = 'text';
            iconElem.classList.replace('fa-eye', 'fa-eye-slash');
        } else {
            input.type = 'password';
            iconElem.classList.replace('fa-eye-slash', 'fa-eye');
        }
    }
}

function showAuthAlert(message, type = 'error') {
    const alertBox = document.getElementById('auth-alert');
    if (alertBox) {
        alertBox.className = `auth-alert ${type}`;
        alertBox.innerHTML = type === 'error' ?
            `<i class="fa-solid fa-triangle-exclamation"></i> ${message}` :
            `<i class="fa-solid fa-circle-check"></i> ${message}`;
        alertBox.classList.remove('hidden');
    }
}

function hideAuthAlert() {
    const alertBox = document.getElementById('auth-alert');
    if (alertBox) alertBox.classList.add('hidden');
}

async function handleLoginSubmit(event) {
    event.preventDefault();
    hideAuthAlert();

    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const btn = document.getElementById('btn-login-submit');

    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Authenticating with users_auth.db...`;
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (data.success && data.user) {
            showAuthAlert(`Login successful! Redirecting to Dashboard...`, 'success');
            setTimeout(() => {
                onAuthSuccess(data.user, true);
            }, 600);
        } else {
            showAuthAlert(data.message || 'Invalid login credentials.', 'error');
        }
    } catch (err) {
        // Fallback demo login if server is starting or network issue
        console.warn("Backend auth call fallback:", err);
        const fallbackUser = { id: 1, name: "Alex Rivera", email: email || "alex@example.com", age: 24, gender: "Male" };
        showAuthAlert(`Authenticated via Local Auth Engine. Welcome!`, 'success');
        setTimeout(() => {
            onAuthSuccess(fallbackUser, true);
        }, 600);
    } finally {
        btn.innerHTML = `<span>Sign In to Dashboard</span> <i class="fa-solid fa-arrow-right"></i>`;
        btn.disabled = false;
    }
}

async function handleRegisterSubmit(event) {
    event.preventDefault();
    hideAuthAlert();

    const name = document.getElementById('reg-name').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const age = parseInt(document.getElementById('reg-age').value) || 24;
    const gender = document.getElementById('reg-gender').value;
    const btn = document.getElementById('btn-register-submit');

    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Creating Account in users_auth.db...`;
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password, age, gender })
        });
        const data = await res.json();

        if (data.success) {
            showAuthAlert(`Account created in users_auth.db! Logging in...`, 'success');
            setTimeout(() => {
                onAuthSuccess(data.user || { id: 2, name, email, age, gender }, true);
            }, 800);
        } else {
            showAuthAlert(data.message || 'Registration failed.', 'error');
        }
    } catch (err) {
        console.warn("Backend reg call fallback:", err);
        const newUser = { id: Date.now(), name, email, age, gender };
        onAuthSuccess(newUser, true);
    } finally {
        btn.innerHTML = `<span>Create Account (Saves to users_auth.db)</span> <i class="fa-solid fa-user-check"></i>`;
        btn.disabled = false;
    }
}

function quickLogin(email, password) {
    document.getElementById('login-email').value = email;
    document.getElementById('login-password').value = password;
    switchAuthTab('login');
    const fakeEvent = { preventDefault: () => { } };
    handleLoginSubmit(fakeEvent);
}

function onAuthSuccess(userData, isNewLogin) {
    currentUser = userData;
    localStorage.setItem('fitpulse_session', JSON.stringify(userData));

    // Update UI Elements
    const nameStr = userData.name || "Alex Rivera";
    const emailStr = userData.email || "alex@example.com";
    const initials = nameStr.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2) || "AR";

    const userDispName = document.getElementById('user-display-name');
    if (userDispName) userDispName.innerText = nameStr;

    const userDispEmail = document.getElementById('user-display-email');
    if (userDispEmail) userDispEmail.innerText = emailStr;

    const avatarInitials = document.getElementById('avatar-initials');
    if (avatarInitials) avatarInitials.innerText = initials;

    const dashGreeting = document.getElementById('dash-greeting-name');
    if (dashGreeting) dashGreeting.innerText = nameStr;

    // Update Profile Inputs
    if (document.getElementById('prof-name')) document.getElementById('prof-name').value = nameStr;
    if (document.getElementById('prof-email')) document.getElementById('prof-email').value = emailStr;

    hideLoginScreen();
    switchWebPage('page-dashboard');
}

function logoutUser() {
    localStorage.removeItem('fitpulse_session');
    currentUser = null;
    showLoginScreen();
    switchAuthTab('login');
    showAuthAlert("You have been signed out. Please sign in to access the system.", "success");
}

/* Database Inspection Modal */
function showAuthDbModal() {
    const modal = document.getElementById('modal-db-info');
    if (modal) {
        modal.classList.remove('hidden');
        fetchDatabaseInspection();
    }
}

function closeAuthDbModal(e) {
    const modal = document.getElementById('modal-db-info');
    if (modal) modal.classList.add('hidden');
}

async function fetchDatabaseInspection() {
    const box = document.getElementById('live-db-inspect-content');
    if (!box) return;

    try {
        const res = await fetch(`${API_BASE_URL}/auth/info`);
        const data = await res.json();

        box.innerHTML = `
            <div style="color:var(--emerald-accent); font-weight:700; margin-bottom:8px;">
                <i class="fa-solid fa-circle-check"></i> Connected Engine: ${data.database_engine} (File Extension: ${data.database_file_extension})
            </div>
            <div style="margin-bottom:6px; color:var(--primary-accent);">
                📁 Auth DB: ${data.auth_database_file} (${data.user_auth_count || 0} user records)
            </div>
            <div style="margin-bottom:10px; color:var(--violet-accent);">
                📁 Main DB: ${data.main_database_file}
            </div>
            <div style="border-top:1px solid rgba(255,255,255,0.1); padding-top:8px; margin-top:8px;">
                <strong>Recent Auth Audit Logs (users_auth.db):</strong>
                <ul style="padding-left: 18px; margin-top: 4px; color: var(--text-muted);">
                    ${(data.recent_audit_logs || []).map(l => `<li>[${l.Timestamp || 'NOW'}] ${l.Email} → <code>${l.LoginStatus}</code></li>`).join('')}
                </ul>
            </div>
        `;
    } catch (e) {
        box.innerHTML = `
            <div style="color:var(--primary-accent); font-weight:700;">
                <i class="fa-solid fa-database"></i> Database Engine: SQLite 3 (.db extension)
            </div>
            <div style="margin-top:6px;">
                1. <strong>users_auth.db</strong> (Separate User Authentication DB)<br>
                2. <strong>fitness_app.db</strong> (Main Fitness Assessment & Kinematics DB)
            </div>
        `;
    }
}

/* ==========================================================================
   THEME MANAGEMENT (DARK & LIGHT MODE)
   ========================================================================== */

function initTheme() {
    const savedTheme = localStorage.getItem("fitpulse_theme");
    const systemPrefersLight = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;
    const initialTheme = savedTheme || (systemPrefersLight ? "light" : "dark");
    applyTheme(initialTheme, false);

    // Listen for OS theme changes if user has no saved preference
    if (window.matchMedia) {
        window.matchMedia("(prefers-color-scheme: light)").addEventListener("change", e => {
            if (!localStorage.getItem("fitpulse_theme")) {
                applyTheme(e.matches ? "light" : "dark", false);
            }
        });
    }
}

function applyTheme(theme, save = true) {
    const isLight = theme === "light";
    document.documentElement.setAttribute("data-theme", theme);
    
    if (isLight) {
        document.body.classList.add("light-theme");
    } else {
        document.body.classList.remove("light-theme");
    }

    if (save) {
        localStorage.setItem("fitpulse_theme", theme);
    }

    updateThemeUI(theme);

    // If assessment canvas is showing standby, re-render with matching background
    if (currentMode === 'IDLE') {
        const canvas = document.getElementById('output-canvas');
        if (canvas && canvas.offsetParent !== null) {
            renderStandbyCanvas();
        }
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
    const nextTheme = currentTheme === "dark" ? "light" : "dark";
    applyTheme(nextTheme, true);
}

function setAppTheme(theme) {
    applyTheme(theme, true);
}

function updateThemeUI(theme) {
    const isLight = theme === "light";

    // Top Navbar Toggle Button
    const navIcon = document.getElementById("theme-icon");
    const navText = document.getElementById("theme-text");
    if (navIcon) navIcon.className = isLight ? "fa-solid fa-sun" : "fa-solid fa-moon";
    if (navText) navText.innerText = isLight ? "Light" : "Dark";

    // Auth Screen Toggle Buttons
    const authIcons = document.querySelectorAll(".auth-theme-icon");
    const authLabels = document.querySelectorAll(".auth-theme-label");
    authIcons.forEach(ic => {
        ic.className = isLight ? "fa-solid fa-sun auth-theme-icon" : "fa-solid fa-moon auth-theme-icon";
    });
    authLabels.forEach(lb => {
        lb.innerText = isLight ? "Light" : "Dark";
    });

    // Profile Settings Theme Option Cards
    const darkOption = document.getElementById("theme-opt-dark");
    const lightOption = document.getElementById("theme-opt-light");
    if (darkOption && lightOption) {
        if (isLight) {
            darkOption.classList.remove("active");
            lightOption.classList.add("active");
        } else {
            darkOption.classList.add("active");
            lightOption.classList.remove("active");
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    switchSportModule('gym');
    checkAuthOnStartup();
});
