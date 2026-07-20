const observer = new IntersectionObserver(entries => entries.forEach(e => {
    if (e.isIntersecting) {
        e.target.classList.add('visible');
        observer.unobserve(e.target)
    }
}), {
    threshold: .12
});
document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
const counterObserver = new IntersectionObserver(entries => entries.forEach(entry => {
    if (!entry.isIntersecting) return;
    const el = entry.target,
        target = Number(el.dataset.target),
        duration = 1300,
        start = performance.now();

    function tick(now) {
        const p = Math.min((now - start) / duration, 1);
        el.textContent = Math.floor(target * (1 - Math.pow(1 - p, 3))).toLocaleString();
        if (p < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick);
    counterObserver.unobserve(el)
}));
document.querySelectorAll('.counter').forEach(el => counterObserver.observe(el));