const sideToggle = document.querySelector('.side-toggle');
const sidebar = document.querySelector('.sidebar');

sideToggle?.addEventListener('click', () => {
    sidebar?.classList.toggle('open');
});

const inventoryCanvas = document.getElementById('inventoryChart');

function drawInventoryChart() {
    if (!inventoryCanvas) {
        return;
    }

    const shell = inventoryCanvas.parentElement;
    const context = inventoryCanvas.getContext('2d');
    const values = [
        Number(inventoryCanvas.dataset.available || 0),
        Number(inventoryCanvas.dataset.reserved || 0),
        Number(inventoryCanvas.dataset.sold || 0)
    ];
    const labels = ['Available', 'Reserved', 'Sold'];
    const colors = ['#2a9d55', '#d99a00', '#c1121f'];
    const deviceScale = window.devicePixelRatio || 1;
    const cssWidth = Math.max(shell?.clientWidth || 300, 240);
    const cssHeight = window.innerWidth <= 520 ? 200 : window.innerWidth <= 760 ? 220 : 250;

    inventoryCanvas.width = Math.floor(cssWidth * deviceScale);
    inventoryCanvas.height = Math.floor(cssHeight * deviceScale);
    inventoryCanvas.style.width = `${cssWidth}px`;
    inventoryCanvas.style.height = `${cssHeight}px`;

    context.setTransform(deviceScale, 0, 0, deviceScale, 0, 0);
    context.clearRect(0, 0, cssWidth, cssHeight);

    const chartPadding = window.innerWidth <= 380 ? 24 : 34;
    const labelArea = 38;
    const chartHeight = cssHeight - chartPadding - labelArea;
    const maxValue = Math.max(...values, 1);
    const groupWidth = (cssWidth - chartPadding * 2) / values.length;
    const barWidth = Math.min(82, Math.max(34, groupWidth * 0.48));
    const fontSize = window.innerWidth <= 420 ? 11 : 13;

    context.textAlign = 'center';
    context.font = `600 ${fontSize}px Arial`;

    values.forEach((value, index) => {
        const barHeight = value === 0 ? 3 : Math.max(8, (value / maxValue) * (chartHeight - 28));
        const centerX = chartPadding + groupWidth * index + groupWidth / 2;
        const x = centerX - barWidth / 2;
        const y = chartHeight - barHeight;

        context.fillStyle = colors[index];
        context.fillRect(x, y, barWidth, barHeight);

        context.fillStyle = '#222222';
        context.fillText(String(value), centerX, Math.max(15, y - 8));

        context.fillStyle = '#666666';
        context.font = `500 ${fontSize}px Arial`;
        context.fillText(labels[index], centerX, chartHeight + 24);
        context.font = `600 ${fontSize}px Arial`;
    });
}

let resizeTimer;

window.addEventListener('resize', () => {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(drawInventoryChart, 120);
});

drawInventoryChart();

// Testimonial live preview
function initializeTestimonialEditor() {
    const editor = document.querySelector('[data-testimonial-editor]');
    if (!editor) return;

    const nameInput = editor.querySelector('[name="client_name"]');
    const titleInput = editor.querySelector('[name="client_title"]');
    const reviewInput = editor.querySelector('[name="testimonial"]');
    const ratingInput = editor.querySelector('[name="rating"]');
    const imageInput = editor.querySelector('[name="image"]');
    const previewName = editor.querySelector('[data-preview-name]');
    const previewTitle = editor.querySelector('[data-preview-title]');
    const previewReview = editor.querySelector('[data-preview-review]');
    const previewStars = editor.querySelector('[data-preview-stars]');
    const previewAvatar = editor.querySelector('[data-preview-avatar]');

    const update = () => {
        const name = (nameInput?.value || '').trim() || 'Client Name';
        const title = (titleInput?.value || '').trim() || 'Valued Client';
        const review = (reviewInput?.value || '').trim() || 'Your client testimonial will appear here as you type.';
        const rating = Math.min(5, Math.max(1, Number(ratingInput?.value || 5)));

        if (previewName) previewName.textContent = name;
        if (previewTitle) previewTitle.textContent = title;
        if (previewReview) previewReview.textContent = review;
        if (previewAvatar) previewAvatar.textContent = name.charAt(0).toUpperCase() || 'C';
        if (previewStars) {
            previewStars.innerHTML = '';
            for (let i = 1; i <= 5; i += 1) {
                const star = document.createElement('i');
                star.className = `${i <= rating ? 'fas' : 'far'} fa-star`;
                previewStars.appendChild(star);
            }
        }
    };

    [nameInput, titleInput, reviewInput, ratingInput].forEach((input) => {
        input?.addEventListener('input', update);
        input?.addEventListener('change', update);
    });

    imageInput?.addEventListener('change', () => {
        const file = imageInput.files?.[0];
        if (!file || !previewAvatar) return;
        const reader = new FileReader();
        reader.addEventListener('load', () => {
            previewAvatar.style.backgroundImage = `url("${reader.result}")`;
            previewAvatar.style.backgroundSize = 'cover';
            previewAvatar.style.backgroundPosition = 'center';
            previewAvatar.textContent = '';
        });
        reader.readAsDataURL(file);
    });

    update();
}

document.addEventListener('DOMContentLoaded', initializeTestimonialEditor);


// Accessible show / hide password controls
function initializePasswordToggles() {
    document.querySelectorAll('[data-password-toggle]').forEach((button) => {
        const targetId = button.dataset.passwordToggle;
        const input = document.getElementById(targetId);
        if (!input) return;

        button.addEventListener('click', () => {
            const shouldShow = input.type === 'password';
            input.type = shouldShow ? 'text' : 'password';
            button.textContent = shouldShow ? 'Hide' : 'Show';
            button.setAttribute('aria-label', shouldShow ? 'Hide password' : 'Show password');
            button.setAttribute('aria-pressed', String(shouldShow));
            input.focus({ preventScroll: true });
        });
    });
}

document.addEventListener('DOMContentLoaded', initializePasswordToggles);
