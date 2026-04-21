document.addEventListener("input", e => {
  if (e.target.matches('.thermo-scale input[type="range"]')) {
    const range = e.target;
    const track = range.closest('.thermo-scale')
                      .querySelector('.thermo-fill');
    const max = Number(range.max || 6);
    const val = Number(range.value || 0);
    const ratio = max ? val / max : 0;
    track.style.setProperty('--ratio', ratio);
    track.style.transform = `scaleX(${ratio})`;
  }
});

// inițializează toate la încărcare
window.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('.thermo-scale input[type="range"]')
    .forEach(r => r.dispatchEvent(new Event('input')));
});
