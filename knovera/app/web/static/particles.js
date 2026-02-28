(() => {
  const canvas = document.getElementById('particleCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d', { alpha: true });
  if (!ctx) return;

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  let width = 0;
  let height = 0;
  let dpr = 1;
  let animationId = 0;
  let lastTick = 0;
  let particles = [];
  let resizeTimer = null;

  // brain-shaped mask path; particles and drawing are constrained inside
  let brainMask = null;

  function updateMask() {
    if (!width || !height) return;
    const cx = width * 0.5;

    // compute radius based on viewport but allow it to grow larger
    const r = Math.min(width, height) * 0.45;
    const offset = r * 0.6; // stronger separation for lobes

    // default y-centre is vertical centre
    let cy = height * 0.5;

    // if hero section is present, move the brain above it
    const hero = document.getElementById('heroBrandSection');
    if (hero) {
      const rect = hero.getBoundingClientRect();
      // put bottom of brain at ~20px above hero top
      cy = rect.top - r + 20;
      // if that pushes mask offscreen, fall back to centre
      if (cy - r < 0) cy = height * 0.3;
    }

    const path = new Path2D();
    // left lobe
    path.arc(cx - offset, cy, r, 0, Math.PI * 2);
    // right lobe
    path.arc(cx + offset, cy, r, 0, Math.PI * 2);
    brainMask = path;
  }

  const palette = {
    node: { r: 92, g: 141, b: 255 },
    link: { r: 92, g: 141, b: 255 },
    glow: { r: 92, g: 141, b: 255 },
  };

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function parseColor(colorValue, fallback) {
    const fallbackColor = fallback || { r: 92, g: 141, b: 255 };
    const color = (colorValue || '').trim();
    if (!color) return fallbackColor;

    if (color[0] === '#') {
      let hex = color.slice(1);
      if (hex.length === 3) {
        hex = `${hex[0]}${hex[0]}${hex[1]}${hex[1]}${hex[2]}${hex[2]}`;
      }
      if (hex.length === 6) {
        const num = Number.parseInt(hex, 16);
        if (!Number.isNaN(num)) {
          return {
            r: (num >> 16) & 255,
            g: (num >> 8) & 255,
            b: num & 255,
          };
        }
      }
      return fallbackColor;
    }

    const rgbMatch = color.match(/rgba?\(([^)]+)\)/i);
    if (!rgbMatch) return fallbackColor;

    const parts = rgbMatch[1].split(',').map((part) => Number.parseFloat(part.trim()));
    if (parts.length < 3 || parts.some((n, idx) => idx < 3 && Number.isNaN(n))) {
      return fallbackColor;
    }

    return {
      r: clamp(Math.round(parts[0]), 0, 255),
      g: clamp(Math.round(parts[1]), 0, 255),
      b: clamp(Math.round(parts[2]), 0, 255),
    };
  }

  function updatePalette() {
    const styles = getComputedStyle(document.documentElement);
    const accent = parseColor(styles.getPropertyValue('--accent'), palette.node);
    const neuronCore = parseColor(styles.getPropertyValue('--neuron-core'), accent);
    const neuronLine = parseColor(styles.getPropertyValue('--neuron-line'), accent);

    palette.node = accent;
    palette.link = neuronLine;
    palette.glow = neuronCore;
  }

  function rgba(rgb, alpha) {
    return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
  }

  function particleCountForSize() {
    const area = width * height;
    // lower divisor yields more particles to fill the larger brain region
    const base = Math.round(area / 17000);
    const min = prefersReducedMotion.matches ? 40 : 80;
    const max = prefersReducedMotion.matches ? 80 : 200;
    return clamp(base, min, max);
  }

  function createParticle() {
    const angle = Math.random() * Math.PI * 2;
    const speed = 0.18 + Math.random() * 0.56;
    return {
      x: Math.random() * width,
      y: Math.random() * height,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      size: 0.8 + Math.random() * 1.55,
      wobble: Math.random() * Math.PI * 2,
      energy: 0.5 + Math.random() * 0.5,
    };
  }

  function createParticleInsideMask() {
    // repeatedly generate until the point lies within the brain shape
    let p;
    do {
      p = createParticle();
    } while (brainMask && !ctx.isPointInPath(brainMask, p.x, p.y));
    return p;
  }

  function initParticles() {
    const count = particleCountForSize();
    particles = [];
    for (let i = 0; i < count; i += 1) {
      particles.push(createParticleInsideMask());
    }
  }

  function resizeCanvas() {
    width = Math.max(window.innerWidth, 1);
    height = Math.max(window.innerHeight, 1);
    dpr = clamp(window.devicePixelRatio || 1, 1, 2);

    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    updateMask();
    initParticles();
  }

  function randomImpulse(particle, factor) {
    const impulseAngle = Math.random() * Math.PI * 2;
    const impulse = (0.035 + Math.random() * 0.16) * factor;
    particle.vx += Math.cos(impulseAngle) * impulse;
    particle.vy += Math.sin(impulseAngle) * impulse;
  }

  function updateParticle(particle, step, time) {
    particle.wobble += (0.012 + (particle.energy * 0.02)) * step;

    if (Math.random() < 0.0095 * step) {
      randomImpulse(particle, 1.0);
    }

    particle.vx += (Math.random() - 0.5) * 0.022 * step;
    particle.vy += (Math.random() - 0.5) * 0.022 * step;

    const driftAngle = Math.sin((time * 0.00023) + particle.wobble) * Math.PI;
    particle.vx += Math.cos(driftAngle) * 0.0042 * step;
    particle.vy += Math.sin(driftAngle) * 0.0042 * step;

    const speed = Math.hypot(particle.vx, particle.vy);
    const minSpeed = 0.05;
    const maxSpeed = prefersReducedMotion.matches ? 0.42 : 1.04;

    if (speed > maxSpeed) {
      const ratio = maxSpeed / speed;
      particle.vx *= ratio;
      particle.vy *= ratio;
    } else if (speed < minSpeed) {
      const angle = Math.random() * Math.PI * 2;
      particle.vx = Math.cos(angle) * minSpeed;
      particle.vy = Math.sin(angle) * minSpeed;
    }

    particle.x += particle.vx * step;
    particle.y += particle.vy * step;

    // bounce off borders of canvas
    if (particle.x <= 0 || particle.x >= width) {
      particle.vx *= -1;
      particle.x = clamp(particle.x, 0, width);
      randomImpulse(particle, 0.35);
    }

    if (particle.y <= 0 || particle.y >= height) {
      particle.vy *= -1;
      particle.y = clamp(particle.y, 0, height);
      randomImpulse(particle, 0.35);
    }

    // keep particles inside the brain mask
    if (brainMask && !ctx.isPointInPath(brainMask, particle.x, particle.y)) {
      // simple reflect
      particle.vx *= -1;
      particle.vy *= -1;
      // nudge back towards center
      const cx = width * 0.5;
      const cy = height * 0.5;
      const ang = Math.atan2(cy - particle.y, cx - particle.x);
      particle.vx += Math.cos(ang) * 0.2;
      particle.vy += Math.sin(ang) * 0.2;
    }
  }

  function drawLinks(maxDistance) {
    const maxDistSq = maxDistance * maxDistance;
    for (let i = 0; i < particles.length; i += 1) {
      const a = particles[i];
      for (let j = i + 1; j < particles.length; j += 1) {
        const b = particles[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const distSq = (dx * dx) + (dy * dy);
        if (distSq > maxDistSq) continue;

        const strength = 1 - (distSq / maxDistSq);
        const alpha = clamp(0.02 + (strength * 0.24), 0, 0.28);

        ctx.strokeStyle = rgba(palette.link, alpha);
        ctx.lineWidth = 0.65 + (strength * 0.55);
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }
    }
  }

  function drawNodes(time) {
    for (let i = 0; i < particles.length; i += 1) {
      const p = particles[i];
      const pulse = 0.58 + (Math.sin((time * 0.0035) + p.wobble) * 0.42);
      const radius = p.size * (0.85 + (pulse * 0.38));

      ctx.fillStyle = rgba(palette.node, 0.30 + (pulse * 0.26));
      ctx.beginPath();
      ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = rgba(palette.glow, 0.10 + (pulse * 0.14));
      ctx.beginPath();
      ctx.arc(p.x, p.y, radius * 2.15, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function animate(time) {
    animationId = window.requestAnimationFrame(animate);

    if (!lastTick) {
      lastTick = time;
    }

    const delta = clamp(time - lastTick, 0, 32);
    const step = delta / 16.6667;
    lastTick = time;

    ctx.clearRect(0, 0, width, height);

    if (prefersReducedMotion.matches && (time % 2 > 1.2)) {
      return;
    }

    const linkDistance = clamp(Math.sqrt((width * height) / 30), 84, 160);

    for (let i = 0; i < particles.length; i += 1) {
      updateParticle(particles[i], step, time);
    }

    // draw only inside the brain silhouette
    if (brainMask) {
      ctx.save();
      ctx.clip(brainMask);
    }

    drawLinks(linkDistance);
    drawNodes(time);

    if (brainMask) {
      ctx.restore();
    }
  }

  function start() {
    if (animationId) {
      cancelAnimationFrame(animationId);
      animationId = 0;
    }
    lastTick = 0;
    animationId = requestAnimationFrame(animate);
  }

  function handleResize() {
    if (resizeTimer) {
      clearTimeout(resizeTimer);
    }
    resizeTimer = setTimeout(() => {
      resizeCanvas();
    }, 90);
  }

  function onVisibilityChange() {
    if (document.hidden) {
      if (animationId) {
        cancelAnimationFrame(animationId);
        animationId = 0;
      }
      return;
    }
    start();
  }

  updatePalette();
  resizeCanvas();
  start();

  window.addEventListener('resize', handleResize);
  document.addEventListener('visibilitychange', onVisibilityChange);

  const themeObserver = new MutationObserver(() => {
    updatePalette();
  });

  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme'],
  });

  if (document.body) {
    themeObserver.observe(document.body, {
      attributes: true,
      attributeFilter: ['data-theme'],
    });
  }
})();
