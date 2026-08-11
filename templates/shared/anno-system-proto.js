/*
 * 标注系统 - 原型端 JS (Annotation System - Prototype Side)
 *
 * 使用方式：在原型 HTML 的 </body> 前添加：
 *   <script src="../../../templates/shared/anno-system-proto.js"></script>
 *
 * 依赖：
 *   - anno-system.css（标注 marker + drawer 样式）
 *   - 页面内 <script id="annoDetailData" type="application/json"> 数据块
 *   - 页面内 drawer HTML（anno-drawer-backdrop + anno-drawer）
 *   - 页面内 .annotation-marker div（绝对定位红色圆圈）
 *
 * 功能：
 *   1. 接收 PRD 端 postMessage 切换标注可见性
 *   2. URL 参数 ?annotations=1 也可激活
 *   3. 点击 marker 向 parent 发送 annotation-clicked
 *   4. 独立模式下直接打开 drawer
 */

// ===== 标注可见性切换（不依赖 DOM，最先执行） =====
window.addEventListener('message', function(e) {
  if (e.data && e.data.type === 'toggle-annotations') {
    document.body.classList.toggle('show-annotations', e.data.show);
  }
});

// URL 参数通道
(function() {
  if (location.search.indexOf('annotations=1') !== -1 || location.hash === '#annotations') {
    document.body.classList.add('show-annotations');
  }
})();

// ===== 工具函数 =====
function escHtml(str) {
  var d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

// ===== Annotation Drawer =====
var annoData = null;
var annoDataEl = document.getElementById('annoDetailData');
if (annoDataEl) {
  try { annoData = JSON.parse(annoDataEl.textContent); }
  catch(e) { console.warn('标注数据解析失败', e); }
}

var annoDrawer = document.getElementById('annoDrawer');
var annoBackdrop = document.getElementById('annoDrawerBackdrop');
var annoDrawerTitle = document.getElementById('annoDrawerTitle');
var annoDrawerBody = document.getElementById('annoDrawerBody');

function openAnnoDrawer(data, highlightNum) {
  if (!annoDrawer || !annoDrawerBody) return;
  annoDrawerTitle.textContent = data.section + ' — 标注点说明';

  if (data && data.items && data.items.length) {
    var html = '';
    data.items.forEach(function(item) {
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
    annoDrawerBody.innerHTML = html;

    // Card header click toggle
    annoDrawerBody.querySelectorAll('.anno-card__header').forEach(function(header) {
      header.addEventListener('click', function() { this.parentElement.classList.toggle('open'); });
    });

    // Scroll to highlighted card
    var hlCard = annoDrawerBody.querySelector('.anno-card.highlight');
    if (hlCard) setTimeout(function() { hlCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }, 50);
  }

  annoDrawer.classList.add('open');
  if (annoBackdrop) annoBackdrop.classList.add('open');
}

function closeAnnoDrawer() {
  if (annoDrawer) annoDrawer.classList.remove('open');
  if (annoBackdrop) annoBackdrop.classList.remove('open');
}

// Drawer close handlers
if (document.getElementById('annoDrawerClose')) {
  document.getElementById('annoDrawerClose').addEventListener('click', closeAnnoDrawer);
}
if (annoBackdrop) {
  annoBackdrop.addEventListener('click', closeAnnoDrawer);
}

// ===== Marker Click → postMessage to parent / standalone open =====
document.querySelectorAll('.annotation-marker').forEach(function(marker) {
  marker.addEventListener('click', function(e) {
    e.stopPropagation();
    var number = parseInt(marker.textContent);
    if (window.parent !== window) {
      window.parent.postMessage({ type: 'annotation-clicked', number: number }, '*');
    } else if (annoData) {
      openAnnoDrawer(annoData, number);
    }
  });
});
