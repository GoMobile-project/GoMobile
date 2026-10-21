/**
 * GoMobile Learning Platform - Frontend Scripts
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Role switcher in login and register forms
  initRoleSwitcher();

  // 2. Interactive quiz engine
  initQuizEngine();

  // 3. QRIS payment simulation helper
  initPaymentHelper();
});

function initRoleSwitcher() {
  const roleButtons = document.querySelectorAll('.role-tab-btn');
  const roleInput = document.getElementById('roleInput');

  if (!roleButtons.length || !roleInput) return;

  roleButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      roleButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const selectedRole = btn.getAttribute('data-role');
      roleInput.value = selectedRole;

      // Update helper text if exists
      const roleHelper = document.getElementById('roleHelperText');
      if (roleHelper) {
        if (selectedRole === 'pengajar') {
          roleHelper.textContent = 'Mode Pengajar: Akses dashboard guru, bank soal, dan pemantauan siswa.';
        } else {
          roleHelper.textContent = 'Mode Siswa: Akses ruang belajar, latihan soal, dan ruang baca.';
        }
      }
    });
  });
}

function initQuizEngine() {
  const quizForm = document.getElementById('quizForm');
  if (!quizForm) return;

  const questions = document.querySelectorAll('.quiz-question-card');
  if (!questions.length) return;

  let currentQuestionIndex = 0;
  const totalQuestions = questions.length;

  const prevBtn = document.getElementById('prevQuestionBtn');
  const nextBtn = document.getElementById('nextQuestionBtn');
  const submitBtn = document.getElementById('submitQuizBtn');
  const currentIndicator = document.getElementById('currentQuestionNumber');
  const progressBar = document.getElementById('quizProgressBar');

  function updateQuestionView() {
    questions.forEach((q, idx) => {
      if (idx === currentQuestionIndex) {
        q.style.display = 'block';
      } else {
        q.style.display = 'none';
      }
    });

    if (currentIndicator) {
      currentIndicator.textContent = (currentQuestionIndex + 1);
    }

    if (progressBar) {
      const progressPercent = Math.round(((currentQuestionIndex + 1) / totalQuestions) * 100);
      progressBar.style.width = `${progressPercent}%`;
    }

    // Previous button state
    if (prevBtn) {
      if (currentQuestionIndex === 0) {
        prevBtn.style.visibility = 'hidden';
      } else {
        prevBtn.style.visibility = 'visible';
      }
    }

    // Next vs Submit button state
    if (currentQuestionIndex === totalQuestions - 1) {
      if (nextBtn) nextBtn.style.display = 'none';
      if (submitBtn) submitBtn.style.display = 'inline-flex';
    } else {
      if (nextBtn) nextBtn.style.display = 'inline-flex';
      if (submitBtn) submitBtn.style.display = 'none';
    }
  }

  // Handle option selection
  document.querySelectorAll('.option-item').forEach(item => {
    item.addEventListener('click', () => {
      const parentCard = item.closest('.quiz-question-card');
      parentCard.querySelectorAll('.option-item').forEach(opt => opt.classList.remove('selected'));
      item.classList.add('selected');

      const radio = item.querySelector('input[type="radio"]');
      if (radio) {
        radio.checked = true;
      }
    });
  });

  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      if (currentQuestionIndex < totalQuestions - 1) {
        currentQuestionIndex++;
        updateQuestionView();
        window.scrollTo({ top: 120, behavior: 'smooth' });
      }
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        updateQuestionView();
        window.scrollTo({ top: 120, behavior: 'smooth' });
      }
    });
  }

  // Initialize view
  updateQuestionView();
}

function initPaymentHelper() {
  const confirmBtn = document.getElementById('btnSimulatePay');
  if (!confirmBtn) return;

  confirmBtn.addEventListener('click', () => {
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = `
      <svg class="spin" style="width:20px;height:20px;margin-right:8px;animation:spin 1s linear infinite;" fill="none" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" style="opacity:0.25;"></circle>
        <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      Memverifikasi Pembayaran QRIS...
    `;
    
    setTimeout(() => {
      const form = document.getElementById('paymentConfirmForm');
      if (form) form.submit();
    }, 1200);
  });
}
