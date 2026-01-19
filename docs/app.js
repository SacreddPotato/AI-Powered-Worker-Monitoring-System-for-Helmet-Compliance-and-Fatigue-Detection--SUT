/* app.js — Updated */

const $ = (sel) => document.querySelector(sel);
function safeGet(id){ return document.getElementById(id); }

// Sidebar Logic
function initSidebar(){
  const menuToggle = document.getElementById('menuToggle');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  if(!sidebar || !menuToggle) return;
  
  if(window.innerWidth <= 980) sidebar.classList.add('closed');
  
  menuToggle.addEventListener('click', () => {
    const isClosed = sidebar.classList.toggle('closed');
    if(window.innerWidth <= 980){
      overlay.classList.toggle('active', !isClosed);
    }
  });
  
  if(overlay) overlay.addEventListener('click', () => {
    sidebar.classList.add('closed');
    overlay.classList.remove('active');
  });
}

// =========================
// FAQ Logic (NEW)
// =========================
function initFaqPage(){
  const questions = document.querySelectorAll('.question');
  // Just return if we aren't on the FAQ page
  if(questions.length === 0) return;

  questions.forEach(q => {
    q.addEventListener('click', () => {
      // 1. Remove active styling from all list items
      questions.forEach(item => item.style.backgroundColor = 'transparent');
      questions.forEach(item => item.style.color = 'inherit');
      
      // 2. Add active styling to clicked
      // (Using inline style or class, let's use the styles.css hover variables mostly)
      q.classList.add('active'); // You can style this class in CSS if you want specific active state
      
      // 3. Hide all answer divs
      document.querySelectorAll('.faq-answer > div').forEach(div => div.classList.add('hidden'));

      // 4. Show the target answer
      const ansId = q.getAttribute('data-answer');
      const target = document.getElementById(ansId);
      if(target) target.classList.remove('hidden');
    });
  });
}

// =========================
// Fatigue Page
// =========================
function initFatiguePage(){
  const camBtn = safeGet('camFat');
  const clearBtn = safeGet('clearFat');
  const preview = safeGet('previewFat');
  const container = safeGet('viewerWrapFat');
  
  const urlParams = new URLSearchParams(window.location.search);
  const source = urlParams.get('source');

  let streamImg = document.getElementById('serverStreamFat');
  if(!streamImg && container){
      streamImg = document.createElement('img');
      streamImg.id = 'serverStreamFat';
      streamImg.style.width = '100%';
      streamImg.style.display = 'none';
      streamImg.style.borderRadius = '8px';
      container.appendChild(streamImg);
  }

  if(source && streamImg) {
      if(preview) preview.style.display = 'none';
      streamImg.src = "/video_feed?source=" + encodeURIComponent(source);
      streamImg.style.display = 'block';
  }

  if(camBtn){
    camBtn.addEventListener('click', () => {
       if(preview) preview.style.display = 'none';
       if(streamImg) {
           streamImg.src = "/video_feed?source=0&t=" + new Date().getTime();
           streamImg.style.display = 'block';
       }
       const logArea = safeGet('logAreaFat');
       if(logArea) logArea.innerHTML = `<div>${new Date().toLocaleTimeString()} - Webcam Started</div>` + logArea.innerHTML;
    });
  }

  if(clearBtn){
      clearBtn.addEventListener('click', () => {
          if(streamImg) {
              streamImg.src = "";
              streamImg.style.display = 'none';
          }
          if(preview) preview.style.display = 'block';
          window.history.pushState({}, document.title, window.location.pathname);
      });
  }
}

// =========================
// Helmet Page
// =========================
function initHelmetPage(){
  const camBtn = safeGet('camHelmet');
  const clearBtn = safeGet('clearHelmet');
  const preview = safeGet('previewHelmet');
  const container = safeGet('viewerWrapHelmet');
  
  const urlParams = new URLSearchParams(window.location.search);
  const source = urlParams.get('source');

  let streamImg = document.getElementById('serverStreamHelmet');
  if(!streamImg && container){
      streamImg = document.createElement('img');
      streamImg.id = 'serverStreamHelmet';
      streamImg.style.width = '100%';
      streamImg.style.display = 'none';
      streamImg.style.borderRadius = '8px';
      container.appendChild(streamImg);
  }

  if(source && streamImg) {
      if(preview) preview.style.display = 'none';
      streamImg.src = "/helmet_video_feed?source=" + encodeURIComponent(source);
      streamImg.style.display = 'block';
  }

  if(camBtn){
    camBtn.addEventListener('click', () => {
       if(preview) preview.style.display = 'none';
       if(streamImg) {
           streamImg.src = "/helmet_video_feed?source=0&t=" + new Date().getTime();
           streamImg.style.display = 'block';
       }
       const logArea = safeGet('logAreaHelmet');
       if(logArea) logArea.innerHTML = `<div>${new Date().toLocaleTimeString()} - Helmet Detection Started</div>` + logArea.innerHTML;
    });
  }

  if(clearBtn){
      clearBtn.addEventListener('click', () => {
          if(streamImg) {
              streamImg.src = "";
              streamImg.style.display = 'none';
          }
          if(preview) preview.style.display = 'block';
          window.history.pushState({}, document.title, window.location.pathname);
          const logArea = safeGet('logAreaHelmet');
          if(logArea) logArea.innerHTML = `<div>${new Date().toLocaleTimeString()} - Detection Stopped</div>` + logArea.innerHTML;
      });
  }
}

// =========================
// Slideshow
// =========================
function initFeaturesSlideshow(){
  const slideshow = document.querySelector('.features-slideshow');
  if(!slideshow) return;
  
  const track = slideshow.querySelector('.slideshow-track');
  const slides = slideshow.querySelectorAll('.slide');
  const dots = slideshow.querySelectorAll('.dot');
  const prevBtn = slideshow.querySelector('.slide-nav.prev');
  const nextBtn = slideshow.querySelector('.slide-nav.next');
  
  if(!track || slides.length === 0) return;
  
  let currentSlide = 1;
  let autoPlayInterval = null;
  const autoPlayDelay = 5000;
  
  function updateSlideshow() {
    track.style.transform = `translateX(-${currentSlide * 100}%)`;
    slides.forEach((slide, index) => slide.classList.toggle('active', index === currentSlide));
    dots.forEach((dot, index) => dot.classList.toggle('active', index === currentSlide));
  }
  
  function goToSlide(index) {
    if(index < 0) index = slides.length - 1;
    if(index >= slides.length) index = 0;
    currentSlide = index;
    updateSlideshow();
    resetAutoPlay();
  }
  
  function nextSlide() { goToSlide(currentSlide + 1); }
  function prevSlide() { goToSlide(currentSlide - 1); }
  
  function startAutoPlay() { autoPlayInterval = setInterval(nextSlide, autoPlayDelay); }
  function stopAutoPlay() { if(autoPlayInterval) { clearInterval(autoPlayInterval); autoPlayInterval = null; } }
  function resetAutoPlay() { stopAutoPlay(); startAutoPlay(); }
  
  if(nextBtn) nextBtn.addEventListener('click', nextSlide);
  if(prevBtn) prevBtn.addEventListener('click', prevSlide);
  dots.forEach((dot, index) => dot.addEventListener('click', () => goToSlide(index)));
  
  slideshow.addEventListener('mouseenter', stopAutoPlay);
  slideshow.addEventListener('mouseleave', startAutoPlay);
  
  let touchStartX = 0;
  let touchEndX = 0;
  track.addEventListener('touchstart', (e) => { touchStartX = e.changedTouches[0].screenX; stopAutoPlay(); });
  track.addEventListener('touchend', (e) => { touchEndX = e.changedTouches[0].screenX; handleSwipe(); startAutoPlay(); });
  
  function handleSwipe() {
    if(Math.abs(touchStartX - touchEndX) > 50) {
      if(touchStartX - touchEndX > 0) nextSlide(); else prevSlide();
    }
  }
  
  updateSlideshow();
  startAutoPlay();
}

// =========================
// Fatigue V2 Page (3 Classes)
// =========================
function initFatigueV2Page(){
  // Check if we're on the fatigue-v2 page
  const webcamVideo = document.getElementById("webcamVideo");
  if(!webcamVideo) return;

  // Use relative URL (same server)
  const API_URL = "";
  let stream = null;
  let autoDetectInterval = null;

  const previewImg = document.getElementById("previewFatV2");
  const canvas = document.getElementById("captureCanvas");
  const ctx = canvas.getContext("2d");
  const camBtn = document.getElementById("camFatV2");
  const captureBtn = document.getElementById("captureFatV2");
  const clearBtn = document.getElementById("clearFatV2");
  const uploadInput = document.getElementById("uploadImageInput");
  const autoDetectCheckbox = document.getElementById("autoDetectCheckbox");
  const logArea = document.getElementById("logAreaFatV2");
  const connectionStatus = document.getElementById("connectionStatus");
  const detectionResults = document.getElementById("detectionResults");

  // Helper Functions
  function addLog(message, color = "#6b7280") {
    const timestamp = new Date().toLocaleTimeString();
    logArea.innerHTML += `<div style="color: ${color}; margin-bottom: 0.5rem;">[${timestamp}] ${message}</div>`;
    logArea.scrollTop = logArea.scrollHeight;
  }

  function clearLogs() {
    logArea.innerHTML = "Ready.";
  }

  // Connection Test
  async function testConnection() {
    try {
      const response = await fetch(`${API_URL}/health`);
      const data = await response.json();

      if (data.status === "healthy") {
        connectionStatus.innerHTML = `<span style="color: #10b981">✅ Connected (Accuracy: ${data.accuracy}%)</span>`;
        addLog(`✅ API Connected - Accuracy: ${data.accuracy}%`, "#10b981");
        return true;
      }
    } catch (error) {
      connectionStatus.innerHTML = `<span style="color: #ef4444">❌ Not Connected - Start Flask API</span>`;
      addLog(`❌ Connection failed: ${error.message}`, "#ef4444");
      return false;
    }
  }

  // Test on load
  testConnection();
  setInterval(testConnection, 30000);

  // Webcam Functions
  camBtn.addEventListener("click", async () => {
    if (!stream) {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
        });
        webcamVideo.srcObject = stream;
        webcamVideo.style.display = "block";
        previewImg.style.display = "none";

        camBtn.textContent = "Webcam Active";
        camBtn.classList.remove("primary");
        addLog("📹 Webcam started", "#10b981");
      } catch (error) {
        addLog(`❌ Webcam error: ${error.message}`, "#ef4444");
        alert("Could not access webcam: " + error.message);
      }
    }
  });

  clearBtn.addEventListener("click", () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      webcamVideo.srcObject = null;
      webcamVideo.style.display = "none";
      previewImg.style.display = "block";
      previewImg.src = "assets/logo.jpeg";

      camBtn.textContent = "Start Webcam";
      camBtn.classList.add("primary");
      addLog("⏹️ Webcam stopped", "#6b7280");
    }

    if (autoDetectInterval) {
      clearInterval(autoDetectInterval);
      autoDetectInterval = null;
      autoDetectCheckbox.checked = false;
    }

    detectionResults.style.display = "none";
    clearLogs();
  });

  // Capture & Analyze
  captureBtn.addEventListener("click", async () => {
    if (!webcamVideo.srcObject) {
      alert("Please start webcam first!");
      return;
    }

    canvas.width = webcamVideo.videoWidth;
    canvas.height = webcamVideo.videoHeight;
    ctx.drawImage(webcamVideo, 0, 0);

    const imageBase64 = canvas.toDataURL("image/jpeg", 0.8);
    await sendPrediction(imageBase64, "webcam");
  });

  // Auto-Detect
  autoDetectCheckbox.addEventListener("change", () => {
    if (autoDetectCheckbox.checked) {
      if (!webcamVideo.srcObject) {
        alert("Please start webcam first!");
        autoDetectCheckbox.checked = false;
        return;
      }

      addLog("🔄 Auto-detect enabled (every 2s)", "#f59e0b");
      autoDetectInterval = setInterval(async () => {
        canvas.width = webcamVideo.videoWidth;
        canvas.height = webcamVideo.videoHeight;
        ctx.drawImage(webcamVideo, 0, 0);
        const imageBase64 = canvas.toDataURL("image/jpeg", 0.8);
        await sendPrediction(imageBase64, "webcam");
      }, 2000);
    } else {
      if (autoDetectInterval) {
        clearInterval(autoDetectInterval);
        autoDetectInterval = null;
        addLog("⏸️ Auto-detect disabled", "#6b7280");
      }
    }
  });

  // Upload Image
  uploadInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    addLog(`📤 Uploading: ${file.name}`, "#48bb78");

    const reader = new FileReader();
    reader.onload = async (event) => {
      const imageBase64 = event.target.result;

      previewImg.src = imageBase64;
      previewImg.style.display = "block";
      webcamVideo.style.display = "none";

      await sendPrediction(imageBase64, "upload");
    };
    reader.readAsDataURL(file);
  });

  // Send Prediction
  async function sendPrediction(imageBase64, source) {
    try {
      const startTime = Date.now();

      const response = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_base64: imageBase64,
          source: source,
        }),
      });

      const data = await response.json();
      const elapsed = Date.now() - startTime;

      if (data.error) {
        addLog(`❌ Error: ${data.error}`, "#ef4444");
        return;
      }

      updateResults(data);

      const className = data.predicted_class
        .toUpperCase()
        .replace("_", " ");
      addLog(
        `🎯 ${className} (${data.confidence}%) - ${elapsed}ms`,
        "#10b981"
      );
    } catch (error) {
      addLog(`❌ Request failed: ${error.message}`, "#ef4444");
    }
  }

  // Update Results
  function updateResults(data) {
    detectionResults.style.display = "block";

    const className = data.predicted_class;
    const confidence = data.confidence;
    const probs = data.probabilities;

    // Status
    const statusText = document.getElementById("statusText");
    const statusEmoji = document.getElementById("statusEmoji");
    const displayName = className.toUpperCase().replace("_", " ");

    statusText.textContent = displayName;

    if (className === "alert") {
      statusText.style.color = "#10b981";
      statusEmoji.textContent = "✅";
    } else if (className === "non_vigilant") {
      statusText.style.color = "#f59e0b";
      statusEmoji.textContent = "⚠️";
    } else {
      statusText.style.color = "#ef4444";
      statusEmoji.textContent = "😴";
    }

    // Confidence
    document.getElementById("confidenceValue").textContent =
      confidence + "%";
    const confidenceBar = document.getElementById("confidenceBar");
    confidenceBar.style.width = confidence + "%";

    if (className === "alert") {
      confidenceBar.style.background =
        "linear-gradient(90deg, #48bb78, #38a169)";
    } else if (className === "non_vigilant") {
      confidenceBar.style.background =
        "linear-gradient(90deg, #ed8936, #dd6b20)";
    } else {
      confidenceBar.style.background =
        "linear-gradient(90deg, #f56565, #e53e3e)";
    }

    // Probabilities
    document.getElementById("probAlertBar").style.width = probs.alert + "%";
    document.getElementById("probAlertValue").textContent =
      probs.alert + "%";

    document.getElementById("probNonVigilantBar").style.width =
      probs.non_vigilant + "%";
    document.getElementById("probNonVigilantValue").textContent =
      probs.non_vigilant + "%";

    document.getElementById("probTiredBar").style.width = probs.tired + "%";
    document.getElementById("probTiredValue").textContent =
      probs.tired + "%";

    // Features
    if (data.features) {
      const f = data.features;
      document.getElementById("facialFeatures").style.display = "block";
      document.getElementById("featuresContent").innerHTML = `
        👁️ EAR: <strong>${f.ear}</strong><br>
        😊 Smiling: <strong>${f.is_smiling ? "Yes" : "No"}</strong><br>
        🥱 Yawning: <strong>${f.is_yawning ? "Yes" : "No"}</strong><br>
        🔍 Method: <strong>${f.method}</strong>
      `;
    }
  }

  addLog("🚀 System ready", "#10b981");
}

function init(){
  try{ initSidebar(); }catch(e){}
  try{ initFatiguePage(); }catch(e){}
  try{ initHelmetPage(); }catch(e){}
  try{ initFeaturesSlideshow(); }catch(e){}
  try{ initFaqPage(); }catch(e){}
  try{ initFatigueV2Page(); }catch(e){}
}

if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();