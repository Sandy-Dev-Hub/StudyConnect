/* ===================================================
   StudyConnect — Main JavaScript
   =================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initScrollAnimations();
    initVoting();
    initAcceptAnswer();
    initLiveSearch();
    initMarkdownPreview();
    initImagePreview();
    initDeleteConfirmation();
    initPasswordToggle();
    initAutoCloseAlerts();
    initNavbarScrollEffect();
    initCustomDropdowns();
    initCommunityDropdown();
    initCommunityBadgeSync();
});

/* =================================================
   SCROLL ANIMATIONS (IntersectionObserver)
   ================================================= */
function initScrollAnimations() {
    const elements = document.querySelectorAll('.animate-on-scroll');
    if (!elements.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.classList.add('animate-visible');
                }, index * 60);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    elements.forEach(el => observer.observe(el));
}

/* =================================================
   AJAX VOTING
   ================================================= */
function initVoting() {
    document.querySelectorAll('.vote-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            if (btn.disabled) return;

            const answerId = parseInt(btn.dataset.answerId);
            const voteValue = parseInt(btn.dataset.value);
            const scoreEl = document.getElementById(`score-${answerId}`);

            if (!answerId || !scoreEl) return;

            // Optimistic UI update
            const wasVoted = btn.classList.contains('voted');
            const siblingClass = voteValue === 1 ? '.vote-down' : '.vote-up';
            const sibling = btn.parentElement.querySelector(siblingClass);

            try {
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content ||
                    document.querySelector('input[name="csrf_token"]')?.value || '';

                const response = await fetch('/answers/vote', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({ answer_id: answerId, value: voteValue })
                });

                const data = await response.json();

                if (!response.ok) {
                    showToast('error', 'Vote Failed', data.error || 'Could not process vote.');
                    return;
                }

                // Update score
                scoreEl.textContent = data.score;

                // Update button states
                if (wasVoted) {
                    btn.classList.remove('voted');
                } else {
                    btn.classList.add('voted');
                    if (sibling) sibling.classList.remove('voted');
                }

                // Update navbar points
                if (data.user_points !== undefined) {
                    const navPointsEl = document.getElementById('nav-points-value');
                    if (navPointsEl) navPointsEl.textContent = data.user_points;
                }

                // Show points toast
                if (data.points_awarded > 0) {
                    showToast('points', `+${data.points_awarded} Points`, 'Upvote awarded!');
                } else if (data.points_awarded < 0) {
                    showToast('info', `${data.points_awarded} Points`, 'Points adjusted.');
                }

            } catch (err) {
                showToast('error', 'Error', 'Network error. Please try again.');
            }
        });
    });
}

/* =================================================
   ACCEPT ANSWER
   ================================================= */
function initAcceptAnswer() {
    document.querySelectorAll('.accept-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const answerId = parseInt(btn.dataset.answerId);
            if (!answerId) return;

            try {
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content ||
                    document.querySelector('input[name="csrf_token"]')?.value || '';

                const response = await fetch(`/answers/accept/${answerId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const data = await response.json();

                if (!response.ok) {
                    showToast('error', 'Error', data.error || 'Could not accept answer.');
                    return;
                }

                // Toggle accepted state visually
                const answerCard = document.getElementById(`answer-${answerId}`);
                const icon = btn.querySelector('i');

                if (data.is_accepted) {
                    btn.classList.add('accepted');
                    if (icon) {
                        icon.classList.remove('bi-check-circle');
                        icon.classList.add('bi-check-circle-fill');
                    }
                    if (answerCard) answerCard.classList.add('answer-accepted');

                    // Remove accepted from other answers
                    document.querySelectorAll('.accept-btn.accepted').forEach(otherBtn => {
                        if (otherBtn !== btn) {
                            otherBtn.classList.remove('accepted');
                            const otherIcon = otherBtn.querySelector('i');
                            if (otherIcon) {
                                otherIcon.classList.remove('bi-check-circle-fill');
                                otherIcon.classList.add('bi-check-circle');
                            }
                            const otherCard = otherBtn.closest('.answer-card');
                            if (otherCard) otherCard.classList.remove('answer-accepted');
                        }
                    });

                    showToast('points', '+25 Points', 'Answer accepted!');
                } else {
                    btn.classList.remove('accepted');
                    if (icon) {
                        icon.classList.remove('bi-check-circle-fill');
                        icon.classList.add('bi-check-circle');
                    }
                    if (answerCard) answerCard.classList.remove('answer-accepted');
                    showToast('info', 'Answer Unaccepted', 'The answer has been unaccepted.');
                }

            } catch (err) {
                showToast('error', 'Error', 'Network error. Please try again.');
            }
        });
    });
}

/* =================================================
   LIVE SEARCH
   ================================================= */
function initLiveSearch() {
    const input = document.getElementById('nav-search-input');
    const dropdown = document.getElementById('search-results-dropdown');
    if (!input || !dropdown) return;

    let debounceTimer;
    let selectedIndex = -1;

    function updateSelection() {
        const items = dropdown.querySelectorAll('.search-result-item[href]');
        items.forEach((item, index) => {
            if (index === selectedIndex) {
                item.classList.add('focused');
                item.setAttribute('aria-selected', 'true');
                input.setAttribute('aria-activedescendant', `search-item-${index}`);
                item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            } else {
                item.classList.remove('focused');
                item.setAttribute('aria-selected', 'false');
            }
        });
        if (selectedIndex === -1) {
            input.removeAttribute('aria-activedescendant');
        }
    }

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        const query = input.value.trim();

        if (query.length < 2) {
            dropdown.classList.add('d-none');
            dropdown.innerHTML = '';
            input.setAttribute('aria-expanded', 'false');
            selectedIndex = -1;
            return;
        }

        debounceTimer = setTimeout(async () => {
            try {
                const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();

                if (data.results.length === 0) {
                    dropdown.innerHTML = `
                        <div class="search-empty-state" role="status">
                            <i class="bi bi-search"></i>
                            <span>No matching questions found</span>
                        </div>
                    `;
                    dropdown.classList.remove('d-none');
                    input.setAttribute('aria-expanded', 'true');
                    selectedIndex = -1;
                    return;
                }

                dropdown.innerHTML = data.results.map((q, idx) => `
                    <a href="/questions/${q.id}" id="search-item-${idx}" class="search-result-item" role="option" aria-selected="false">
                        <div class="search-result-title">${escapeHtml(q.title)}</div>
                        <div class="search-result-meta">
                            <span class="tag tag-subject">${escapeHtml(q.subject_tag)}</span>
                            <span class="ms-2">${q.answer_count} answer${q.answer_count !== 1 ? 's' : ''}</span>
                            <span class="ms-2">${q.time_ago}</span>
                            ${q.is_resolved ? '<span class="ms-2 text-success" title="Resolved"><i class="bi bi-check-circle-fill"></i></span>' : ''}
                        </div>
                    </a>
                `).join('');
                dropdown.classList.remove('d-none');
                input.setAttribute('aria-expanded', 'true');
                selectedIndex = -1;

                const items = dropdown.querySelectorAll('.search-result-item[href]');
                items.forEach((item, index) => {
                    item.addEventListener('mouseenter', () => {
                        selectedIndex = index;
                        updateSelection();
                    });
                });
            } catch (err) {
                dropdown.classList.add('d-none');
                input.setAttribute('aria-expanded', 'false');
                selectedIndex = -1;
            }
        }, 300);
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.add('d-none');
            input.setAttribute('aria-expanded', 'false');
            selectedIndex = -1;
        }
    });

    // Handle keyboard navigation
    input.addEventListener('keydown', (e) => {
        const items = dropdown.querySelectorAll('.search-result-item[href]');

        if (e.key === 'ArrowDown') {
            if (dropdown.classList.contains('d-none') || items.length === 0) return;
            e.preventDefault();
            selectedIndex = (selectedIndex + 1) % items.length;
            updateSelection();
        } else if (e.key === 'ArrowUp') {
            if (dropdown.classList.contains('d-none') || items.length === 0) return;
            e.preventDefault();
            selectedIndex = (selectedIndex - 1 + items.length) % items.length;
            updateSelection();
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (selectedIndex >= 0 && selectedIndex < items.length) {
                items[selectedIndex].click();
            } else {
                const query = input.value.trim();
                if (query.length >= 2) {
                    window.location.href = `/questions/?q=${encodeURIComponent(query)}`;
                }
            }
        } else if (e.key === 'Escape') {
            dropdown.classList.add('d-none');
            input.setAttribute('aria-expanded', 'false');
            selectedIndex = -1;
        }
    });
}

/* =================================================
   MARKDOWN PREVIEW
   ================================================= */
function initMarkdownPreview() {
    // Question body preview
    setupPreviewToggle('preview-toggle', 'body', 'markdown-preview');
    // Answer body preview
    setupPreviewToggle('answer-preview-toggle', 'answer-body', 'answer-markdown-preview');
}

function setupPreviewToggle(toggleId, textareaId, previewId) {
    const toggle = document.getElementById(toggleId);
    const textarea = document.getElementById(textareaId);
    const preview = document.getElementById(previewId);

    if (!toggle || !textarea || !preview) return;

    let showingPreview = false;

    toggle.addEventListener('click', () => {
        showingPreview = !showingPreview;

        if (showingPreview) {
            const text = textarea.value;
            // Simple client-side markdown rendering
            preview.innerHTML = simpleMarkdown(text);
            preview.classList.remove('d-none');
            textarea.classList.add('d-none');
            toggle.innerHTML = '<i class="bi bi-pencil me-1"></i>Edit';
        } else {
            preview.classList.add('d-none');
            textarea.classList.remove('d-none');
            toggle.innerHTML = '<i class="bi bi-eye me-1"></i>Preview';
        }
    });
}

function simpleMarkdown(text) {
    if (!text) return '<p class="text-muted">Nothing to preview</p>';

    let html = escapeHtml(text);

    // Code blocks
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    // Italic
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    // Headers
    html = html.replace(/^### (.+)$/gm, '<h5>$1</h5>');
    html = html.replace(/^## (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^# (.+)$/gm, '<h3>$1</h3>');
    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');

    return `<div class="markdown-body"><p>${html}</p></div>`;
}

/* =================================================
   IMAGE PREVIEW
   ================================================= */
function initImagePreview() {
    const input = document.getElementById('image');
    const previewContainer = document.getElementById('image-preview-container');
    const previewImg = document.getElementById('image-preview');
    const removeBtn = document.getElementById('image-remove');

    if (!input || !previewContainer || !previewImg) return;

    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (event) => {
                previewImg.src = event.target.result;
                previewContainer.classList.remove('d-none');
            };
            reader.readAsDataURL(file);
        } else {
            previewContainer.classList.add('d-none');
        }
    });

    if (removeBtn) {
        removeBtn.addEventListener('click', () => {
            input.value = '';
            previewContainer.classList.add('d-none');
        });
    }
}

/* =================================================
   DELETE CONFIRMATION
   ================================================= */
function initDeleteConfirmation() {
    document.querySelectorAll('.delete-form').forEach(form => {
        form.addEventListener('submit', (e) => {
            const message = form.dataset.confirm || 'Are you sure?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

/* =================================================
   PASSWORD TOGGLE
   ================================================= */
function initPasswordToggle() {
    document.querySelectorAll('.toggle-password').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.dataset.target;
            const input = document.getElementById(targetId);
            if (!input) return;

            const icon = btn.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        });
    });
}

/* =================================================
   TOAST NOTIFICATION SYSTEM
   ================================================= */
function showToast(type, title, message, duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const iconMap = {
        success: 'bi-check-circle-fill toast-success',
        points: 'bi-star-fill toast-points',
        error: 'bi-exclamation-triangle-fill toast-error',
        info: 'bi-info-circle-fill toast-info',
    };

    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.innerHTML = `
        <div class="toast-icon ${iconMap[type] || iconMap.info}">
            <i class="bi ${iconMap[type]?.split(' ')[0] || 'bi-info-circle-fill'}"></i>
        </div>
        <div class="toast-body">
            <strong>${escapeHtml(title)}</strong>
            <small>${escapeHtml(message)}</small>
        </div>
        <button class="toast-close" aria-label="Close">&times;</button>
    `;

    container.appendChild(toast);

    // Close button
    toast.querySelector('.toast-close').addEventListener('click', () => {
        removeToast(toast);
    });

    // Auto-remove
    setTimeout(() => removeToast(toast), duration);
}

function removeToast(toast) {
    if (toast.classList.contains('toast-exit')) return;
    toast.classList.add('toast-exit');
    setTimeout(() => toast.remove(), 300);
}

/* =================================================
   AUTO-CLOSE FLASH ALERTS
   ================================================= */
function initAutoCloseAlerts() {
    document.querySelectorAll('.flash-container .alert').forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });
}

/* =================================================
   NAVBAR SCROLL EFFECT
   ================================================= */
function initNavbarScrollEffect() {
    const nav = document.querySelector('.glass-nav');
    if (!nav) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            nav.style.borderBottom = '1px solid rgba(108, 99, 255, 0.2)';
            nav.style.background = 'rgba(10, 10, 26, 0.92)';
        } else {
            nav.style.borderBottom = '1px solid rgba(255, 255, 255, 0.08)';
            nav.style.background = 'rgba(10, 10, 26, 0.8)';
        }
    });
}

/* =================================================
   COMMUNITY DROPDOWN & BADGE SYNC
   ================================================= */
function initCommunityDropdown() {
    const dropdown = document.querySelector('.community-dropdown');
    if (!dropdown) return;
    const toggleBtn = dropdown.querySelector('.dropdown-toggle');
    const menu = dropdown.querySelector('.dropdown-menu');
    if (!toggleBtn || !menu) return;

    let hoverTimeout;

    dropdown.addEventListener('mouseenter', () => {
        if (window.innerWidth >= 992) {
            clearTimeout(hoverTimeout);
            menu.classList.add('show');
            toggleBtn.setAttribute('aria-expanded', 'true');
        }
    });

    dropdown.addEventListener('mouseleave', () => {
        if (window.innerWidth >= 992) {
            hoverTimeout = setTimeout(() => {
                menu.classList.remove('show');
                toggleBtn.setAttribute('aria-expanded', 'false');
            }, 150);
        }
    });
}

function initCommunityBadgeSync() {
    const unreadBadge = document.getElementById('navbar-unread-badge');
    const indicator = document.getElementById('community-nav-indicator');
    if (!unreadBadge || !indicator) return;

    const observer = new MutationObserver(() => {
        const count = parseInt(unreadBadge.textContent) || 0;
        const isHidden = unreadBadge.classList.contains('d-none') || count === 0;
        if (!isHidden) {
            indicator.classList.remove('d-none');
        }
    });
    observer.observe(unreadBadge, { attributes: true, characterData: true, subtree: true });
}

/* =================================================
   UTILITY FUNCTIONS
   ================================================= */
function escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Expose showToast globally for use by templates
window.showToast = showToast;

/* =================================================
   PREMIUM CUSTOM DROPDOWN / SELECT COMPONENT
   Inspired by Linear, Raycast, Notion, Vercel
   ================================================= */

/* Icon mapping for subjects and exams */
const DROPDOWN_ICON_MAP = {
    /* Subjects */
    'Mathematics':       { emoji: '🧮', color: '#F59E0B' },
    'Physics':           { emoji: '⚛️', color: '#8B5CF6' },
    'Chemistry':         { emoji: '🧪', color: '#10B981' },
    'Biology':           { emoji: '🌿', color: '#22C55E' },
    'Computer Science':  { emoji: '💻', color: '#3B82F6' },
    'English':           { emoji: '📖', color: '#EC4899' },
    'History':           { emoji: '🏛️', color: '#A78BFA' },
    'Geography':         { emoji: '🌍', color: '#06B6D4' },
    'Economics':         { emoji: '📈', color: '#F97316' },
    'Political Science': { emoji: '⚖️', color: '#6366F1' },
    'Psychology':        { emoji: '🧠', color: '#E879F9' },
    'Sociology':         { emoji: '👥', color: '#14B8A6' },
    'Accountancy':       { emoji: '📊', color: '#EAB308' },
    'Business Studies':  { emoji: '💼', color: '#F472B6' },
    'Other':             { emoji: '📝', color: '#94A3B8' },

    /* Exams */
    'JEE Main':      { emoji: '🎯', color: '#EF4444' },
    'JEE Advanced':  { emoji: '🔥', color: '#DC2626' },
    'NEET':          { emoji: '🩺', color: '#10B981' },
    'UPSC':          { emoji: '🏅', color: '#F59E0B' },
    'CAT':           { emoji: '📐', color: '#8B5CF6' },
    'GATE':          { emoji: '⚙️', color: '#6366F1' },
    'GRE':           { emoji: '🌐', color: '#3B82F6' },
    'SAT':           { emoji: '📘', color: '#2563EB' },
    'CBSE':          { emoji: '🏫', color: '#0EA5E9' },
    'ICSE':          { emoji: '🏫', color: '#06B6D4' },
    'State Board':   { emoji: '📋', color: '#14B8A6' },
    'University':    { emoji: '🎓', color: '#A855F7' },
    'Competitive':   { emoji: '🏆', color: '#F97316' },

    /* Sort options */
    'Newest':        { emoji: '🕐', color: '#3B82F6' },
    'Oldest':        { emoji: '📅', color: '#94A3B8' },
    'Most Answers':  { emoji: '💬', color: '#22C55E' },
    'Unanswered':    { emoji: '❓', color: '#F59E0B' },
    'Resolved':      { emoji: '✅', color: '#10B981' },
};

/* Fallback icons for generic/placeholder options */
const DROPDOWN_FALLBACK = { emoji: '📌', color: '#64748B' };

function getOptionIcon(text) {
    const trimmed = text.trim();
    return DROPDOWN_ICON_MAP[trimmed] || DROPDOWN_FALLBACK;
}

function initCustomDropdowns() {
    const nativeSelects = document.querySelectorAll('select.glass-input, select.form-select');

    nativeSelects.forEach(select => {
        if (select.dataset.customized === 'true') return;
        select.dataset.customized = 'true';

        /* ---- Hide native select (visually-hidden, still accessible for forms) ---- */
        select.style.position = 'absolute';
        select.style.width = '1px';
        select.style.height = '1px';
        select.style.padding = '0';
        select.style.margin = '-1px';
        select.style.overflow = 'hidden';
        select.style.clip = 'rect(0, 0, 0, 0)';
        select.style.border = '0';
        select.style.opacity = '0';

        /* ---- Wrapper ---- */
        const wrapper = document.createElement('div');
        wrapper.className = 'sc-select';
        select.parentNode.insertBefore(wrapper, select);
        wrapper.appendChild(select);

        /* ---- Trigger ---- */
        const trigger = document.createElement('button');
        trigger.type = 'button';
        trigger.className = 'sc-select__trigger';
        trigger.setAttribute('role', 'combobox');
        trigger.setAttribute('aria-expanded', 'false');
        trigger.setAttribute('aria-haspopup', 'listbox');

        const selectedOpt = select.options[select.selectedIndex];
        const initText = selectedOpt ? selectedOpt.textContent.trim() : 'Select…';
        const initIcon = getOptionIcon(initText);
        const isPlaceholder = !selectedOpt || selectedOpt.value === '';

        trigger.innerHTML = buildTriggerHTML(initText, initIcon, isPlaceholder);
        wrapper.appendChild(trigger);

        /* ---- Floating Panel ---- */
        const panel = document.createElement('div');
        panel.className = 'sc-select__panel';
        panel.setAttribute('role', 'listbox');
        wrapper.appendChild(panel);

        /* ---- Build Options ---- */
        const items = [];
        Array.from(select.options).forEach((opt, idx) => {
            const text = opt.textContent.trim();
            const icon = getOptionIcon(text);
            const isDefault = opt.value === '';

            const item = document.createElement('div');
            item.className = 'sc-select__item';
            item.dataset.value = opt.value;
            item.dataset.index = idx;
            item.setAttribute('role', 'option');

            if (opt.selected) {
                item.classList.add('sc-select__item--selected');
                item.setAttribute('aria-selected', 'true');
            } else {
                item.setAttribute('aria-selected', 'false');
            }

            item.innerHTML = `
                <span class="sc-select__item-icon" style="background:${icon.color}20; border-color:${icon.color}35">
                    ${icon.emoji}
                </span>
                <span class="sc-select__item-label${isDefault ? ' sc-select__item-label--muted' : ''}">${escapeHtml(text)}</span>
                <span class="sc-select__item-check">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M3.5 8.5L6.5 11.5L12.5 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </span>
            `;

            panel.appendChild(item);
            items.push(item);

            item.addEventListener('click', (e) => {
                e.stopPropagation();
                pickOption(idx);
                close();
                trigger.focus();
            });
        });

        let focusIdx = select.selectedIndex;

        /* ---- Core Logic ---- */
        function pickOption(idx) {
            items.forEach(it => {
                it.classList.remove('sc-select__item--selected');
                it.setAttribute('aria-selected', 'false');
            });
            const picked = items[idx];
            if (!picked) return;

            picked.classList.add('sc-select__item--selected');
            picked.setAttribute('aria-selected', 'true');
            select.selectedIndex = idx;
            focusIdx = idx;

            const text = select.options[idx].textContent.trim();
            const icon = getOptionIcon(text);
            const isPlaceholder = select.options[idx].value === '';
            trigger.innerHTML = buildTriggerHTML(text, icon, isPlaceholder);

            /* Dispatch native change for onchange handlers */
            select.dispatchEvent(new Event('change', { bubbles: true }));
        }

        function open() {
            /* Close any other open dropdowns first */
            document.querySelectorAll('.sc-select.sc-select--open').forEach(w => {
                if (w !== wrapper) {
                    w.classList.remove('sc-select--open');
                    const t = w.querySelector('.sc-select__trigger');
                    if (t) t.setAttribute('aria-expanded', 'false');
                }
            });

            wrapper.classList.add('sc-select--open');
            trigger.setAttribute('aria-expanded', 'true');

            /* Scroll to selected */
            const sel = panel.querySelector('.sc-select__item--selected');
            if (sel) {
                requestAnimationFrame(() => sel.scrollIntoView({ block: 'nearest' }));
            }
        }

        function close() {
            wrapper.classList.remove('sc-select--open');
            trigger.setAttribute('aria-expanded', 'false');
            items.forEach(it => it.classList.remove('sc-select__item--focus'));
        }

        function highlight(idx) {
            items.forEach(it => it.classList.remove('sc-select__item--focus'));
            const it = items[idx];
            if (it) {
                it.classList.add('sc-select__item--focus');
                it.scrollIntoView({ block: 'nearest' });
            }
        }

        /* ---- Event Listeners ---- */
        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            wrapper.classList.contains('sc-select--open') ? close() : open();
        });

        document.addEventListener('click', (e) => {
            if (!wrapper.contains(e.target)) close();
        });

        trigger.addEventListener('keydown', (e) => {
            const isOpen = wrapper.classList.contains('sc-select--open');

            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    if (!isOpen) { open(); } else {
                        focusIdx = (focusIdx + 1) % items.length;
                        highlight(focusIdx);
                    }
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    if (!isOpen) { open(); } else {
                        focusIdx = (focusIdx - 1 + items.length) % items.length;
                        highlight(focusIdx);
                    }
                    break;
                case 'Enter':
                case ' ':
                    e.preventDefault();
                    if (isOpen) { pickOption(focusIdx); close(); }
                    else { open(); }
                    break;
                case 'Escape':
                    e.preventDefault();
                    close();
                    break;
                case 'Tab':
                    close();
                    break;
                case 'Home':
                    if (isOpen) { e.preventDefault(); focusIdx = 0; highlight(focusIdx); }
                    break;
                case 'End':
                    if (isOpen) { e.preventDefault(); focusIdx = items.length - 1; highlight(focusIdx); }
                    break;
            }
        });
    });
}

/* Build trigger inner HTML with icon + text + chevron */
function buildTriggerHTML(text, icon, isPlaceholder) {
    return `
        <span class="sc-select__trigger-icon" style="background:${icon.color}20; border-color:${icon.color}35">
            ${icon.emoji}
        </span>
        <span class="sc-select__trigger-text${isPlaceholder ? ' sc-select__trigger-text--placeholder' : ''}">${escapeHtml(text)}</span>
        <span class="sc-select__trigger-chevron">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </span>
    `;
}

