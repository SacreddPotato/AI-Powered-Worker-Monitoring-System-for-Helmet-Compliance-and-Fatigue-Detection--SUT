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

function init(){
  try{ initSidebar(); }catch(e){}
  try{ initFatiguePage(); }catch(e){}
  try{ initHelmetPage(); }catch(e){}
  try{ initFeaturesSlideshow(); }catch(e){}
  try{ initFaqPage(); }catch(e){} // Added this
}

if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();