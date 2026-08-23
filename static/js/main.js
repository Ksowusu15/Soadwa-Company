document.addEventListener("DOMContentLoaded", () => {
    const navbar = document.getElementById("navbar");
    const menuButton = document.querySelector(".menu-btn");
    const navigationLinks = document.querySelector(".nav-links");

    const updateNavbar = () => {
        if (navbar) {
            navbar.classList.toggle("scrolled", window.scrollY > 40);
        }
    };

    updateNavbar();
    window.addEventListener("scroll", updateNavbar);

    menuButton?.addEventListener("click", () => {
        const isOpen = navigationLinks?.classList.toggle("open") || false;
        document.body.classList.toggle("menu-open", isOpen);
        menuButton.setAttribute("aria-expanded", String(isOpen));

        const icon = menuButton.querySelector("i");
        icon?.classList.toggle("fa-bars", !isOpen);
        icon?.classList.toggle("fa-xmark", isOpen);
    });

    document.querySelectorAll(".nav-links a").forEach((link) => {
        link.addEventListener("click", () => {
            navigationLinks?.classList.remove("open");
            document.body.classList.remove("menu-open");
            menuButton?.setAttribute("aria-expanded", "false");

            const icon = menuButton?.querySelector("i");
            icon?.classList.add("fa-bars");
            icon?.classList.remove("fa-xmark");
        });
    });

    document.addEventListener("click", (event) => {
        if (
            navigationLinks?.classList.contains("open") &&
            !navigationLinks.contains(event.target) &&
            !menuButton?.contains(event.target)
        ) {
            navigationLinks.classList.remove("open");
            document.body.classList.remove("menu-open");
            menuButton?.setAttribute("aria-expanded", "false");

            const icon = menuButton?.querySelector("i");
            icon?.classList.add("fa-bars");
            icon?.classList.remove("fa-xmark");
        }
    });

    document.querySelectorAll(".flash button").forEach((button) => {
        button.addEventListener("click", () => {
            button.parentElement?.remove();
        });
    });

    initializeFavorites();
    initializeComparison();
    initializeGallery();
    initializeFinanceCalculator();
});

function readStoredIds(key) {
    try {
        const storedValue = JSON.parse(localStorage.getItem(key) || "[]");

        if (!Array.isArray(storedValue)) {
            return [];
        }

        return storedValue.map(String);
    } catch (error) {
        return [];
    }
}

function initializeFavorites() {
    const storageKey = "eliteFavorites";
    const favorites = readStoredIds(storageKey);

    document.querySelectorAll(".car-card").forEach((card) => {
        const carId = String(card.dataset.carId);
        const favoriteButton = card.querySelector(".favorite-btn");
        const favoriteIcon = favoriteButton?.querySelector("i");

        if (favorites.includes(carId)) {
            favoriteButton?.classList.add("active");
            favoriteIcon?.classList.replace("far", "fas");
        }

        favoriteButton?.addEventListener("click", () => {
            const index = favorites.indexOf(carId);

            if (index >= 0) {
                favorites.splice(index, 1);
                favoriteButton.classList.remove("active");
                favoriteIcon?.classList.replace("fas", "far");
            } else {
                favorites.push(carId);
                favoriteButton.classList.add("active");
                favoriteIcon?.classList.replace("far", "fas");
            }

            localStorage.setItem(storageKey, JSON.stringify(favorites));
        });
    });
}

function initializeComparison() {
    const storageKey = "eliteCompare";
    const maximumVehicles = 3;
    let selectedCars = readStoredIds(storageKey).slice(0, maximumVehicles);

    const compareBar = document.getElementById("compareBar");
    const compareCount = document.getElementById("compareCount");
    const compareButton = document.getElementById("compareBtn");
    const clearCompareButton = document.getElementById("clearCompare");

    const saveSelection = () => {
        localStorage.setItem(storageKey, JSON.stringify(selectedCars));
    };

    const updateComparisonUI = () => {
        document.querySelectorAll(".compare-toggle").forEach((checkbox) => {
            const card = checkbox.closest(".car-card");
            const carId = String(card?.dataset.carId || "");
            checkbox.checked = selectedCars.includes(carId);
        });

        if (compareCount) {
            compareCount.textContent = selectedCars.length;
        }

        compareBar?.classList.toggle("show", selectedCars.length >= 2);

        if (compareBar) {
            compareBar.setAttribute(
                "aria-hidden",
                selectedCars.length >= 2 ? "false" : "true"
            );
        }

        if (compareButton) {
            compareButton.disabled = selectedCars.length < 2;
        }
    };

    document.querySelectorAll(".compare-toggle").forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
            const card = checkbox.closest(".car-card");
            const carId = String(card?.dataset.carId || "");

            if (!carId) {
                return;
            }

            if (checkbox.checked) {
                if (selectedCars.includes(carId)) {
                    return;
                }

                if (selectedCars.length >= maximumVehicles) {
                    checkbox.checked = false;
                    window.alert(
                        `You can compare up to ${maximumVehicles} vehicles at a time.`
                    );
                    return;
                }

                selectedCars.push(carId);
            } else {
                selectedCars = selectedCars.filter((id) => id !== carId);
            }

            saveSelection();
            updateComparisonUI();
        });
    });

    compareButton?.addEventListener("click", () => {
        if (selectedCars.length < 2) {
            window.alert("Select at least two vehicles to compare.");
            return;
        }

        const query = encodeURIComponent(selectedCars.join(","));
        window.location.href = `/compare?ids=${query}`;
    });

    document.querySelectorAll(".compare-remove").forEach((button) => {
        button.addEventListener("click", () => {
            const carId = String(button.dataset.carId || "");
            selectedCars = selectedCars.filter((id) => id !== carId);
            saveSelection();

            if (selectedCars.length >= 2) {
                const query = encodeURIComponent(selectedCars.join(","));
                window.location.href = `/compare?ids=${query}`;
            } else {
                window.location.href = "/inventory";
            }
        });
    });

    clearCompareButton?.addEventListener("click", () => {
        selectedCars = [];
        saveSelection();
        window.location.href = "/inventory";
    });

    saveSelection();
    updateComparisonUI();
}

function initializeGallery() {
    document.querySelectorAll(".thumbnails img").forEach((image) => {
        image.addEventListener("click", () => {
            const mainImage = document.getElementById("mainCarImage");

            if (mainImage) {
                mainImage.src = image.src;
                mainImage.alt = image.alt;
            }
        });
    });
}

function initializeFinanceCalculator() {
    const calculateButton = document.getElementById("calculateFinance");

    calculateButton?.addEventListener("click", (event) => {
        event.preventDefault();

        const price = Number(calculateButton.dataset.price);
        const downPayment = Number(
            document.getElementById("downPayment")?.value || 0
        );
        const months = Number(
            document.getElementById("financeTerm")?.value || 12
        );
        const annualRate = Number(
            document.getElementById("interestRate")?.value || 0
        ) / 100;
        const monthlyRate = annualRate / 12;
        const principal = Math.max(price - downPayment, 0);

        const monthlyPayment = monthlyRate
            ? principal * monthlyRate * Math.pow(1 + monthlyRate, months) /
              (Math.pow(1 + monthlyRate, months) - 1)
            : principal / months;

        const output = document.getElementById("monthlyPayment");

        if (output) {
            output.textContent = `${monthlyPayment.toLocaleString(undefined, {
                maximumFractionDigits: 0,
            })} / month`;
        }
    });
}

// Clean page-loading experience
(() => {
    const loader = document.getElementById("pageLoader");
    if (!loader) return;

    const showLoader = () => {
        loader.classList.remove("hidden");
        document.body.classList.add("is-page-loading");
    };

    const hideLoader = () => {
        window.requestAnimationFrame(() => {
            loader.classList.add("hidden");
            document.body.classList.remove("is-page-loading");
        });
    };

    // Keep the loader visible while the initial page and critical assets finish.
    document.body.classList.add("is-page-loading");

    window.addEventListener("load", () => {
        // Small minimum duration prevents an abrupt flash on fast connections.
        window.setTimeout(hideLoader, 180);
    }, { once: true });

    // Handles browser back/forward cache restoration.
    window.addEventListener("pageshow", (event) => {
        if (event.persisted) hideLoader();
    });

    // Show the loader when navigating to another page on this website.
    document.addEventListener("click", (event) => {
        const link = event.target.closest("a[href]");
        if (!link) return;

        const href = link.getAttribute("href") || "";

        if (
            event.defaultPrevented ||
            event.button !== 0 ||
            event.metaKey ||
            event.ctrlKey ||
            event.shiftKey ||
            event.altKey ||
            link.target === "_blank" ||
            link.hasAttribute("download") ||
            href.startsWith("#") ||
            href.startsWith("mailto:") ||
            href.startsWith("tel:") ||
            href.startsWith("javascript:")
        ) {
            return;
        }

        try {
            const destination = new URL(link.href, window.location.href);
            if (
                destination.origin === window.location.origin &&
                destination.href !== window.location.href
            ) {
                showLoader();
            }
        } catch (_) {
            // Ignore malformed/non-navigation URLs.
        }
    });

    // Give submitted forms immediate visual feedback while the server responds.
    document.addEventListener("submit", (event) => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement)) return;
        if (form.dataset.noPageLoader === "true") return;

        // Let browser validation run first.
        if (!form.checkValidity()) return;

        showLoader();
    });
})();


// Responsive vehicle details gallery
document.addEventListener("DOMContentLoaded", () => {
    const mainImage = document.getElementById("mainCarImage");
    const thumbnails = document.querySelectorAll(".vehicle-thumbnail");

    if (!mainImage || !thumbnails.length) return;

    thumbnails.forEach((button) => {
        button.addEventListener("click", () => {
            const image = button.querySelector("img");
            if (!image) return;

            mainImage.src = image.src;
            mainImage.alt = image.alt;
            thumbnails.forEach((item) => item.classList.remove("active"));
            button.classList.add("active");
        });
    });
});

// Premium responsive testimonial carousel
function initializeTestimonialCarousel() {
    const carousel = document.querySelector('[data-testimonial-carousel]');
    if (!carousel) return;

    const viewport = carousel.querySelector('.testimonial-carousel-viewport');
    const track = carousel.querySelector('[data-testimonial-track]');
    const slides = Array.from(track?.querySelectorAll('.testimonial-slide') || []);
    const previousButton = carousel.querySelector('[data-testimonial-prev]');
    const nextButton = carousel.querySelector('[data-testimonial-next]');
    const dotsContainer = carousel.querySelector('[data-testimonial-dots]');
    if (!viewport || !track || !slides.length) return;

    let page = 0;

    const visibleCount = () => {
        if (window.innerWidth <= 680) return 1;
        if (window.innerWidth <= 980) return 2;
        return 3;
    };

    const pageCount = () => Math.max(1, Math.ceil(slides.length / visibleCount()));

    const renderDots = () => {
        if (!dotsContainer) return;
        dotsContainer.innerHTML = '';
        for (let i = 0; i < pageCount(); i += 1) {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = `testimonial-dot${i === page ? ' active' : ''}`;
            button.setAttribute('aria-label', `Show testimonial page ${i + 1}`);
            button.addEventListener('click', () => {
                page = i;
                update();
            });
            dotsContainer.appendChild(button);
        }
    };

    const update = () => {
        const pages = pageCount();
        if (page >= pages) page = pages - 1;
        const offset = page * viewport.clientWidth;
        track.style.transform = `translateX(-${offset}px)`;
        renderDots();
        if (previousButton) previousButton.disabled = pages <= 1;
        if (nextButton) nextButton.disabled = pages <= 1;
    };

    previousButton?.addEventListener('click', () => {
        const pages = pageCount();
        page = (page - 1 + pages) % pages;
        update();
    });

    nextButton?.addEventListener('click', () => {
        const pages = pageCount();
        page = (page + 1) % pages;
        update();
    });

    // Touch / mouse drag support. Vertical page scrolling remains enabled.
    let dragging = false;
    let startX = 0;
    let currentX = 0;
    let baseOffset = 0;
    let activePointerId = null;

    const beginDrag = (event) => {
        if (event.pointerType === 'mouse' && event.button !== 0) return;
        dragging = true;
        activePointerId = event.pointerId;
        startX = event.clientX;
        currentX = startX;
        baseOffset = page * viewport.clientWidth;
        track.classList.add('is-dragging');
        viewport.classList.add('is-dragging');
        try { viewport.setPointerCapture(event.pointerId); } catch (_) {}
    };

    const moveDrag = (event) => {
        if (!dragging || event.pointerId !== activePointerId) return;
        currentX = event.clientX;
        const delta = currentX - startX;
        track.style.transform = `translateX(${-(baseOffset - delta)}px)`;
    };

    const endDrag = (event) => {
        if (!dragging || event.pointerId !== activePointerId) return;
        dragging = false;
        const delta = currentX - startX;
        const threshold = Math.min(90, Math.max(45, viewport.clientWidth * 0.12));
        const pages = pageCount();

        track.classList.remove('is-dragging');
        viewport.classList.remove('is-dragging');
        try { viewport.releasePointerCapture(event.pointerId); } catch (_) {}
        activePointerId = null;

        if (Math.abs(delta) >= threshold && pages > 1) {
            if (delta < 0) {
                page = (page + 1) % pages;
            } else {
                page = (page - 1 + pages) % pages;
            }
        }
        update();
    };

    viewport.addEventListener('pointerdown', beginDrag);
    viewport.addEventListener('pointermove', moveDrag);
    viewport.addEventListener('pointerup', endDrag);
    viewport.addEventListener('pointercancel', endDrag);

    // Keyboard accessibility when the carousel has focus.
    viewport.setAttribute('tabindex', '0');
    viewport.addEventListener('keydown', (event) => {
        if (event.key === 'ArrowLeft') {
            event.preventDefault();
            previousButton?.click();
        } else if (event.key === 'ArrowRight') {
            event.preventDefault();
            nextButton?.click();
        }
    });

    let resizeTimer;
    window.addEventListener('resize', () => {
        window.clearTimeout(resizeTimer);
        resizeTimer = window.setTimeout(update, 120);
    });

    update();
}

document.addEventListener('DOMContentLoaded', initializeTestimonialCarousel);


// Enquiry success notification controls
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash").forEach((flash) => {
    const closeButton = flash.querySelector(".flash-close");

    const dismiss = () => {
      if (flash.classList.contains("flash-leaving")) return;
      flash.classList.add("flash-leaving");
      window.setTimeout(() => flash.remove(), 260);
    };

    if (closeButton) {
      closeButton.addEventListener("click", dismiss);
    }

    if (flash.classList.contains("success")) {
      window.setTimeout(dismiss, 6500);
    }
  });
});
