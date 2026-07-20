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
