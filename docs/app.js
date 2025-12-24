/* app.js — Updated for Flask Integration */

const $ = (sel) => document.querySelector(sel);

function safeGet(id){ return document.getElementById(id); }

// Sidebar Logic (Unchanged)
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
// Fatigue Page Integration (THE FIX)
// =========================
function initFatiguePage(){
  const camBtn = safeGet('camFat');
  const clearBtn = safeGet('clearFat');
  const preview = safeGet('previewFat');    // The default placeholder image
  const container = safeGet('viewerWrapFat'); // The container div
  
  // Check if we are viewing an uploaded video (from the URL query param)
  const urlParams = new URLSearchParams(window.location.search);
  const source = urlParams.get('source');

  // Create or Find the Stream Image Element
  let streamImg = document.getElementById('serverStreamFat');
  if(!streamImg && container){
      streamImg = document.createElement('img');
      streamImg.id = 'serverStreamFat';
      streamImg.style.width = '100%';
      streamImg.style.display = 'none';
      streamImg.style.borderRadius = '8px';
      container.appendChild(streamImg);
  }

  // If a source exists in URL (e.g. after upload), start playing it immediately
  if(source && streamImg) {
      if(preview) preview.style.display = 'none';
      streamImg.src = "/video_feed?source=" + encodeURIComponent(source);
      streamImg.style.display = 'block';
  }

  // "Use Camera" Button Logic
  if(camBtn){
    camBtn.addEventListener('click', () => {
       // 1. Hide the placeholder
       if(preview) preview.style.display = 'none';
       
       // 2. Point the image to the Python webcam feed
       if(streamImg) {
           // Add timestamp to prevent browser caching
           streamImg.src = "/video_feed?source=0&t=" + new Date().getTime();
           streamImg.style.display = 'block';
       }
       
       const logArea = safeGet('logAreaFat');
       if(logArea) logArea.innerHTML = `<div>${new Date().toLocaleTimeString()} - Webcam Started</div>` + logArea.innerHTML;
    });
  }

  // "Stop / Clear" Button Logic
  if(clearBtn){
      clearBtn.addEventListener('click', () => {
          if(streamImg) {
              streamImg.src = ""; // Cut the connection
              streamImg.style.display = 'none';
          }
          if(preview) preview.style.display = 'block'; // Show placeholder
          
          // Clear URL params so refresh doesn't reload the video
          window.history.pushState({}, document.title, window.location.pathname);
      });
  }
}

// =========================
// Helmet Page Integration
// =========================
function initHelmetPage(){
  const camBtn = safeGet('camHelmet');
  const clearBtn = safeGet('clearHelmet');
  const preview = safeGet('previewHelmet');    // The default placeholder image
  const container = safeGet('viewerWrapHelmet'); // The container div
  
  // Check if we are viewing an uploaded video (from the URL query param)
  const urlParams = new URLSearchParams(window.location.search);
  const source = urlParams.get('source');

  // Create or Find the Stream Image Element
  let streamImg = document.getElementById('serverStreamHelmet');
  if(!streamImg && container){
      streamImg = document.createElement('img');
      streamImg.id = 'serverStreamHelmet';
      streamImg.style.width = '100%';
      streamImg.style.display = 'none';
      streamImg.style.borderRadius = '8px';
      container.appendChild(streamImg);
  }

  // If a source exists in URL (e.g. after upload), start playing it immediately
  if(source && streamImg) {
      if(preview) preview.style.display = 'none';
      streamImg.src = "/helmet_video_feed?source=" + encodeURIComponent(source);
      streamImg.style.display = 'block';
  }

  // "Use Camera" Button Logic
  if(camBtn){
    camBtn.addEventListener('click', () => {
       // 1. Hide the placeholder
       if(preview) preview.style.display = 'none';
       
       // 2. Point the image to the Python helmet detection webcam feed
       if(streamImg) {
           // Add timestamp to prevent browser caching
           streamImg.src = "/helmet_video_feed?source=0&t=" + new Date().getTime();
           streamImg.style.display = 'block';
       }
       
       const logArea = safeGet('logAreaHelmet');
       if(logArea) logArea.innerHTML = `<div>${new Date().toLocaleTimeString()} - Helmet Detection Started</div>` + logArea.innerHTML;
    });
  }

  // "Stop / Clear" Button Logic
  if(clearBtn){
      clearBtn.addEventListener('click', () => {
          if(streamImg) {
              streamImg.src = ""; // Cut the connection
              streamImg.style.display = 'none';
          }
          if(preview) preview.style.display = 'block'; // Show placeholder
          
          // Clear URL params so refresh doesn't reload the video
          window.history.pushState({}, document.title, window.location.pathname);
          
          const logArea = safeGet('logAreaHelmet');
          if(logArea) logArea.innerHTML = `<div>${new Date().toLocaleTimeString()} - Detection Stopped</div>` + logArea.innerHTML;
      });
  }
}

// =========================
// Features Slideshow
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
  
  let currentSlide = 1; // Start with middle slide (index 1)
  let autoPlayInterval = null;
  const autoPlayDelay = 5000; // 5 seconds
  
  function updateSlideshow() {
    // Update track position
    track.style.transform = `translateX(-${currentSlide * 100}%)`;
    
    // Update active states
    slides.forEach((slide, index) => {
      slide.classList.toggle('active', index === currentSlide);
    });
    
    // Update dots
    dots.forEach((dot, index) => {
      dot.classList.toggle('active', index === currentSlide);
    });
  }
  
  function goToSlide(index) {
    if(index < 0) index = slides.length - 1;
    if(index >= slides.length) index = 0;
    currentSlide = index;
    updateSlideshow();
    resetAutoPlay();
  }
  
  function nextSlide() {
    goToSlide(currentSlide + 1);
  }
  
  function prevSlide() {
    goToSlide(currentSlide - 1);
  }
  
  function startAutoPlay() {
    autoPlayInterval = setInterval(nextSlide, autoPlayDelay);
  }
  
  function stopAutoPlay() {
    if(autoPlayInterval) {
      clearInterval(autoPlayInterval);
      autoPlayInterval = null;
    }
  }
  
  function resetAutoPlay() {
    stopAutoPlay();
    startAutoPlay();
  }
  
  // Navigation buttons
  if(nextBtn) nextBtn.addEventListener('click', nextSlide);
  if(prevBtn) prevBtn.addEventListener('click', prevSlide);
  
  // Dot navigation
  dots.forEach((dot, index) => {
    dot.addEventListener('click', () => goToSlide(index));
  });
  
  // Pause on hover
  slideshow.addEventListener('mouseenter', stopAutoPlay);
  slideshow.addEventListener('mouseleave', startAutoPlay);
  
  // Touch/swipe support
  let touchStartX = 0;
  let touchEndX = 0;
  
  track.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].screenX;
    stopAutoPlay();
  });
  
  track.addEventListener('touchend', (e) => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
    startAutoPlay();
  });
  
  function handleSwipe() {
    const swipeThreshold = 50;
    const diff = touchStartX - touchEndX;
    
    if(Math.abs(diff) > swipeThreshold) {
      if(diff > 0) {
        nextSlide(); // Swipe left - next
      } else {
        prevSlide(); // Swipe right - previous
      }
    }
  }
  
  // Initialize
  updateSlideshow();
  startAutoPlay();
}

// Init
function init(){
  try{ initSidebar(); }catch(e){}
  try{ initFatiguePage(); }catch(e){}
  try{ initHelmetPage(); }catch(e){}
  try{ initFeaturesSlideshow(); }catch(e){}
}

if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();