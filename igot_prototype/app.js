/**
 * iGOT Karmayogi Bharat Course Simulation — Standalone Interactive Logic
 * Fully decoupled prototype running on port 3003
 */

document.addEventListener('DOMContentLoaded', () => {
  // =========================================================================
  // 1. VIDEO PLAYER CONTROLS & STREAMING ENGINE
  // =========================================================================
  const video = document.getElementById('lecture-video');
  const videoContainer = document.getElementById('video-player-container');
  const splashOverlay = document.getElementById('video-splash-overlay');
  const btnPlayPause = document.getElementById('btn-play-pause');
  const iconPlay = document.getElementById('icon-play');
  const iconPause = document.getElementById('icon-pause');
  const btnRewind = document.getElementById('btn-rewind');
  const btnMute = document.getElementById('btn-mute');
  const iconVolHigh = document.getElementById('icon-vol-high');
  const iconVolMuted = document.getElementById('icon-vol-muted');
  const volumeSlider = document.getElementById('volume-slider');
  const videoScrubber = document.getElementById('video-scrubber');
  const scrubProgressFill = document.getElementById('scrub-progress-fill');
  const timeCounter = document.getElementById('video-time-counter');
  const speedChips = document.querySelectorAll('.speed-chip');
  const btnFullscreen = document.getElementById('btn-fullscreen');

  function formatTime(seconds) {
    if (isNaN(seconds) || seconds < 0) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  function updatePlayPauseUI(isPlaying) {
    if (isPlaying) {
      iconPlay.classList.add('hidden');
      iconPause.classList.remove('hidden');
      splashOverlay.classList.add('hidden');
    } else {
      iconPlay.classList.remove('hidden');
      iconPause.classList.add('hidden');
      splashOverlay.classList.remove('hidden');
    }
  }

  function togglePlay() {
    if (video.paused || video.ended) {
      video.play().catch(err => console.warn('Play error:', err));
    } else {
      video.pause();
    }
  }

  // Play / Pause event listeners
  if (btnPlayPause) btnPlayPause.addEventListener('click', togglePlay);
  if (splashOverlay) splashOverlay.addEventListener('click', togglePlay);
  if (video) {
    video.addEventListener('click', togglePlay);
    video.addEventListener('play', () => updatePlayPauseUI(true));
    video.addEventListener('pause', () => updatePlayPauseUI(false));
  }

  // Keyboard shortcut: Spacebar toggles play/pause
  window.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && e.target.tagName !== 'INPUT' && !isModalOpen()) {
      e.preventDefault();
      togglePlay();
    }
  });

  // Rewind 10 seconds
  if (btnRewind) {
    btnRewind.addEventListener('click', () => {
      video.currentTime = Math.max(0, video.currentTime - 10);
    });
  }

  // Volume & Mute
  if (btnMute) {
    btnMute.addEventListener('click', () => {
      video.muted = !video.muted;
      if (video.muted) {
        iconVolHigh.classList.add('hidden');
        iconVolMuted.classList.remove('hidden');
        volumeSlider.value = 0;
      } else {
        iconVolHigh.classList.remove('hidden');
        iconVolMuted.classList.add('hidden');
        video.volume = 0.85;
        volumeSlider.value = 0.85;
      }
    });
  }

  if (volumeSlider) {
    volumeSlider.addEventListener('input', (e) => {
      const val = parseFloat(e.target.value);
      video.volume = val;
      if (val === 0) {
        video.muted = true;
        iconVolHigh.classList.add('hidden');
        iconVolMuted.classList.remove('hidden');
      } else {
        video.muted = false;
        iconVolHigh.classList.remove('hidden');
        iconVolMuted.classList.add('hidden');
      }
    });
  }

  // Time & Scrubber Updates
  if (video) {
    video.addEventListener('loadedmetadata', () => {
      if (videoScrubber) videoScrubber.max = video.duration || 60;
      updateTimeDisplay();
    });

    video.addEventListener('timeupdate', () => {
      updateTimeDisplay();
      highlightActiveTimestamp(video.currentTime);
    });
  }

  function updateTimeDisplay() {
    const cur = video.currentTime || 0;
    const dur = video.duration || 60;
    if (timeCounter) {
      timeCounter.textContent = `${formatTime(cur)} / ${formatTime(dur)}`;
    }
    if (videoScrubber) {
      videoScrubber.value = cur;
    }
    if (scrubProgressFill && dur > 0) {
      scrubProgressFill.style.width = `${(cur / dur) * 100}%`;
    }
  }

  if (videoScrubber) {
    videoScrubber.addEventListener('input', (e) => {
      const targetTime = parseFloat(e.target.value);
      video.currentTime = targetTime;
      if (scrubProgressFill && video.duration > 0) {
        scrubProgressFill.style.width = `${(targetTime / video.duration) * 100}%`;
      }
    });
  }

  // Playback speed chips
  speedChips.forEach(chip => {
    chip.addEventListener('click', () => {
      speedChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      const rate = parseFloat(chip.dataset.speed);
      if (video) video.playbackRate = rate;
    });
  });

  // Fullscreen toggle
  if (btnFullscreen) {
    btnFullscreen.addEventListener('click', () => {
      if (!document.fullscreenElement) {
        if (videoContainer.requestFullscreen) {
          videoContainer.requestFullscreen();
        } else if (videoContainer.webkitRequestFullscreen) {
          videoContainer.webkitRequestFullscreen();
        }
      } else {
        if (document.exitFullscreen) {
          document.exitFullscreen();
        }
      }
    });
  }

  // Auto-play on launch with muted fallback
  setTimeout(() => {
    if (video) {
      video.muted = true;
      if (iconVolHigh && iconVolMuted) {
        iconVolHigh.classList.add('hidden');
        iconVolMuted.classList.remove('hidden');
        if (volumeSlider) volumeSlider.value = 0;
      }
      video.play().then(() => {
        updatePlayPauseUI(true);
      }).catch(e => {
        console.warn('Autoplay prevented:', e);
      });
    }
  }, 200);

  // =========================================================================
  // 1B. OFFICIAL iGOT COURSE VIDEO URL CLIPBOARD COPY
  // =========================================================================
  const btnCopyCourseUrl = document.getElementById('btn-copy-course-url');
  const copyBtnText = document.getElementById('copy-btn-text');
  const copyToast = document.getElementById('copy-toast');
  const COURSE_VIDEO_URL = "https://youtu.be/QIXUTsdj_oA";

  if (btnCopyCourseUrl) {
    btnCopyCourseUrl.addEventListener('click', async () => {
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(COURSE_VIDEO_URL);
        } else {
          const textarea = document.createElement('textarea');
          textarea.value = COURSE_VIDEO_URL;
          textarea.style.position = 'fixed';
          textarea.style.opacity = '0';
          document.body.appendChild(textarea);
          textarea.select();
          document.execCommand('copy');
          document.body.removeChild(textarea);
        }

        // Visual feedback on button
        btnCopyCourseUrl.classList.add('copied');
        if (copyBtnText) copyBtnText.textContent = '✓ Copied to Clipboard!';

        // Show animated toast
        if (copyToast) {
          copyToast.classList.remove('hidden');
          // Force reflow for CSS animation
          void copyToast.offsetWidth;
          copyToast.classList.add('show');

          setTimeout(() => {
            copyToast.classList.remove('show');
            setTimeout(() => {
              copyToast.classList.add('hidden');
            }, 300);
          }, 3500);
        }

        // Reset button after 3 seconds
        setTimeout(() => {
          btnCopyCourseUrl.classList.remove('copied');
          if (copyBtnText) copyBtnText.textContent = 'Copy iGOT Course URL';
        }, 3000);
      } catch (err) {
        console.error('Clipboard copy error:', err);
      }
    });
  }

  // =========================================================================
  // 2. TABBED STUDIO SWITCHER
  // =========================================================================
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const tabKey = btn.dataset.tab;
      const targetPane = document.getElementById(`tab-${tabKey}`);
      if (targetPane) targetPane.classList.add('active');
    });
  });

  // =========================================================================
  // 3. INTERACTIVE TIMESTAMPS
  // =========================================================================
  const timestampItems = document.querySelectorAll('.timestamp-item');

  timestampItems.forEach(item => {
    item.addEventListener('click', () => {
      const timeInSec = parseFloat(item.dataset.time);
      if (!isNaN(timeInSec) && video) {
        video.currentTime = timeInSec;
        video.play().catch(console.warn);
        highlightActiveTimestamp(timeInSec);
      }
    });
  });

  function highlightActiveTimestamp(currTime) {
    let activeIdx = 0;
    timestampItems.forEach((item, idx) => {
      const ts = parseFloat(item.dataset.time);
      if (currTime >= ts) {
        activeIdx = idx;
      }
    });
    timestampItems.forEach((item, idx) => {
      if (idx === activeIdx) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });
  }

  // =========================================================================
  // 4. COURSE CURRICULUM PLAYLIST (COURSERA / iGOT STYLE)
  // =========================================================================
  const playlistItems = document.querySelectorAll('.playlist-item');
  const moduleTimeStarts = [0, 15, 30, 45, 55];

  playlistItems.forEach(item => {
    item.addEventListener('click', () => {
      playlistItems.forEach(p => {
        p.classList.remove('active');
        const badge = p.querySelector('.item-icon-col');
        const idx = p.dataset.modIdx;
        badge.innerHTML = `<div class="num-badge">${parseInt(idx) + 1}</div>`;
      });

      item.classList.add('active');
      const activeBadge = item.querySelector('.item-icon-col');
      activeBadge.innerHTML = `<div class="active-play-badge"><svg class="icon-xs" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg></div>`;

      const modIdx = parseInt(item.dataset.modIdx);
      if (video && moduleTimeStarts[modIdx] !== undefined) {
        video.currentTime = moduleTimeStarts[modIdx];
        video.play().catch(console.warn);
      }
    });
  });

  // =========================================================================
  // 5. 15-MCQ DIAGNOSTIC ASSESSMENT ENGINE (GYANSETU SIMULATION)
  // =========================================================================
  const assessmentModal = document.getElementById('assessment-modal');
  const closeModalBtn = document.getElementById('close-modal-btn');
  const btnNextQuestion = document.getElementById('btn-next-question');
  const btnRestartAssessment = document.getElementById('btn-restart-assessment');
  const btnFinishModal = document.getElementById('btn-finish-modal');

  // Launch buttons across page
  const launchTriggers = [
    document.getElementById('open-assessment-btn-header'),
    document.getElementById('hero-diagnostic-trigger'),
    document.getElementById('evaluate-banner-btn'),
    document.getElementById('sidebar-launch-assessment-btn')
  ];

  function isModalOpen() {
    return assessmentModal && !assessmentModal.classList.contains('hidden');
  }

  function openModal() {
    if (assessmentModal) {
      assessmentModal.classList.remove('hidden');
      resetAssessment();
    }
  }

  function closeModal() {
    if (assessmentModal) {
      assessmentModal.classList.add('hidden');
    }
  }

  launchTriggers.forEach(btn => {
    if (btn) btn.addEventListener('click', openModal);
  });

  if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
  if (btnFinishModal) btnFinishModal.addEventListener('click', closeModal);
  if (btnRestartAssessment) btnRestartAssessment.addEventListener('click', resetAssessment);

  // Close on outside backdrop click
  if (assessmentModal) {
    assessmentModal.addEventListener('click', (e) => {
      if (e.target === assessmentModal) closeModal();
    });
  }

  // 15 Calibrated Questions based on Steve Brunton Lecture & MoSPI Cadre Standard
  const questionsBank = [
    {
      subskill: "Inferential vs. Descriptive Statistics",
      prompt: "Which statement accurately distinguishes inferential statistics from descriptive statistics in official survey administration?",
      options: [
        "Descriptive statistics summarizes collected sample data, whereas inferential statistics makes predictions about population parameters under uncertainty.",
        "Inferential statistics only applies to census surveys where every population unit is measured.",
        "Descriptive statistics derives posterior probability distributions using Markov Chain Monte Carlo.",
        "Both are identical terms used interchangeably in MoSPI field manuals."
      ],
      correct: 0,
      explanation: "Descriptive statistics organizes and summarizes observed data, while inferential statistics uses sample data to draw probabilistic conclusions about an unobserved population.",
      misconception: "Confuses summary statistics (mean, variance) with inferential modeling (estimation, confidence intervals, hypothesis testing)."
    },
    {
      subskill: "Continuous Probability Models",
      prompt: "In a continuous probability density function (PDF) f(x), what does the area under the curve between points a and b represent?",
      options: [
        "The exact value of the random variable at the mean.",
        "The probability P(a ≤ X ≤ b) that the random variable falls within that specific interval.",
        "The cumulative variance of the population divided by degrees of freedom.",
        "The total sample size of the NSS survey round."
      ],
      correct: 1,
      explanation: "For a continuous PDF, probability is given by the integral between boundaries: P(a ≤ X ≤ b) = ∫ f(x) dx. The total area equals 1.0.",
      misconception: "Assumes f(x) evaluates directly to probability P(X=x), which is zero for any exact point in a continuous distribution."
    },
    {
      subskill: "Central Limit Theorem (CLT)",
      prompt: "According to the Central Limit Theorem, what happens to the sampling distribution of the sample mean as sample size n increases?",
      options: [
        "It becomes highly skewed and converges toward a Cauchy distribution.",
        "It approaches a normal distribution regardless of the underlying population shape, with variance equal to σ² / n.",
        "Its variance increases proportionally with the square root of n.",
        "It loses all asymptotic properties unless the parent distribution is strictly Gaussian."
      ],
      correct: 1,
      explanation: "The CLT establishes that the distribution of sample means approaches N(μ, σ²/n) as n → ∞, which is the mathematical foundation for survey estimation.",
      misconception: "Believes the CLT requires the underlying population itself to be normally distributed."
    },
    {
      subskill: "Sampling Variance & Standard Error",
      prompt: "How does the Standard Error (SE) of the sample mean scale with an increase in sample size n?",
      options: [
        "SE is inversely proportional to the square root of n (SE = σ / √n).",
        "SE increases linearly with n.",
        "SE remains constant because population variance σ² is fixed.",
        "SE doubles whenever n is quadrupled."
      ],
      correct: 0,
      explanation: "Standard Error equals σ / √n. Quadrupling the sample size cuts the standard error in half, illustrating the diminishing return of sample expansion.",
      misconception: "Confuses population standard deviation (σ) with sample mean standard error (σ/√n)."
    },
    {
      subskill: "Stratified Sampling: Neyman Allocation",
      prompt: "Under Neyman Optimum Allocation, how are sample sizes allocated across survey strata?",
      options: [
        "Equally among all strata regardless of size or variability.",
        "Proportionally to the product of stratum size Nh and stratum standard deviation Sh.",
        "Exclusively to strata with the lowest survey operational costs.",
        "Inversely proportional to stratum variance."
      ],
      correct: 1,
      explanation: "Neyman allocation minimizes estimation variance for a fixed sample size by assigning nh ∝ Nh × Sh, giving larger shares to larger and more variable strata.",
      misconception: "Confuses simple proportional allocation (nh ∝ Nh) with variance-minimizing Neyman allocation (nh ∝ Nh × Sh)."
    },
    {
      subskill: "Hypothesis Testing: Type I Error",
      prompt: "What is a Type I Error (α) in classical statistical decision theory?",
      options: [
        "Failing to reject the null hypothesis when it is false.",
        "Rejecting the null hypothesis when it is actually true (false positive).",
        "The probability of computing an arithmetic error in sum of squares.",
        "Accepting the alternative hypothesis when sample size is too large."
      ],
      correct: 1,
      explanation: "Type I error occurs when a true null hypothesis is erroneously rejected. The maximum allowable rate is the significance level α (commonly 0.05 or 0.01).",
      misconception: "Confuses Type I error (rejecting true null) with Type II error (accepting false null)."
    },
    {
      subskill: "Hypothesis Testing: Statistical Power",
      prompt: "The power of a statistical test is mathematically defined as:",
      options: [
        "1 − α (Confidence Level)",
        "1 − β (Probability of correctly rejecting a false null hypothesis)",
        "The p-value multiplied by the degrees of freedom",
        "The ratio of explained sum of squares to total sum of squares"
      ],
      correct: 1,
      explanation: "Statistical power equals 1 − β, representing the test's ability to detect an effect when a true effect exists.",
      misconception: "Confuses power (1 − β) with the confidence coefficient (1 − α)."
    },
    {
      subskill: "Maximum Likelihood Estimation (MLE)",
      prompt: "The principle of Maximum Likelihood Estimation selects parameter estimates that:",
      options: [
        "Minimize the sum of squared deviations from the median.",
        "Maximize the likelihood function L(θ | X), making observed data most probable under the model.",
        "Equalize between-group variance with within-group variance.",
        "Set the prior distribution equal to uniform noise."
      ],
      correct: 1,
      explanation: "MLE identifies parameter values θ that maximize the joint probability density/mass function of the observed sample.",
      misconception: "Confuses MLE with Ordinary Least Squares (OLS) or Method of Moments."
    },
    {
      subskill: "Covariance & Correlation",
      prompt: "What is the key advantage of Pearson's correlation coefficient r over raw covariance Cov(X, Y)?",
      options: [
        "r is scale-invariant and bounded strictly between −1.0 and +1.0.",
        "r can only be computed for non-linear relationships.",
        "r does not require pairs of observations.",
        "Covariance is always positive, whereas r can be negative."
      ],
      correct: 0,
      explanation: "Correlation normalizes covariance by dividing by the product of individual standard deviations (r = Cov(X,Y)/(σX σY)), making it dimensionless.",
      misconception: "Assumes covariance values are bounded between −1 and +1."
    },
    {
      subskill: "Ordinary Least Squares: Homoscedasticity",
      prompt: "In regression diagnostics, what does the Gauss-Markov assumption of 'Homoscedasticity' mean?",
      options: [
        "Residuals have constant variance across all levels of the predictor variables.",
        "All predictor variables are orthogonal to each other.",
        "The dependent variable follows an exact Poisson distribution.",
        "Regression coefficients sum to unity."
      ],
      correct: 0,
      explanation: "Homoscedasticity requires Var(εi | Xi) = σ² for all observations. When violated (heteroscedasticity), OLS standard errors become biased.",
      misconception: "Confuses constant error variance (homoscedasticity) with lack of multicollinearity."
    },
    {
      subskill: "Survey Design Effect (DEFF)",
      prompt: "In multi-stage cluster survey sampling, what does a Design Effect (DEFF) greater than 1.0 indicate?",
      options: [
        "The complex survey design has smaller variance than simple random sampling (SRS).",
        "Clustering has increased variance compared to an SRS of the same sample size due to intra-cluster correlation.",
        "The survey has achieved 100% operational efficiency.",
        "The sample size must be halved to preserve precision."
      ],
      correct: 1,
      explanation: "DEFF = Var(complex) / Var(SRS). In cluster sampling, units within clusters resemble each other (ρ > 0), causing DEFF > 1.0 and reducing effective sample size.",
      misconception: "Assumes cluster sampling inherently increases statistical precision over simple random sampling."
    },
    {
      subskill: "Non-Response Imputation",
      prompt: "Which imputation method substitutes a missing value with the observed value of a respondent matching similar demographic and economic characteristics?",
      options: [
        "Mean imputation across the entire national pool.",
        "Hot-deck donor imputation.",
        "Zero-filling imputation.",
        "Deterministic Laplace deflation."
      ],
      correct: 1,
      explanation: "Hot-deck imputation finds an eligible donor respondent within the same survey round and imputation cell to replace missing values.",
      misconception: "Believes mean substitution preserves variance and joint distribution properties."
    },
    {
      subskill: "Index Numbers: Laspeyres vs. Paasche",
      prompt: "Why does the base-weighted Laspeyres price index typically exhibit an upward substitution bias?",
      options: [
        "It uses current-period quantity weights that adjust immediately to price changes.",
        "It holds base-period consumption baskets fixed, ignoring consumer shifts away from items with rising relative prices.",
        "It divides price relatives by geometric mean factors.",
        "It applies arithmetic deflation to wholesale goods."
      ],
      correct: 1,
      explanation: "Laspeyres uses fixed base-year quantities Q0. Consumers naturally substitute away from items that become relatively expensive, so Laspeyres overstates inflation.",
      misconception: "Confuses Laspeyres (base-weighted, upward bias) with Paasche (current-weighted, downward bias)."
    },
    {
      subskill: "National Accounts: Real vs. Nominal GDP",
      prompt: "How is Real Gross Domestic Product (GDP) derived from Nominal GDP?",
      options: [
        "By multiplying Nominal GDP by the Consumer Price Index.",
        "By deflating Nominal GDP using the GDP Deflator to isolate volume growth from price inflation.",
        "By subtracting total government subsidies and import duties.",
        "By adding intermediate consumption to gross output."
      ],
      correct: 1,
      explanation: "Real GDP = (Nominal GDP / GDP Deflator) × 100. It measures the physical volume of goods and services produced at constant base-period prices.",
      misconception: "Believes Nominal GDP already accounts for purchasing power parity and price changes."
    },
    {
      subskill: "Bayesian Knowledge Tracing (BKT)",
      prompt: "In cognitive mastery models (BKT), how does an observed slip probability P(S) influence the mastery update after an incorrect response?",
      options: [
        "A non-zero slip probability prevents the estimated mastery probability from dropping instantaneously to zero when an error occurs.",
        "It sets the guessing parameter P(G) to 1.0 automatically.",
        "It guarantees the learner is permanently classified as a master.",
        "It freezes all subsequent learning parameter updates."
      ],
      correct: 0,
      explanation: "In BKT, P(S) accounts for careless mistakes by knowledgeable learners. It prevents a single slip from completely erasing accumulated mastery evidence.",
      misconception: "Assumes deterministic evaluation where a single mistake always proves complete absence of skill."
    }
  ];

  // Assessment State Machine
  let currentQuestionIdx = 0;
  let scoreCount = 0;
  let isAnswerSubmitted = false;

  const assessmentBodyActive = document.getElementById('assessment-body-active');
  const assessmentBodyResults = document.getElementById('assessment-body-results');
  const modalActiveFooter = document.getElementById('modal-active-footer');
  const qProgressLabel = document.getElementById('question-progress-label');
  const qScoreCounter = document.getElementById('question-score-counter');
  const qProgressFill = document.getElementById('q-progress-fill');
  const qSubskillPill = document.getElementById('q-subskill-pill');
  const qPromptText = document.getElementById('q-prompt-text');
  const optionsContainer = document.getElementById('options-container');
  const feedbackBox = document.getElementById('feedback-box');
  const feedbackTitle = document.getElementById('feedback-title');
  const feedbackExplanation = document.getElementById('feedback-explanation');
  const misconceptionCallout = document.getElementById('misconception-callout');
  const misconceptionText = document.getElementById('misconception-text');

  // Results elements
  const resultsPct = document.getElementById('results-pct');
  const resultsScoreCircle = document.getElementById('results-score-circle');
  const resultsHeadline = document.getElementById('results-headline');
  const resultsSubtext = document.getElementById('results-subtext');
  const kpiCorrectCount = document.getElementById('kpi-correct-count');
  const kpiProgressionStatus = document.getElementById('kpi-progression-status');

  function resetAssessment() {
    currentQuestionIdx = 0;
    scoreCount = 0;
    isAnswerSubmitted = false;

    if (assessmentBodyActive) assessmentBodyActive.classList.remove('hidden');
    if (assessmentBodyResults) assessmentBodyResults.classList.add('hidden');
    if (modalActiveFooter) modalActiveFooter.classList.remove('hidden');

    renderQuestion();
  }

  function renderQuestion() {
    isAnswerSubmitted = false;
    if (btnNextQuestion) {
      btnNextQuestion.classList.add('disabled');
      btnNextQuestion.disabled = true;
      btnNextQuestion.textContent = (currentQuestionIdx === questionsBank.length - 1) ? 'Finish Assessment →' : 'Next Question →';
    }

    if (feedbackBox) feedbackBox.classList.add('hidden');
    if (misconceptionCallout) misconceptionCallout.classList.add('hidden');

    const q = questionsBank[currentQuestionIdx];
    const totalQ = questionsBank.length;

    // Update progress counters
    if (qProgressLabel) qProgressLabel.textContent = `Question ${currentQuestionIdx + 1} of ${totalQ}`;
    if (qScoreCounter) qScoreCounter.textContent = `Score: ${scoreCount} / ${currentQuestionIdx}`;
    if (qProgressFill) qProgressFill.style.width = `${((currentQuestionIdx + 1) / totalQ) * 100}%`;

    // Update prompt
    if (qSubskillPill) qSubskillPill.textContent = `Sub-Skill: ${q.subskill}`;
    if (qPromptText) qPromptText.textContent = q.prompt;

    // Render options
    if (optionsContainer) {
      optionsContainer.innerHTML = '';
      const letters = ['A', 'B', 'C', 'D'];
      q.options.forEach((optText, optIdx) => {
        const optCard = document.createElement('div');
        optCard.className = 'option-card';
        optCard.dataset.idx = optIdx;
        optCard.innerHTML = `
          <div class="opt-letter">${letters[optIdx]}</div>
          <div class="opt-text">${optText}</div>
        `;
        optCard.addEventListener('click', () => handleOptionSelect(optIdx, optCard));
        optionsContainer.appendChild(optCard);
      });
    }
  }

  function handleOptionSelect(selectedIdx, clickedCard) {
    if (isAnswerSubmitted) return;
    isAnswerSubmitted = true;

    const q = questionsBank[currentQuestionIdx];
    const isCorrect = (selectedIdx === q.correct);
    if (isCorrect) scoreCount++;

    // Lock option cards and apply colors
    const allCards = optionsContainer.querySelectorAll('.option-card');
    allCards.forEach(card => {
      card.classList.add('locked');
      const idx = parseInt(card.dataset.idx);
      if (idx === q.correct) {
        card.classList.add('correct');
      } else if (idx === selectedIdx && !isCorrect) {
        card.classList.add('incorrect');
      }
    });

    // Display feedback box
    if (feedbackBox) {
      feedbackBox.classList.remove('hidden', 'correct-box', 'incorrect-box');
      if (isCorrect) {
        feedbackBox.classList.add('correct-box');
        if (feedbackTitle) feedbackTitle.textContent = '✓ Correct Answer!';
        if (misconceptionCallout) misconceptionCallout.classList.add('hidden');
      } else {
        feedbackBox.classList.add('incorrect-box');
        if (feedbackTitle) feedbackTitle.textContent = '✗ Incorrect Choice';
        if (misconceptionCallout) {
          misconceptionCallout.classList.remove('hidden');
          if (misconceptionText) misconceptionText.textContent = q.misconception;
        }
      }
      if (feedbackExplanation) feedbackExplanation.textContent = q.explanation;
    }

    // Enable next button
    if (btnNextQuestion) {
      btnNextQuestion.classList.remove('disabled');
      btnNextQuestion.disabled = false;
    }
  }

  if (btnNextQuestion) {
    btnNextQuestion.addEventListener('click', () => {
      if (currentQuestionIdx < questionsBank.length - 1) {
        currentQuestionIdx++;
        renderQuestion();
      } else {
        renderResults();
      }
    });
  }

  function renderResults() {
    if (assessmentBodyActive) assessmentBodyActive.classList.add('hidden');
    if (modalActiveFooter) modalActiveFooter.classList.add('hidden');
    if (assessmentBodyResults) assessmentBodyResults.classList.remove('hidden');

    const totalQ = questionsBank.length;
    const finalPct = Math.round((scoreCount / totalQ) * 100);
    const passed = finalPct >= 70;

    if (resultsPct) resultsPct.textContent = `${finalPct}%`;
    if (kpiCorrectCount) kpiCorrectCount.textContent = `${scoreCount} / ${totalQ}`;

    if (resultsScoreCircle) {
      resultsScoreCircle.classList.remove('passed', 'retry');
      resultsScoreCircle.classList.add(passed ? 'passed' : 'retry');
    }

    if (passed) {
      if (resultsHeadline) resultsHeadline.textContent = 'Qualification Standard Achieved! 🎉';
      if (resultsSubtext) {
        resultsSubtext.textContent = `Score of ${finalPct}% exceeds the official MoSPI 70% threshold. Tier 2: Application (Calculations & Formulations) is now UNLOCKED for this candidate.`;
      }
      if (kpiProgressionStatus) {
        kpiProgressionStatus.textContent = 'Tier 2 Unlocked';
        kpiProgressionStatus.style.color = '#15803d';
      }
    } else {
      if (resultsHeadline) resultsHeadline.textContent = 'Review & Practice Recommended';
      if (resultsSubtext) {
        resultsSubtext.textContent = `Score of ${finalPct}% is below the mandated 70% qualification benchmark. Please review the video timestamps and MoSPI handbooks before re-attempting Tier 1.`;
      }
      if (kpiProgressionStatus) {
        kpiProgressionStatus.textContent = 'Tier 1 Review Needed';
        kpiProgressionStatus.style.color = '#ea580c';
      }
    }
  }

  // Accessibility modal shortcut (Alerts accessibility status)
  const accessibilityBtn = document.getElementById('accessibility-btn');
  if (accessibilityBtn) {
    accessibilityBtn.addEventListener('click', () => {
      alert('iGOT Karmayogi Bharat Accessibility Suite\n• WCAG 2.1 Level AA Compliant\n• High Contrast Palette Active\n• Keyboard Navigation Supported (Space: Play/Pause)\n• Video Captions & Audio Descriptions Enabled');
    });
  }
});
