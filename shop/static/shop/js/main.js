/**
 * Store3D — Main JavaScript
 * Cart management, animations, UI interactions
 */

document.addEventListener('DOMContentLoaded', () => {
    initNavbar();
    initScrollReveal();
    initToast();
    initParticles();
});

/* ── Navbar Scroll Effect & Mobile Menu ── */
function initNavbar() {
    const navbar = document.querySelector('.navbar');
    const burger = document.querySelector('.navbar__burger');
    const links = document.querySelector('.navbar__links');
    const auth = document.querySelector('.navbar__auth');

    // Scroll effect
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }

    // Mobile menu toggle
    if (burger) {
        burger.addEventListener('click', () => {
            burger.classList.toggle('active');
            if (links) links.classList.toggle('mobile-open');
            if (auth) auth.classList.toggle('mobile-open');
        });

        // Close menu when link clicked
        document.querySelectorAll('.navbar__link').forEach(link => {
            link.addEventListener('click', () => {
                burger.classList.remove('active');
                if (links) links.classList.remove('mobile-open');
                if (auth) auth.classList.remove('mobile-open');
            });
        });
    }
}

/* ── Cart Functions ── */
function getCSRFToken() {
    const cookie = document.cookie.split('; ').find(c => c.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

function addToCart(productId, quantity = 1) {
    const btn = document.querySelector(`[data-product-id="${productId}"]`);
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '⏳';
    }

    fetch('/cart/add/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify({ product_id: productId, quantity: quantity }),
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            updateCartBadge(data.cart_count);
            showToast(data.message || 'Додано до кошика!', '✅');

            if (btn) {
                btn.innerHTML = '✓';
                btn.style.background = 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)';
                setTimeout(() => {
                    btn.innerHTML = '+';
                    btn.style.background = '';
                    btn.disabled = false;
                }, 1500);
            }
        } else {
            showToast(data.error || 'Помилка', '❌');
            if (btn) {
                btn.innerHTML = '+';
                btn.disabled = false;
            }
        }
    })
    .catch(() => {
        showToast('Помилка зʼєднання', '❌');
        if (btn) {
            btn.innerHTML = '+';
            btn.disabled = false;
        }
    });
}

function updateCartItem(productId, quantity) {
    fetch('/cart/update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify({ product_id: productId, quantity: quantity }),
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            updateCartBadge(data.cart_count);
            // Reload page to recalculate totals
            window.location.reload();
        }
    });
}

function removeFromCart(productId) {
    fetch('/cart/remove/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify({ product_id: productId }),
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            updateCartBadge(data.cart_count);
            // Animate removal
            const item = document.querySelector(`[data-cart-item="${productId}"]`);
            if (item) {
                item.style.transform = 'translateX(100px)';
                item.style.opacity = '0';
                setTimeout(() => {
                    window.location.reload();
                }, 300);
            } else {
                window.location.reload();
            }
        }
    });
}

function updateCartBadge(count) {
    const badge = document.querySelector('.navbar__cart-badge');
    if (badge) {
        badge.textContent = count;
        if (count > 0) {
            badge.classList.add('visible');
            // Bounce animation
            badge.style.transform = 'scale(1.3)';
            setTimeout(() => {
                badge.style.transform = 'scale(1)';
            }, 200);
        } else {
            badge.classList.remove('visible');
        }
    }
}

/* ── Product Detail Quantity ── */
function changeQuantity(delta) {
    const valueEl = document.getElementById('quantity-value');
    if (!valueEl) return;

    let val = parseInt(valueEl.textContent) + delta;
    const max = parseInt(valueEl.dataset.max) || 99;
    val = Math.max(1, Math.min(val, max));
    valueEl.textContent = val;
}

function addToCartFromDetail() {
    const valueEl = document.getElementById('quantity-value');
    const productId = valueEl ? valueEl.dataset.productId : null;
    const quantity = valueEl ? parseInt(valueEl.textContent) : 1;
    if (productId) {
        addToCart(productId, quantity);
    }
}

/* ── Toast Notification ── */
let toastTimeout;

function initToast() {
    // Create toast element if it doesn't exist
    if (!document.querySelector('.toast')) {
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.innerHTML = '<span class="toast__icon"></span><span class="toast__text"></span>';
        document.body.appendChild(toast);
    }
}

function showToast(message, icon = '✅') {
    const toast = document.querySelector('.toast');
    if (!toast) return;

    clearTimeout(toastTimeout);

    toast.querySelector('.toast__icon').textContent = icon;
    toast.querySelector('.toast__text').textContent = message;

    // Show
    requestAnimationFrame(() => {
        toast.classList.add('visible');
    });

    // Auto-hide
    toastTimeout = setTimeout(() => {
        toast.classList.remove('visible');
    }, 3000);
}

/* ── Scroll Reveal ── */
function initScrollReveal() {
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
    );

    document.querySelectorAll('.reveal').forEach(el => {
        observer.observe(el);
    });
}

/* ── Particles ── */
function initParticles() {
    const container = document.querySelector('.hero__particles');
    if (!container) return;

    for (let i = 0; i < 20; i++) {
        const particle = document.createElement('div');
        particle.className = 'hero__particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.setProperty('--duration', (4 + Math.random() * 6) + 's');
        particle.style.setProperty('--delay', (Math.random() * 4) + 's');
        particle.style.width = (2 + Math.random() * 4) + 'px';
        particle.style.height = particle.style.width;
        container.appendChild(particle);
    }
}

/* ── Auto-dismiss messages ── */
setTimeout(() => {
    document.querySelectorAll('.message').forEach(msg => {
        msg.style.animation = 'fadeOutUp 0.4s ease-out forwards';
        setTimeout(() => msg.remove(), 400);
    });
}, 4000);
