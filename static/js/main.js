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

window.addEventListener("load", () => {
    document.querySelector(".page-loader")?.classList.add("hidden");
});


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
