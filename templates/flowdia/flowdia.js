/* ============================================================
 * flowdia · 交互式流程图组件（JS）
 * 标准文档：docs/rules/flow-diagram-standard.md
 * 功能：SVG 连线路由（直线/肘形/扇出/通道/回环/上绕）、流向动画、
 *       悬停链路高亮、进场渐入、ResizeObserver 自适应重绘
 * 用法：页面底部 <script> 注入本文件内容；每个 .flowdia 容器内
 *       以 <script type="application/json" class="fd-edges"> 配置边
 * ============================================================ */
(function () {
  const diagrams = document.querySelectorAll('.flowdia');
  if (!diagrams.length) return;
  const NS = 'http://www.w3.org/2000/svg';

  function rectOf(el, root) {
    const r = el.getBoundingClientRect(), p = root.getBoundingClientRect();
    return {
      x: r.left - p.left, y: r.top - p.top, w: r.width, h: r.height,
      cx: r.left - p.left + r.width / 2, cy: r.top - p.top + r.height / 2,
      left: r.left - p.left, right: r.right - p.left,
      top: r.top - p.top, bottom: r.bottom - p.top
    };
  }

  function orthPath(pts, r) {
    let d = `M${pts[0][0]},${pts[0][1]}`;
    for (let i = 1; i < pts.length - 1; i++) {
      const [px, py] = pts[i - 1], [cx, cy] = pts[i], [nx, ny] = pts[i + 1];
      const v1x = cx - px, v1y = cy - py, v2x = nx - cx, v2y = ny - cy;
      const l1 = Math.hypot(v1x, v1y), l2 = Math.hypot(v2x, v2y);
      if (!l1 || !l2) continue;
      const rr = Math.min(r, l1 / 2, l2 / 2);
      const sx = cx - (v1x / l1) * rr, sy = cy - (v1y / l1) * rr;
      const ex = cx + (v2x / l2) * rr, ey = cy + (v2y / l2) * rr;
      d += ` L${sx},${sy} Q${cx},${cy} ${ex},${ey}`;
    }
    const last = pts[pts.length - 1];
    d += ` L${last[0]},${last[1]}`;
    return d;
  }

  function build(dia) {
    const svg = dia.querySelector('.fd-svg');
    const edges = JSON.parse(dia.querySelector('.fd-edges').textContent);
    dia._edges = edges;
    dia.querySelectorAll('.fd-label').forEach(l => l.remove());
    svg.innerHTML = '';
    const W = dia.offsetWidth, H = dia.offsetHeight;
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);

    const defs = document.createElementNS(NS, 'defs');
    svg.appendChild(defs);
    const markers = {};
    function marker(color) {
      if (markers[color]) return markers[color];
      const id = 'fdm-' + color.replace(/[^0-9a-fA-F]/g, '');
      const m = document.createElementNS(NS, 'marker');
      m.setAttribute('id', id); m.setAttribute('markerWidth', '11'); m.setAttribute('markerHeight', '11');
      m.setAttribute('markerUnits', 'userSpaceOnUse');
      m.setAttribute('refX', '8.6'); m.setAttribute('refY', '4'); m.setAttribute('orient', 'auto');
      const p = document.createElementNS(NS, 'path');
      p.setAttribute('d', 'M0,0.4 L9.6,4 L0,7.6 Z'); p.setAttribute('fill', color);
      p.setAttribute('stroke-linejoin', 'round');
      m.appendChild(p); defs.appendChild(m); markers[color] = id;
      return id;
    }

    const nodes = {};
    dia.querySelectorAll('.fn[data-id]').forEach(n => { nodes[n.dataset.id] = rectOf(n, dia); });

    edges.forEach(e => {
      const a = nodes[e.f], b = nodes[e.t];
      if (!a || !b) return;
      let d;
      const dx = b.cx - a.cx, dy = b.cy - a.cy;
      if (e.kind === 'loop') {
        const ly = H - 16;
        d = orthPath([[a.cx, a.bottom], [a.cx, ly], [b.cx, ly], [b.cx, b.bottom]], 10);
      } else if (e.kind === 'gate') {
        // 直角肘形：源底部中央垂直下行 → 卡片上方 26px 净空横移 → 落入目标顶部
        const yt = b.top - 26;
        d = orthPath([[a.cx, a.bottom], [a.cx, yt], [b.cx, yt], [b.cx, b.top]], 10);
      } else if (e.kind === 'channel') {
        // 右侧空列通道：源底部右出 → 右移入空列 → 垂直下行 → 卡片上方 26px 净空横移 → 落入目标顶部
        const x0 = a.right - 14, x1 = a.right + 14, yt = b.top - 26;
        d = orthPath([[x0, a.bottom], [x0, a.bottom + 14], [x1, a.bottom + 14], [x1, yt], [b.cx, yt], [b.cx, b.top]], 10);
      } else if (e.kind === 'fan') {
        // 扇出肘形：源右侧指定高度出 → 独立竖向通道 → 目标左侧水平进入
        const y0 = a.top + a.h * (e.fy || 0.5), laneX = a.right + (e.lane || 24);
        d = orthPath([[a.right, y0], [laneX, y0], [laneX, b.cy], [b.left, b.cy]], 8);
      } else if (e.kind === 'up-left') {
        const sx = a.left + 18, txp = b.right - 18;
        d = `M${sx},${a.top} C${sx},${a.top - 42} ${txp},${b.bottom + 42} ${txp},${b.bottom}`;
      } else if (e.kind === 'down') {
        // 垂直下落：源底部（sx 可偏移）垂直下行 → 落入目标顶部（tx 可偏移）
        const sx = a.cx + (e.sx || 0), txp = b.cx + (e.tx || 0);
        const h = Math.max(24, Math.abs(dy) / 2);
        d = `M${sx},${a.bottom} C${sx},${a.bottom + h} ${txp},${b.top - h} ${txp},${b.top}`;
      } else if (Math.abs(dy) < 8) {
        const h = Math.max(30, Math.abs(dx) / 2);
        d = `M${a.right},${a.cy} C${a.right + h},${a.cy} ${b.left - h},${b.cy} ${b.left},${b.cy}`;
      } else if (Math.abs(dx) < 8) {
        const h = Math.max(24, Math.abs(dy) / 2);
        d = `M${a.cx},${a.bottom} C${a.cx},${a.bottom + h} ${b.cx},${b.top - h} ${b.cx},${b.top}`;
      } else if (e.enter === 'bottom') {
        const sx = a.right, txp = b.cx + (e.tx || 0);
        d = `M${sx},${a.cy} C${sx + 50},${a.cy} ${txp},${b.bottom + 42} ${txp},${b.bottom}`;
      } else {
        const rightward = b.cx > a.cx;
        const sx = rightward ? a.right : a.left, txp = rightward ? b.left : b.right;
        const h = Math.max(40, Math.abs(dx) / 2);
        d = `M${sx},${a.cy} C${sx + (rightward ? h : -h)},${a.cy} ${txp + (rightward ? -h : h)},${b.cy} ${txp},${b.cy}`;
      }

      const color = e.c || '#9aa4b2';
      const path = document.createElementNS(NS, 'path');
      path.setAttribute('d', d);
      path.setAttribute('class', 'fd-edge' + (e.solid ? ' fd-solid' : '') + (e.kind === 'loop' ? ' fd-loop' : ''));
      path.setAttribute('stroke', color);
      if (e.w) path.style.strokeWidth = e.w;
      path.setAttribute('marker-end', `url(#${marker(color)})`);
      path.dataset.f = e.f; path.dataset.t = e.t;
      svg.appendChild(path);

      if (e.label) {
        const pt = path.getPointAtLength(path.getTotalLength() * (e.lx || 0.5));
        const lb = document.createElement('div');
        lb.className = 'fd-label' + (e.strong ? ' fd-strong' : '');
        lb.textContent = e.label;
        lb.style.left = (pt.x + (e.ox || 0)) + 'px'; lb.style.top = (pt.y + (e.oy || 0)) + 'px';
        lb.style.color = color; lb.style.borderColor = color + '55';
        lb.dataset.f = e.f; lb.dataset.t = e.t;
        dia.appendChild(lb);
      }
    });
  }

  function wire(dia) {
    dia.querySelectorAll('.fn[data-id]').forEach(n => {
      n.addEventListener('mouseenter', () => {
        const id = n.dataset.id;
        dia.classList.add('focusing');
        n.classList.add('fd-hot');
        (dia._edges || []).forEach(e => {
          if (e.f !== id && e.t !== id) return;
          const other = e.f === id ? e.t : e.f;
          const on = dia.querySelector(`.fn[data-id="${other}"]`);
          if (on) on.classList.add('fd-hot');
          dia.querySelectorAll(`path.fd-edge[data-f="${e.f}"][data-t="${e.t}"], .fd-label[data-f="${e.f}"][data-t="${e.t}"]`)
            .forEach(el => el.classList.add('fd-hot'));
        });
      });
      n.addEventListener('mouseleave', () => {
        dia.classList.remove('focusing');
        dia.querySelectorAll('.fd-hot').forEach(el => el.classList.remove('fd-hot'));
      });
    });
  }

  diagrams.forEach(dia => {
    dia.classList.add('fd-arm');
    // 节点进场阶梯延迟
    dia.querySelectorAll('.fn[data-id]').forEach((n, i) => n.style.setProperty('--i', i));
    build(dia);
    wire(dia);

    // 进场动画
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => {
        if (!en.isIntersecting) return;
        dia.classList.add('fd-in');
        const cnt = dia.querySelectorAll('.fn[data-id]').length;
        setTimeout(() => dia.classList.add('fd-done'), cnt * 55 + 700);
        io.disconnect();
      });
    }, { threshold: 0.15 });
    io.observe(dia);

    // 自适应重绘
    let raf = null;
    const schedule = () => { if (raf) return; raf = requestAnimationFrame(() => { raf = null; build(dia); }); };
    if (window.ResizeObserver) new ResizeObserver(schedule).observe(dia);
    window.addEventListener('load', schedule);
    setTimeout(schedule, 600);
  });
})();
