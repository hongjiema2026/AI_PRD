/*
 * 标注系统 - PRD 端 JS (Annotation System - PRD Side)
 *
 * 使用方式：在 PRD HTML 的 </body> 前添加：
 *   <script src="../../../templates/shared/anno-system-prd.js"></script>
 *
 * 前置依赖：
 *   - anno-system.css（标注切换按钮 + drawer + card 样式）
 *   - 页面内 .proto-embed 元素（含 data-proto-src 属性）
 *   - 页面内 <script class="anno-detail-data"> JSON 数据块
 *   - 页面内 <table class="anno-table"> 标注点表格
 *   - 页面内 drawer HTML（anno-drawer-backdrop + anno-drawer）
 *   - 页面内 proto-fullscreen-overlay（含 proto-fs-annotations 按钮）
 *
 * 功能：
 *   1. 内联 iframe 标注切换（直接 DOM 操作，降级 postMessage）
 *   2. 全屏模式标注切换
 *   3. iframe marker 点击 → 直接打开详情抽屉（capture 阶段拦截）
 *   4. anno-table 行点击 → 打开详情抽屉
 */

// ===== 工具函数 =====
function escHtml(str) {
  var d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

// ===== 查找 anno-detail-data JSON =====
function findDetailData(sectionName) {
  var scripts = document.querySelectorAll('script.anno-detail-data');
  for (var i = 0; i < scripts.length; i++) {
    if (scripts[i].dataset.section === sectionName) {
      try { return JSON.parse(scripts[i].textContent); } catch(e) { return null; }
    }
  }
  return null;
}

// ===== Annotation Drawer（实时查找，避免加载时序问题） =====
function _getDrawer() {
  return {
    drawer: document.getElementById('annoDrawer'),
    backdrop: document.getElementById('annoDrawerBackdrop'),
    title: document.getElementById('annoDrawerTitle'),
    body: document.getElementById('annoDrawerBody')
  };
}

function openAnnoDrawer(sectionName, items, highlightNum, detailData) {
  var d = _getDrawer();
  if (!d.drawer || !d.body) return;
  d.title.textContent = sectionName + ' — 标注点说明';

  if (detailData && detailData.items && detailData.items.length) {
    // ── Detail mode: render expandable cards ──
    var html = '';
    detailData.items.forEach(function(item) {
      var isOpen = item.num == highlightNum;
      var hl = isOpen ? ' highlight open' : '';
      html += '<div class="anno-card' + hl + '" data-num="' + item.num + '">';
      html += '<div class="anno-card__header">' +
        '<span class="anno-card__num">' + item.num + '</span>' +
        '<span class="anno-card__title">' + escHtml(item.title) + '</span>' +
        '<span class="anno-card__toggle">▸</span></div>';
      html += '<div class="anno-card__body">';
      if (item.summary) {
        html += '<div class="anno-card__section"><div class="anno-card__label">概述</div>' +
          '<div class="anno-card__text">' + escHtml(item.summary) + '</div></div>';
      }
      if (item.fields && item.fields.length) {
        html += '<div class="anno-card__section"><div class="anno-card__label">字段清单</div>' +
          '<table class="anno-field-table"><thead><tr>' +
          '<th>字段</th><th>类型</th><th>必填</th><th>规则</th><th>来源/计算</th>' +
          '</tr></thead><tbody>';
        item.fields.forEach(function(f) {
          html += '<tr><td>' + escHtml(f.name) + '</td><td>' + escHtml(f.type) + '</td>' +
            '<td>' + (f.required ? '<span class="tag-required">必填</span>' : '<span class="tag-optional">选填</span>') + '</td>' +
            '<td>' + escHtml(f.rules || '') + '</td>' +
            '<td>' + (f.source ? escHtml(f.source) : '—') + '</td></tr>';
        });
        html += '</tbody></table></div>';
      }
      if (item.interactions && item.interactions.length) {
        html += '<div class="anno-card__section"><div class="anno-card__label">交互规则</div><ul class="anno-card__list">';
        item.interactions.forEach(function(r) { html += '<li>' + escHtml(r) + '</li>'; });
        html += '</ul></div>';
      }
      if (item.validations && item.validations.length) {
        html += '<div class="anno-card__section"><div class="anno-card__label">校验规则</div><ul class="anno-card__list">';
        item.validations.forEach(function(v) { html += '<li>' + escHtml(v) + '</li>'; });
        html += '</ul></div>';
      }
      if (item.states && item.states.length) {
        html += '<div class="anno-card__section"><div class="anno-card__label">状态说明</div><div class="anno-card__states">';
        item.states.forEach(function(s) { html += '<span class="state-badge">' + escHtml(s) + '</span>'; });
        html += '</div></div>';
      }
      html += '</div></div>';
    });
    d.body.innerHTML = html;

    // Card expand/collapse
    d.body.querySelectorAll('.anno-card__header').forEach(function(header) {
      header.addEventListener('click', function() { this.parentElement.classList.toggle('open'); });
    });

    // Scroll to highlighted card
    var hlCard = d.body.querySelector('.anno-card.highlight');
    if (hlCard) setTimeout(function() { hlCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }, 50);
  } else {
    // ── Fallback mode: simple list ──
    var html = '';
    items.forEach(function(item) {
      var hl = item.num == highlightNum ? ' highlight' : '';
      html += '<div class="anno-drawer-item' + hl + '">' +
        '<span class="anno-num">' + item.num + '</span>' +
        '<span class="anno-content">' + escHtml(item.content) + '</span>' +
        '<div class="anno-desc">' + escHtml(item.desc) + '</div></div>';
    });
    d.body.innerHTML = html;
  }

  d.drawer.classList.add('open');
  if (d.backdrop) d.backdrop.classList.add('open');
}

function closeAnnoDrawer() {
  var d = _getDrawer();
  if (d.drawer) d.drawer.classList.remove('open');
  if (d.backdrop) d.backdrop.classList.remove('open');
}

// Drawer close handlers（null 安全）
(function() {
  var closeBtn = document.getElementById('annoDrawerClose');
  if (closeBtn) closeBtn.addEventListener('click', closeAnnoDrawer);
  var backdrop = document.getElementById('annoDrawerBackdrop');
  if (backdrop) backdrop.addEventListener('click', closeAnnoDrawer);
})();

// ===== 查找 proto-embed 对应的 anno-table =====
function findAnnoTableForEmbed(embed) {
  var section = embed.closest('section');
  if (!section) return null;
  return section.querySelector('.anno-table');
}

function findAnnoTableBySrc(src) {
  var fileName = src.split('/').pop().split('?')[0];
  var embeds = document.querySelectorAll('.proto-embed[data-proto-src]');
  for (var i = 0; i < embeds.length; i++) {
    var embedFileName = embeds[i].dataset.protoSrc.split('/').pop().split('?')[0];
    if (embedFileName === fileName) {
      return findAnnoTableForEmbed(embeds[i]);
    }
  }
  return document.querySelector('.anno-table') || null;
}

// ===== 直接 DOM 操作工具函数 =====

// 检测 iframe contentDocument 是否可访问（同源检测）
function canAccessIframe(iframe) {
  try {
    return !!(iframe.contentDocument && iframe.contentDocument.body);
  } catch(e) {
    return false;
  }
}

// 核心切换：优先直接 DOM → 降级 postMessage → 兜底 URL 参数
function applyAnnotationState(iframe, show) {
  if (canAccessIframe(iframe)) {
    // 通道1：直接 DOM（同源可用，如本地服务器）
    iframe.contentDocument.body.classList.toggle('show-annotations', show);
  } else {
    // 通道2：postMessage（同源可用）
    try { iframe.contentWindow.postMessage({ type: 'toggle-annotations', show: show }, '*'); } catch(e) {}
    // 通道3：URL 参数回退（file:// 跨域兜底）
    setTimeout(function() {
      if (canAccessIframe(iframe)) return; // postMessage 成功则跳过
      try {
        var src = iframe.src || '';
        var hIdx = src.indexOf('#'), hash = hIdx !== -1 ? src.substring(hIdx) : '';
        var qIdx = src.indexOf('?');
        var base = qIdx !== -1 ? src.substring(0, qIdx) : (hIdx !== -1 ? src.substring(0, hIdx) : src);
        // 保留既有参数（如 modal=xxx），仅增删 annotations，避免丢失弹窗等状态
        var sp = new URLSearchParams(qIdx !== -1 ? src.substring(qIdx + 1).split('#')[0] : '');
        var hadAnno = sp.get('annotations') === '1';
        if (show && !hadAnno) sp.set('annotations', '1');
        else if (!show && hadAnno) sp.delete('annotations');
        else return; // 已处于目标状态，幂等返回，避免无限重载闪烁
        var qs = sp.toString();
        var target = base + (qs ? '?' + qs : '') + hash;
        if (iframe.src !== target) iframe.src = target; // 目标相同则不赋值，避免重载
      } catch(e) {}
    }, 100);
  }
}

// 打开 drawer 的内部逻辑（供 marker 点击和 anno-table 共用）
function openDrawerByAnnoTable(annoTable, highlightNum) {
  var sectionName = annoTable.dataset.section || '';
  var rows = annoTable.querySelectorAll('tr[data-anno]');
  var items = [];
  rows.forEach(function(row) {
    var cells = row.querySelectorAll('td');
    if (cells.length >= 3) {
      items.push({ num: row.dataset.anno, content: cells[1].textContent, desc: cells[2].textContent });
    }
  });
  var detailData = findDetailData(sectionName);
  openAnnoDrawer(sectionName, items, highlightNum, detailData);
}

// 在 iframe 内拦截 marker 点击（capture 阶段，优先于 proto 端 handler）
function bindIframeMarkerClicks(iframe, isFullscreen) {
  if (!canAccessIframe(iframe)) return;
  var doc = iframe.contentDocument;

  // 解绑旧 handler
  if (iframe._annoClickHandler) {
    try { doc.removeEventListener('click', iframe._annoClickHandler, true); } catch(e) {}
  }

  function handler(e) {
    var marker = null;
    var el = e.target;
    while (el && el !== doc) {
      if (el.classList && el.classList.contains('annotation-marker')) { marker = el; break; }
      el = el.parentElement;
    }
    if (!marker) return;

    var number = parseInt(marker.textContent, 10);
    if (isNaN(number)) return;

    // 查找对应的 anno-table
    var annoTable;
    if (isFullscreen) {
      annoTable = findAnnoTableBySrc(iframe.src);
    } else {
      var parent = iframe.parentElement;
      while (parent) {
        if (parent.classList && parent.classList.contains('proto-embed')) break;
        parent = parent.parentElement;
      }
      annoTable = parent ? findAnnoTableForEmbed(parent) : null;
    }
    if (!annoTable) return;

    openDrawerByAnnoTable(annoTable, number);
  }

  iframe._annoClickHandler = handler;
  doc.addEventListener('click', handler, true); // capture phase
}

function unbindIframeMarkerClicks(iframe) {
  if (iframe._annoClickHandler) {
    if (canAccessIframe(iframe)) {
      try { iframe.contentDocument.removeEventListener('click', iframe._annoClickHandler, true); } catch(e) {}
    }
    iframe._annoClickHandler = null;
  }
}

// ===== 内联 iframe 标注切换（直接 DOM 操作） =====

// :not(#proto-fs-annotations) 排除全屏按钮，避免 double-bind
document.querySelectorAll('.proto-anno-btn:not(#proto-fs-annotations)').forEach(function(btn) {
  btn.addEventListener('click', function() {
    var embed = btn.closest('.proto-embed');
    if (!embed) return;
    var iframe = embed.querySelector('iframe');
    if (!iframe) return;
    var isActive = btn.classList.toggle('active');
    btn.textContent = isActive ? '📍 隐藏标注' : '📍 显示标注';

    if (canAccessIframe(iframe)) {
      // iframe 已加载 → 直接操作 DOM
      applyAnnotationState(iframe, isActive);
      if (isActive) bindIframeMarkerClicks(iframe, false);
      else unbindIframeMarkerClicks(iframe);
    } else {
      // iframe 尚未加载（loading="lazy"）→ 记录待处理状态
      iframe._annoPendingShow = isActive;
      applyAnnotationState(iframe, isActive);
    }
  });
});

// 内联 iframe load 后重发标注状态 + 绑定 marker 点击
document.querySelectorAll('.proto-embed').forEach(function(embed) {
  var iframe = embed.querySelector('iframe');
  if (!iframe) return;
  var btn = embed.querySelector('.proto-anno-btn:not(#proto-fs-annotations)');
  iframe.addEventListener('load', function() {
    setTimeout(function() {
      // 重发按钮已有状态
      if (btn && btn.classList.contains('active')) {
        applyAnnotationState(iframe, true);
        bindIframeMarkerClicks(iframe, false);
      }
      // 处理未加载时的待处理状态
      if (iframe._annoPendingShow !== undefined) {
        applyAnnotationState(iframe, iframe._annoPendingShow);
        if (iframe._annoPendingShow) bindIframeMarkerClicks(iframe, false);
        delete iframe._annoPendingShow;
      }
    }, 50);
  });
});

// ===== 全屏模式标注切换（直接 DOM 操作） =====
var protoIframe = document.getElementById('proto-fs-iframe');
var annoBtn = document.getElementById('proto-fs-annotations');
var fsAnnoActive = false;

if (annoBtn && protoIframe) {
  protoIframe.addEventListener('load', function() {
    setTimeout(function() {
      if (fsAnnoActive) {
        applyAnnotationState(protoIframe, true);
        bindIframeMarkerClicks(protoIframe, true);
      }
    }, 50);
  });

  annoBtn.addEventListener('click', function() {
    fsAnnoActive = annoBtn.classList.toggle('active');
    annoBtn.textContent = fsAnnoActive ? '📍 隐藏标注' : '📍 显示标注';

    if (canAccessIframe(protoIframe)) {
      applyAnnotationState(protoIframe, fsAnnoActive);
      if (fsAnnoActive) bindIframeMarkerClicks(protoIframe, true);
      else unbindIframeMarkerClicks(protoIframe);
    } else {
      protoIframe._annoPendingShow = fsAnnoActive;
      applyAnnotationState(protoIframe, fsAnnoActive);
    }
  });
}

// ===== 接收 iframe annotation-clicked → 打开 drawer =====
window.addEventListener('message', function(e) {
  if (e.data && e.data.type === 'annotation-clicked') {
    var embeds = document.querySelectorAll('.proto-embed');
    var matchedEmbed = null;
    var isFullscreen = false;

    for (var i = 0; i < embeds.length; i++) {
      var iframe = embeds[i].querySelector('iframe');
      if (iframe && iframe.contentWindow === e.source) {
        matchedEmbed = embeds[i];
        break;
      }
    }

    if (!matchedEmbed && protoIframe && protoIframe.contentWindow === e.source) {
      isFullscreen = true;
    }

    var annoTable = isFullscreen
      ? findAnnoTableBySrc(protoIframe.src)
      : (matchedEmbed ? findAnnoTableForEmbed(matchedEmbed) : null);

    if (!annoTable) return;

    var sectionName = annoTable.dataset.section || '';
    var rows = annoTable.querySelectorAll('tr[data-anno]');
    var items = [];
    rows.forEach(function(row) {
      var cells = row.querySelectorAll('td');
      if (cells.length >= 3) {
        items.push({ num: row.dataset.anno, content: cells[1].textContent, desc: cells[2].textContent });
      }
    });
    var detailData = findDetailData(sectionName);
    openAnnoDrawer(sectionName, items, e.data.number, detailData);
  }
});

// ===== anno-table 行点击 → 打开 drawer =====
document.querySelectorAll('.anno-table').forEach(function(table) {
  table.addEventListener('click', function(e) {
    var td = e.target.closest('td');
    if (!td) return;
    var row = td.parentElement;
    if (!row.dataset.anno) return;
    if (td !== row.firstElementChild) return;
    var sectionName = table.dataset.section || '';
    var rows = table.querySelectorAll('tr[data-anno]');
    var items = [];
    rows.forEach(function(r) {
      var cells = r.querySelectorAll('td');
      if (cells.length >= 3) {
        items.push({ num: r.dataset.anno, content: cells[1].textContent, desc: cells[2].textContent });
      }
    });
    var detailData = findDetailData(sectionName);
    openAnnoDrawer(sectionName, items, row.dataset.anno, detailData);
  });
});

// ===== Escape 关闭 drawer =====
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    var d = _getDrawer();
    if (d.drawer && d.drawer.classList.contains('open')) {
      closeAnnoDrawer();
    }
  }
});
