---
title: PRD HTML 渲染规范
version: v1.7
date: 2026-08-10
status: active
---

# PRD HTML 渲染规范

| 属性 | 值 |
|------|-----|
| 版本 | v1.7 |
| 适用范围 | PRD 流水线 Writer Step 6（HTML 渲染）阶段 |
| 创建日期 | 2026-07-28 |
| 更新日期 | 2026-08-10 |
| 状态 | active |
| 关联文档 | `docs/rules/sop-writing-standard.md` §2.1（代码级规范例外条款）、`docs/rules/prd-diagram-standard.md`（D01-D08，H06 引用的图绘制标准） |

> 本文件仅在 Writer Step 6（HTML 渲染）阶段加载。其他阶段无需读取。
> 包含 H01-H07 完整规范：图片灯箱、原型内嵌、模态容器、CSS 变量化、可访问性、交互式流程图、文字排版。
> **代码级规范，允许超行**：本文件含完整 CSS/JS 模板，依 `docs/rules/sop-writing-standard.md` §2.1 例外条款不受 ≤500 行上限约束。

---

### H01：图片灯箱（Image Lightbox）

**CSS** — 替换原有 `img { ... }` 规则：

```css
/* ========== Images ========== */
.img-wrapper {
  margin: 16px 0;
  cursor: pointer;
  position: relative;
  display: inline-block;
  max-width: 100%;
}
.img-wrapper img {
  max-width: 100%;
  max-height: 600px;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  display: block;
  transition: box-shadow 0.2s ease, transform 0.15s ease;
}
.img-wrapper:hover img {
  box-shadow: 0 4px 16px rgba(108,99,255,0.2);
  transform: scale(1.005);
}
.img-wrapper::after {
  content: '点击查看大图';
  position: absolute;
  bottom: 12px; right: 12px;
  background: rgba(0,0,0,0.55);
  color: #fff;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}
.img-wrapper:hover::after {
  opacity: 1;
}
.img-wrapper:focus-visible {
  outline: 2px solid #6c63ff;
  outline-offset: 4px;
  border-radius: 8px;
}
.img-wrapper:focus-visible img {
  box-shadow: 0 4px 16px rgba(108,99,255,0.2);
  transform: scale(1.005);
}
```

**HTML** — 每个图片用 `.img-wrapper` 包裹（含可访问性属性）：

```html
<div class="img-wrapper" data-title="图片标题" role="button" tabindex="0" aria-label="点击查看大图">
  <img src="path/to/image.png" alt="图片描述">
</div>
```

> ⚠️ `role="button"` + `tabindex="0"` 使图片容器可被键盘 Tab 聚焦；`aria-label` 为屏幕阅读器提供可点击提示（弥补 `::after` 伪元素不可访问的缺陷）。

### H02：原型内嵌（Prototype Embed）

**CSS**：

```css
/* ========== Prototype Embed ========== */
.proto-embed {
  margin: 16px 0 24px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.proto-embed-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #fafbfc;
  border-bottom: 1px solid #e4e7ed;
  font-size: 13px;
}
.proto-embed-header .proto-title {
  font-weight: 600;
  color: #333;
}
.proto-embed-header .proto-open-btn {
  background: #6c63ff;
  color: #fff;
  border: none;
  padding: 5px 14px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
}
.proto-embed-header .proto-open-btn:hover {
  background: #5a52e0;
}
.proto-embed-header .proto-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.proto-embed-header .proto-anno-btn {
  background: #fff;
  border: 1px solid #d0d0d0;
  padding: 5px 14px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  color: #333;
  transition: all 0.2s;
}
.proto-embed-header .proto-anno-btn:hover {
  border-color: #f56c6c; color: #f56c6c;
}
.proto-embed-header .proto-anno-btn.active {
  background: #f56c6c; color: #fff; border-color: #f56c6c;
}
.anno-table td:first-child { cursor: pointer; color: var(--color-primary); font-weight: 700; }
.anno-table td:first-child:hover { text-decoration: underline; }
.anno-drawer-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.3);
  z-index: 10002; opacity: 0; visibility: hidden;
  transition: opacity 0.3s ease, visibility 0.3s ease;
}
.anno-drawer-backdrop.open { opacity: 1; visibility: visible; }
.anno-drawer {
  position: fixed; top: 0; right: 0; bottom: 0; width: 50vw; /* 占屏幕宽 50% */
  background: #fff; box-shadow: -4px 0 24px rgba(0,0,0,0.12);
  z-index: 10003; transform: translateX(100%);
  transition: transform 0.3s cubic-bezier(0.4,0,0.2,1);
  display: flex; flex-direction: column; overflow: hidden;
}
.anno-drawer.open { transform: translateX(0); }
/* 移动端 50% 过窄不可用，改为全屏抽屉 */
@media (max-width: 768px) {
  .anno-drawer { width: 100vw; }
}
.anno-drawer-header { padding: 16px 20px; border-bottom: 1px solid #eee; display: flex; align-items: center; justify-content: space-between; flex-shrink: 0; }
.anno-drawer-header h4 { font-size: 15px; margin: 0; color: #1a1a2e; }
.anno-drawer-close { background: none; border: none; font-size: 22px; cursor: pointer; color: #999; padding: 4px 8px; line-height: 1; }
.anno-drawer-close:hover { color: #333; }
.anno-drawer-body { flex: 1; overflow-y: auto; }
.anno-drawer-item { padding: 14px 20px; border-bottom: 1px solid #f0f0f0; border-left: 3px solid transparent; transition: all 0.15s; }
.anno-drawer-item.highlight { background: #eef2ff; border-left-color: #2563eb; }
.anno-drawer-item .anno-num { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 50%; background: #f56c6c; color: #fff; font-size: 12px; font-weight: 700; margin-right: 10px; vertical-align: middle; }
.anno-drawer-item .anno-content { font-weight: 600; font-size: 14px; color: #333; display: inline; vertical-align: middle; }
.anno-drawer-item .anno-desc { margin-top: 6px; font-size: 13px; color: #666; line-height: 1.6; padding-left: 32px; }
/* ========== Annotation Card (Detail Mode) ========== */
.anno-card { border-bottom: 1px solid #f0f0f0; border-left: 3px solid transparent; transition: all 0.15s; }
.anno-card.highlight { background: #eef2ff; border-left-color: #2563eb; }
.anno-card__header { display: flex; align-items: center; padding: 14px 20px; cursor: pointer; user-select: none; }
.anno-card__header:hover { background: #fafafa; }
.anno-card__num { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 50%; background: #f56c6c; color: #fff; font-size: 12px; font-weight: 700; margin-right: 10px; flex-shrink: 0; }
.anno-card__title { font-weight: 600; font-size: 14px; color: #333; flex: 1; }
.anno-card__toggle { font-size: 12px; color: #999; transition: transform 0.2s; }
.anno-card.open .anno-card__toggle { transform: rotate(90deg); }
.anno-card__body { display: none; padding: 0 20px 16px 52px; }
.anno-card.open .anno-card__body { display: block; }
.anno-card__section { margin-bottom: 12px; }
.anno-card__label { font-size: 12px; font-weight: 600; color: #2563eb; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
.anno-card__text { font-size: 13px; color: #555; line-height: 1.6; }
.anno-card__list { margin: 0; padding-left: 18px; font-size: 13px; color: #555; line-height: 1.7; }
.anno-field-table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 4px; }
.anno-field-table th { background: #f5f7fa; text-align: left; padding: 6px 8px; font-weight: 600; color: #666; border-bottom: 1px solid #e4e7ed; }
.anno-field-table td { padding: 5px 8px; border-bottom: 1px solid #f0f0f0; color: #444; vertical-align: top; }
.tag-required { display: inline-block; background: #fef0f0; color: #f56c6c; padding: 1px 6px; border-radius: 3px; font-size: 11px; font-weight: 600; }
.tag-optional { display: inline-block; background: #f0f5ff; color: #409eff; padding: 1px 6px; border-radius: 3px; font-size: 11px; }
.anno-card__states { display: flex; gap: 6px; flex-wrap: wrap; }
.state-badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 500; }
.state-badge.state-active { background: #e6f7e9; color: #52c41a; }
.state-badge.state-paused { background: #fff7e6; color: #faad14; }
.state-badge.state-draft { background: #f5f5f5; color: #999; }
.proto-embed iframe {
  width: 100%;
  height: 420px;
  border: none;
  display: block;
}
```

**HTML** — 在每个交互原型小节标题紧下方（`<h3>` 后、标注点说明等文字内容前）插入：

```html
<div class="proto-embed" data-proto-src="../prototype/proto-{name}.html" data-proto-title="模块名称" role="region" aria-label="原型预览：模块名称">
  <div class="proto-embed-header">
    <span class="proto-title">proto-{name}.html</span>
    <div class="proto-actions">
      <button class="proto-anno-btn">📍 显示标注</button>
      <button class="proto-open-btn">全屏查看</button>
    </div>
  </div>
  <iframe src="../prototype/proto-{name}.html" loading="lazy" title="模块名称原型预览"></iframe>
</div>
```

> ⚠️ iframe 必须有 `title` 属性（格式：`{模块名称}原型预览`），否则屏幕阅读器无法识别 iframe 用途。
> ⚠️ `.proto-embed` 添加 `role="region"` + `aria-label` 使原型区域成为可导航的地标。

### H02b：标注点详尽数据（anno-detail-data）

每个 `.anno-table` 的 `</table>` 后、`</section>` 前，必须插入 `<script class="anno-detail-data">` JSON 块：

```html
<script class="anno-detail-data" type="application/json" data-section="{与 .anno-table[data-section] 一致}">
{
  "section": "3.x 模块名称",
  "items": [
    {
      "num": 1,
      "title": "区块名称",
      "summary": "该区块的功能概述（1-3句）",
      "fields": [
        { "name": "字段名", "type": "控件类型", "required": true, "rules": "校验规则", "source": "数据来源或计算公式，无则 null" }
      ],
      "interactions": ["交互规则描述"],
      "validations": ["错误场景 → 提示信息"],
      "states": ["状态枚举（可选）"]
    }
  ]
}
</script>
```

> ⚠️ `data-section` 必须与对应的 `.anno-table[data-section]` 完全一致，否则 drawer 无法匹配数据。
> ⚠️ `fields.source`：有数据来源或计算规则的字段必须填写，纯手动输入字段填 `null`。
> ⚠️ **四要素渲染（强制）**：无论用动态 JSON 渲染还是静态 HTML，每个标注项的详情必须按四块展示——📋 **字段说明**（字段名/类型/必填/校验/来源）、📏 **规则说明**（引用规则编号 + 具体约束）、🔀 **判断逻辑**（状态/条件分支）、🖱 **交互说明**（操作行为与反馈）。详情默认收起，标注项被选中（点击原型标注点或点击抽屉项）时展开。

### H03：模态容器 + JavaScript

> ⛔ **禁令**：「全屏查看」**禁止**使用 `window.open` 打开新浏览器窗口，必须使用本节的页面内全屏弹窗（`proto-fullscreen-overlay`）。弹窗内必须支持「📍 显示/隐藏标注」切换与 Esc 关闭。

**HTML** — 在 `</body>` 前插入：

```html
<!-- 图片灯箱 -->
<div class="lightbox-overlay" id="lightbox" role="dialog" aria-modal="true" aria-label="图片预览">
  <button class="lightbox-close" id="lightbox-close" aria-label="关闭图片预览">&times;</button>
  <img id="lightbox-img" src="" alt="">
  <div class="lightbox-caption" id="lightbox-caption"></div>
</div>

<!-- 原型全屏 -->
<div class="proto-fullscreen-overlay" id="proto-fullscreen" role="dialog" aria-modal="true" aria-label="原型全屏预览">
  <div class="proto-fullscreen-bar">
    <span class="proto-fs-title" id="proto-fs-title"></span>
    <div class="proto-fs-actions">
      <button class="proto-fs-annotations" id="proto-fs-annotations" aria-label="切换标注显示">📍 显示标注</button>
      <button class="proto-fs-close" id="proto-fs-close" aria-label="关闭原型预览">关闭 (Esc)</button>
    </div>
  </div>
  <iframe id="proto-fs-iframe" src="" title="原型预览"></iframe>
</div>

<!-- Annotation Drawer -->
<div class="anno-drawer-backdrop" id="annoDrawerBackdrop"></div>
<div class="anno-drawer" id="annoDrawer">
  <div class="anno-drawer-header">
    <h4 id="annoDrawerTitle">标注点说明</h4>
    <button class="anno-drawer-close" id="annoDrawerClose" aria-label="关闭标注抽屉">&times;</button>
  </div>
  <div class="anno-drawer-body" id="annoDrawerBody"></div>
</div>
```

### H03b：原型 ↔ PRD 通信协议（字段定义，禁止改动）

PRD 与原型 iframe 之间仅允许使用以下两条 postMessage 协议，**字段名必须与原型页面实现严格一致**：

| 方向 | type | 字段 | 含义 |
|------|------|------|------|
| PRD → 原型 | `toggle-annotations` | `on`（boolean） | 显示/隐藏原型内 `.annotation-marker`（原型实现：`document.body.classList.toggle('show-annotations', !!e.data.on)`） |
| 原型 → PRD | `annotation-clicked` | `number`（int） | 用户点击了第 N 个数字标注点 |

父页面接收 `annotation-clicked` 时的**强制处理流程**：

1. 用 `e.source` 在**所有** iframe（内嵌 `.proto-embed iframe` + 全屏 `#proto-fs-iframe`）中匹配消息来源，取其 `src` 文件名
2. 按 `data-num` + `data-page`（文件名）**双条件**匹配标注项——编号在各章节间重复，仅按编号匹配必然跨章节错配
3. 打开右侧标注抽屉，高亮并滚动到该标注项
4. 标注抽屉 z-index 必须高于全屏弹窗（10000），保证全屏时抽屉浮于其上可用

> ⚠️ 历史事故：协议字段曾写成 `show`，与原型实际监听的 `on` 不一致，导致弹窗内标注切换失效；标注项仅按 `data-num` 匹配导致跨章节错配。修改协议字段前必须同步修改全部 `proto-*.html` 的监听实现。

**CSS**：

```css
/* ========== Lightbox Modal ========== */
.lightbox-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.85);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.25s ease, visibility 0.25s ease;
}
.lightbox-overlay.active {
  opacity: 1;
  visibility: visible;
}
.lightbox-overlay img {
  max-width: 92vw;
  max-height: 90vh;
  border-radius: 4px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.4);
  object-fit: contain;
}
.lightbox-close {
  position: absolute;
  top: 16px; right: 20px;
  background: rgba(255,255,255,0.15);
  border: none;
  color: #fff;
  font-size: 28px;
  width: 44px; height: 44px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  line-height: 1;
}
.lightbox-close:hover {
  background: rgba(255,255,255,0.3);
}
.lightbox-caption {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255,255,255,0.7);
  font-size: 13px;
  background: rgba(0,0,0,0.4);
  padding: 4px 16px;
  border-radius: 20px;
}

/* ========== Prototype Fullscreen Modal ========== */
.proto-fullscreen-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: #fff;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s ease, visibility 0.2s ease;
}
.proto-fullscreen-overlay.active {
  opacity: 1;
  visibility: visible;
}
.proto-fullscreen-bar {
  height: 48px;
  background: #f8f9fa;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  flex-shrink: 0;
}
.proto-fullscreen-bar .proto-fs-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}
.proto-fullscreen-bar .proto-fs-close {
  background: #fff;
  border: 1px solid #d0d0d0;
  padding: 6px 16px;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  color: #333;
  transition: background 0.2s;
}
.proto-fullscreen-bar .proto-fs-close:hover {
  background: #f5f5f5;
}
.proto-fullscreen-bar .proto-fs-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.proto-fullscreen-bar .proto-fs-annotations {
  background: #fff;
  border: 1px solid #d0d0d0;
  padding: 6px 16px;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  color: #333;
  transition: all 0.2s;
}
.proto-fullscreen-bar .proto-fs-annotations:hover {
  border-color: #f56c6c; color: #f56c6c;
}
.proto-fullscreen-bar .proto-fs-annotations.active {
  background: #f56c6c; color: #fff; border-color: #f56c6c;
}
.proto-fullscreen-overlay iframe {
  flex: 1;
  width: 100%;
  border: none;
}

/* ========== Modal body lock（替代 JS 中的 body.style.overflow） ========== */
body.modal-open { overflow: hidden; }
```

**JavaScript** — 完整脚本（scroll spy + 灯箱 + 原型全屏 + 可访问性）：

```javascript
// ===== Scroll Spy（requestAnimationFrame 节流） =====
const sections = document.querySelectorAll('section[id]');
const navItems = document.querySelectorAll('.nav-item');
const TRANSITION_MS = 260; // 与 CSS transition 保持一致

let scrollTicking = false;
function onScroll() {
  let current = '';
  sections.forEach(sec => {
    if (window.scrollY >= sec.offsetTop - 100) current = sec.id;
  });
  navItems.forEach(item => {
    item.classList.toggle('active', item.getAttribute('href') === '#' + current);
  });
}
window.addEventListener('scroll', () => {
  if (!scrollTicking) {
    requestAnimationFrame(() => { onScroll(); scrollTicking = false; });
    scrollTicking = true;
  }
});
onScroll();

// ===== Modal 工具函数 =====
let lastFocusedEl = null;

function openModal(modalEl) {
  lastFocusedEl = document.activeElement;
  modalEl.classList.add('active');
  document.body.classList.add('modal-open');
  const closeBtn = modalEl.querySelector('button');
  if (closeBtn) closeBtn.focus();
}

function closeModal(modalEl, cleanup) {
  modalEl.classList.remove('active');
  document.body.classList.remove('modal-open');
  if (cleanup) setTimeout(cleanup, TRANSITION_MS);
  if (lastFocusedEl) lastFocusedEl.focus();
}

function trapFocus(modalEl) {
  const focusable = modalEl.querySelectorAll('button, [tabindex]:not([tabindex="-1"])');
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  modalEl.addEventListener('keydown', (e) => {
    if (e.key !== 'Tab') return;
    if (e.shiftKey) {
      if (document.activeElement === first) { e.preventDefault(); last.focus(); }
    } else {
      if (document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
}

// ===== Image Lightbox =====
const lightbox = document.getElementById('lightbox');
const lightboxImg = document.getElementById('lightbox-img');
const lightboxCaption = document.getElementById('lightbox-caption');

document.querySelectorAll('.img-wrapper').forEach(wrapper => {
  const handler = () => {
    const img = wrapper.querySelector('img');
    if (!img) return;
    lightboxImg.src = img.src;
    lightboxImg.alt = img.alt;
    lightboxCaption.textContent = wrapper.dataset.title || img.alt;
    openModal(lightbox);
  };
  wrapper.addEventListener('click', handler);
  wrapper.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handler(); }
  });
});
trapFocus(lightbox);

function closeLightbox() {
  closeModal(lightbox, () => { lightboxImg.src = ''; });
}
document.getElementById('lightbox-close').addEventListener('click', closeLightbox);
lightbox.addEventListener('click', (e) => { if (e.target === lightbox) closeLightbox(); });

// ===== Prototype Fullscreen =====
const protoOverlay = document.getElementById('proto-fullscreen');
const protoIframe = document.getElementById('proto-fs-iframe');
const protoFsTitle = document.getElementById('proto-fs-title');

document.querySelectorAll('.proto-open-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const embed = btn.closest('.proto-embed');
    if (!embed) return;
    protoIframe.src = embed.dataset.protoSrc;
    protoFsTitle.textContent = embed.dataset.protoTitle || '原型预览';
    openModal(protoOverlay);
  });
});
trapFocus(protoOverlay);

function closeProtoFullscreen() {
  const annoBtn = document.getElementById('proto-fs-annotations');
  annoBtn.classList.remove('active');
  annoBtn.textContent = '📍 显示标注';
  closeModal(protoOverlay, () => { protoIframe.src = ''; });
}
document.getElementById('proto-fs-close').addEventListener('click', closeProtoFullscreen);

// ===== Fullscreen Annotation Toggle =====
const fsAnnoBtn = document.getElementById('proto-fs-annotations');
fsAnnoBtn.addEventListener('click', () => {
  const isActive = fsAnnoBtn.classList.toggle('active');
  fsAnnoBtn.textContent = isActive ? '📍 隐藏标注' : '📍 显示标注';
  try {
    protoIframe.contentWindow.postMessage({ type: 'toggle-annotations', on: isActive }, '*');
  } catch(e) {}
});

// ===== Inline Annotation Toggle =====
document.querySelectorAll('.proto-anno-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const embed = btn.closest('.proto-embed');
    if (!embed) return;
    const iframe = embed.querySelector('iframe');
    if (!iframe) return;
    const isActive = btn.classList.toggle('active');
    btn.textContent = isActive ? '📍 隐藏标注' : '📍 显示标注';
    try {
      iframe.contentWindow.postMessage({ type: 'toggle-annotations', on: isActive }, '*');
    } catch(e) {}
  });
});

// ===== Annotation Drawer =====
const annoDrawer = document.getElementById('annoDrawer');
const annoBackdrop = document.getElementById('annoDrawerBackdrop');
const annoDrawerTitle = document.getElementById('annoDrawerTitle');
const annoDrawerBody = document.getElementById('annoDrawerBody');

// HTML escape utility
function escHtml(str) {
  var d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

// Find detail JSON for a section
function findDetailData(sectionName) {
  var scripts = document.querySelectorAll('script.anno-detail-data');
  for (var i = 0; i < scripts.length; i++) {
    if (scripts[i].dataset.section === sectionName) {
      try { return JSON.parse(scripts[i].textContent); } catch(e) { return null; }
    }
  }
  return null;
}

function openAnnoDrawer(sectionName, items, highlightNum, detailData) {
  annoDrawerTitle.textContent = sectionName + ' — 标注点说明';

  if (detailData && detailData.items && detailData.items.length) {
    // ── Detail mode: render cards ──
    let html = '';
    detailData.items.forEach(function(item) {
      const isOpen = item.num == highlightNum;
      const hl = isOpen ? ' highlight open' : '';
      html += '<div class="anno-card' + hl + '" data-num="' + item.num + '">';
      // Header
      html += '<div class="anno-card__header">' +
        '<span class="anno-card__num">' + item.num + '</span>' +
        '<span class="anno-card__title">' + escHtml(item.title) + '</span>' +
        '<span class="anno-card__toggle">▸</span></div>';
      // Body
      html += '<div class="anno-card__body">';
      // Summary
      if (item.summary) {
        html += '<div class="anno-card__section"><div class="anno-card__label">概述</div>' +
          '<div class="anno-card__text">' + escHtml(item.summary) + '</div></div>';
      }
      // Fields table
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
      // Interactions
      if (item.interactions && item.interactions.length) {
        html += '<div class="anno-card__section"><div class="anno-card__label">交互规则</div><ul class="anno-card__list">';
        item.interactions.forEach(function(r) { html += '<li>' + escHtml(r) + '</li>'; });
        html += '</ul></div>';
      }
      // Validations
      if (item.validations && item.validations.length) {
        html += '<div class="anno-card__section"><div class="anno-card__label">校验规则</div><ul class="anno-card__list">';
        item.validations.forEach(function(v) { html += '<li>' + escHtml(v) + '</li>'; });
        html += '</ul></div>';
      }
      // States
      if (item.states && item.states.length) {
        html += '<div class="anno-card__section"><div class="anno-card__label">状态说明</div><div class="anno-card__states">';
        item.states.forEach(function(s) { html += '<span class="state-badge">' + escHtml(s) + '</span>'; });
        html += '</div></div>';
      }
      html += '</div></div>'; // body / card
    });
    annoDrawerBody.innerHTML = html;
    // Toggle card expand/collapse
    annoDrawerBody.querySelectorAll('.anno-card__header').forEach(function(header) {
      header.addEventListener('click', function() { this.parentElement.classList.toggle('open'); });
    });
    // Scroll to highlighted card
    var hlCard = annoDrawerBody.querySelector('.anno-card.highlight');
    if (hlCard) setTimeout(function() { hlCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }, 50);
  } else {
    // ── Fallback mode: simple items ──
    let html = '';
    items.forEach(function(item) {
      const hl = item.num == highlightNum ? ' highlight' : '';
      html += '<div class="anno-drawer-item' + hl + '">' +
        '<span class="anno-num">' + item.num + '</span>' +
        '<span class="anno-content">' + escHtml(item.content) + '</span>' +
        '<div class="anno-desc">' + escHtml(item.desc) + '</div></div>';
    });
    annoDrawerBody.innerHTML = html;
  }

  annoDrawer.classList.add('open');
  annoBackdrop.classList.add('open');
}
function closeAnnoDrawer() {
  annoDrawer.classList.remove('open');
  annoBackdrop.classList.remove('open');
}
document.getElementById('annoDrawerClose').addEventListener('click', closeAnnoDrawer);
annoBackdrop.addEventListener('click', closeAnnoDrawer);

// Map proto file → section prefix for fullscreen matching
const protoSectionMap = {
  'proto-strategy-list': '3.1', 'proto-seller-offer-form': '3.2',
  'proto-offer-queue': '3.3', 'proto-strategy-log': '3.4'
};

function findAnnoTableBySrc(src) {
  const fileName = src.split('/').pop().replace('.html', '');
  const prefix = protoSectionMap[fileName];
  if (!prefix) return null;
  for (const table of document.querySelectorAll('.anno-table')) {
    if (table.dataset.section?.startsWith(prefix)) return table;
  }
  return null;
}

// Listen for annotation-clicked from prototype iframes
window.addEventListener('message', function(e) {
  if (e.data?.type === 'annotation-clicked') {
    let annoTable = null;
    for (const embed of document.querySelectorAll('.proto-embed')) {
      const iframe = embed.querySelector('iframe');
      if (iframe?.contentWindow === e.source) {
        annoTable = embed.closest('section')?.querySelector('.anno-table');
        break;
      }
    }
    if (!annoTable && protoIframe.contentWindow === e.source) {
      annoTable = findAnnoTableBySrc(protoIframe.src);
    }
    if (!annoTable) return;
    const rows = annoTable.querySelectorAll('tr[data-anno]');
    const items = [...rows].map(r => {
      const cells = r.querySelectorAll('td');
      return { num: r.dataset.anno, content: cells[1]?.textContent || '', desc: cells[2]?.textContent || '' };
    });
    const sectionName = annoTable.dataset.section || '';
    const detailData = findDetailData(sectionName);
    openAnnoDrawer(sectionName, items, e.data.number, detailData);
  }
});

// Also allow clicking # column in anno-table
document.querySelectorAll('.anno-table').forEach(table => {
  table.addEventListener('click', e => {
    const td = e.target.closest('td');
    if (!td) return;
    const row = td.parentElement;
    if (!row.dataset.anno || td !== row.firstElementChild) return;
    const rows = table.querySelectorAll('tr[data-anno]');
    const items = [...rows].map(r => {
      const cells = r.querySelectorAll('td');
      return { num: r.dataset.anno, content: cells[1]?.textContent || '', desc: cells[2]?.textContent || '' };
    });
    const sectionName = table.dataset.section || '';
    const detailData = findDetailData(sectionName);
    openAnnoDrawer(sectionName, items, row.dataset.anno, detailData);
  });
});

// ===== Global: Escape closes modals =====
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if (lightbox.classList.contains('active')) closeLightbox();
    if (protoOverlay.classList.contains('active')) closeProtoFullscreen();
    if (annoDrawer.classList.contains('open')) closeAnnoDrawer();
  }
});
```

### 技术约束

- 纯 CSS + vanilla JS，**禁止引入外部库或 CDN**
- 使用 `<iframe>` 嵌入原型，避免原型文件与 PRD 的 CSS 冲突
- `iframe loading="lazy"` 实现懒加载，减少首屏负担
- z-index: 10000 确保遮罩层在 header(100) 和 sidebar(90) 之上

### 布局参数

- `.main-content` 的 `max-width: 1200px`（内容区统一栏宽，散文与表格同宽；阅读体验由 H07-B 模式层承担，不通过宽度控制实现）
- `.sidebar` 宽度 280px，`.top-header` 高度 56px
- 原型 iframe 预览高度 `420px`，全屏模式占满视口

### H04：CSS 基础规范（变量化 + 兼容性）

所有 PRD HTML 的 `<style>` 开头**必须**包含 `:root` CSS 变量定义，后续所有颜色、尺寸引用变量而非硬编码值：

```css
:root {
  --color-primary: #6c63ff;
  --color-primary-dark: #5a52e0;
  --color-heading: #1a1a2e;
  --color-body: #2c3e50;
  --color-bg: #ffffff;
  --color-sidebar-bg: #f8f9fc;
  --color-border: #e4e7ed;
  --font-size-base: 15px;
  --sidebar-width: 280px;
  --header-height: 56px;
  --transition-speed: 0.2s;
}
```

> ⚠️ 所有原本硬编码 `#6c63ff`、`#5a52e0`、`280px`、`56px` 的地方**必须**改为 `var(--color-primary)` 等变量引用。修改变量值即可全局切换主题。

**侧边栏滚动条 Firefox 兼容**：

```css
.sidebar {
  /* 保留现有 -webkit-scrollbar 系列样式 */
  scrollbar-width: thin;           /* 标准 Firefox 属性 */
  scrollbar-color: #ccc #f5f5f5;   /* 标准 Firefox 属性 */
}
```

**移动端响应式改进**（替代 `display: none` 方案）：

```css
/* 移动端菜单按钮（默认隐藏） */
.mobile-menu-btn {
  display: none;
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #1a1a2e;
  padding: 4px 8px;
}

@media (max-width: 768px) {
  .mobile-menu-btn { display: block; }
  .sidebar {
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    z-index: 200;
  }
  .sidebar.open { transform: translateX(0); }
  .sidebar-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.4);
    z-index: 199;
  }
  .sidebar-overlay.active { display: block; }
  .main-content { margin-left: 0; padding: 20px; }
}
```

**top-header 中添加移动端菜单按钮**：

```html
<header class="top-header">
  <button class="mobile-menu-btn" id="mobile-menu-btn" aria-label="打开导航菜单">☰</button>
  <div class="logo">PRD <span>{标题}</span></div>
  <div class="meta">...</div>
</header>

<!-- sidebar-overlay 在 sidebar 之后 -->
<div class="sidebar-overlay" id="sidebar-overlay"></div>
```

**JS 中添加移动端菜单逻辑**（追加到 `<script>` 末尾）：

```javascript
// ===== Mobile Menu =====
const mobileBtn = document.getElementById('mobile-menu-btn');
const sidebarEl = document.querySelector('.sidebar');
const sidebarOverlay = document.getElementById('sidebar-overlay');
if (mobileBtn && sidebarEl && sidebarOverlay) {
  mobileBtn.addEventListener('click', () => {
    sidebarEl.classList.toggle('open');
    sidebarOverlay.classList.toggle('active');
  });
  sidebarOverlay.addEventListener('click', () => {
    sidebarEl.classList.remove('open');
    sidebarOverlay.classList.remove('active');
  });
}
```

**桌面端侧栏收起/展开**（与移动端共用 ☰ 按钮，必须实现）：

桌面端点击 top-header 的 ☰ 按钮可收起左侧栏，主内容区自动占满全宽；再次点击展开。收起状态通过 `localStorage` 持久化，刷新后保持。

CSS（追加到 `<style>`）：

```css
/* 侧栏收起/展开：桌面端 ☰ 按钮始终可见 */
.mobile-menu-btn { display: block; }
.sidebar { transition: transform 0.3s ease; }
.main-content {
  min-width: 0; /* flex 子元素默认 min-width:auto，会被宽表格等内容撑出横向滚动条，必须归零 */
  transition: margin-left 0.3s ease;
}

@media (min-width: 769px) {
  body.sidebar-collapsed .sidebar { transform: translateX(-100%); }
  body.sidebar-collapsed .main-content {
    margin-left: 0;
    max-width: none; /* 收起后解除限宽，随浏览器实际宽度自适应 */
  }
}

@media (max-width: 768px) {
  /* 移动端仍使用 .open 抽屉模式，不受影响 */
}
```

JS（追加到 `<script>` 末尾，与移动端菜单逻辑共存）：

```javascript
// ===== Sidebar Collapse (desktop) =====
(function () {
  const btn = document.getElementById('mobile-menu-btn');
  if (!btn) return;
  const mq = window.matchMedia('(max-width: 768px)');
  // 恢复上次的收起状态（仅桌面端生效）
  if (localStorage.getItem('prd-sidebar-collapsed') === '1') {
    document.body.classList.add('sidebar-collapsed');
  }
  btn.addEventListener('click', () => {
    if (mq.matches) return; // 移动端走 .open 抽屉逻辑
    const collapsed = document.body.classList.toggle('sidebar-collapsed');
    localStorage.setItem('prd-sidebar-collapsed', collapsed ? '1' : '0');
  });
})();
```

> ⚠️ 桌面端与移动端的判断以 `matchMedia('(max-width: 768px)')` 为准，与 CSS 断点保持一致；移动端点击 ☰ 仍只切换 `.sidebar.open` + overlay。

### H05：文档结构规范（可访问性 + 语义化）

**跳转链接（Skip Link）** — `<body>` 开头必须包含：

```html
<body>
<a href="#main-content" class="skip-link">跳转到主要内容</a>
```

CSS：
```css
.skip-link {
  position: absolute;
  top: -100px;
  left: 0;
  background: #6c63ff;
  color: #fff;
  padding: 8px 16px;
  z-index: 100000;
  font-size: 14px;
  text-decoration: none;
  border-radius: 0 0 4px 0;
}
.skip-link:focus { top: 0; }
```

> ⚠️ 跳转链接让键盘用户无需 Tab 过整个侧边栏（24+链接）即可直达主内容区。

**main 标签添加 id**：

```html
<main class="main-content" id="main-content">
```

**状态徽章添加图标前缀**（不仅依赖颜色区分，照顾色盲用户）：

```css
.badge-verified::before { content: '✓ '; }
.badge-pending::before { content: '⏳ '; }
```

---

### H06：流程图与状态图渲染（mermaid.js 原生渲染）

**流程图/状态图禁止使用静态 PNG 截图呈现**（引用规则 D06）。HTML 版直接用 mermaid.js CDN 运行时渲染 MD 中的 Mermaid 权威源——MD 与 HTML 同一份图源代码，禁止双份维护。

**渲染范围**（全部走 mermaid.js，无例外）：

- §1.1 业务完整流程图、§2.1 核心业务流程图、§2.2.x 复杂子流程图、§3.x 场景示意图（`flowchart`，UML 活动图语义，引用规则 D03）
- §2.3 状态流转图（`stateDiagram-v2`，UML 状态机语法，引用规则 D04）
- 角色关系图（`flowchart`）

**实施方式**：

1. 在 `<head>` 引入固定版本 mermaid.js CDN 并初始化：

```html
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.3/dist/mermaid.min.js"></script>
<script>
  mermaid.initialize({
    startOnLoad: true,
    flowchart: { htmlLabels: true, nodeSpacing: 30, rankSpacing: 60 },
    themeVariables: { fontSize: '14px' }
  });
</script>
```

2. MD 中每个 ```mermaid 代码块原样转为 `<pre class="mermaid">` 容器，图源代码逐字拷贝，禁止二次改写
3. 图源绘制规则（stadium 起止/判断菱形/单层泳道/守卫条件等）见 `docs/rules/prd-diagram-standard.md` D03/D04（渲染前必读）
4. 图外包裹 `.diagram-card` 容器（复用既有卡片样式），图注按 D07 保留

**禁令**：

- ⛔ 禁止把图转成静态 PNG/JPG 截图嵌入
- ⛔ PRD 语境禁止使用 flowdia 组件（flowdia 仅供 proto/diagram 存量 HTML 维护，适用范围见 `docs/rules/flow-diagram-standard.md` v1.4）
- ⛔ 禁止改动 MD 权威源的图源代码（含节点文案、分支标签、classDef 配色）

---

### H07：文字排版规范（通篇强制）

> 本节为**通篇排版模式库**：A 基础层对全文统一生效；B 模式层按内容特征匹配，**不限章节**——任何位置出现同类内容必须套用对应模式。
> **红线**：存量 HTML 套用本节时仅改结构与样式，业务文字一字不改；MD 保持权威源，writer 生成 HTML 时按本节模式产出。

#### A. 基础层（全文强制）

**A1 排版变量** — 追加进 H04 的 `:root`：

```css
:root {
  --font-size-base: 16px;            /* 正文基准字号，中文长文阅读舒适区 */
  --line-height-body: 1.75;
  --color-text-secondary: #6b7280;   /* 次要文字对比度 ≥ 4.5:1（WCAG AA） */
}
```

**A2 标题层级（1.25 模数比例）** — 禁止 h4 与正文同号仅靠粗体区分：

| 层级 | 规格 | 间距（上宽下窄） |
|------|------|------------------|
| h1 | 30px / 700 | margin 0 0 12px |
| h2 | 24px / 600 + border-bottom | margin 48px 0 16px，padding-bottom 10px |
| h3 | 19px / 600 | margin 32px 0 12px |
| h4 | 16px / 700 + `var(--color-heading)` | margin 24px 0 8px |

```css
.main h1, .main h2, .main h3, .main h4 { text-wrap: balance; }
```

**A3 统一栏宽** — 散文与表格/图卡/流程图同栏宽，**禁止用限宽手段解决可读性**；长文可读性由 B 层模式承担（P1 定义列表拆解条目、P2 编号规则块拆解步骤、P3 表格化呈现结构化信息、P4 标题层级）。MD 源头段落长度已由 F11 约束（单段 ≤3 行），本节 B 层模式只负责结构呈现，不改变文字。

```css
/* 无单独散文限宽规则；正文与数据元素共用 .main 容器宽度 */
```

**A4 锚点跳转修正**（固定头遮挡修复，必须）：

```css
section[id], h2[id], h3[id], h4[id] {
  scroll-margin-top: calc(var(--header-height) + 16px);
}
```

**A5 正文细节**：

```css
.main p { margin-bottom: 14px; text-align: justify; text-justify: inter-ideograph; }
.main li { margin-bottom: 8px; }
.main strong { font-weight: 600; color: var(--color-heading); }
```

#### B. 模式层（按内容特征匹配）

**P1 定义列表（glossary）** — 触发条件：一段话里串联 ≥3 个「名称 + 标识 + 定义」的条目（术语、枚举、字段口径、状态说明等）。

```html
<dl class="glossary">
  <div class="glossary-item">
    <dt>术语名 <code>identifier</code></dt>
    <dd>定义文字……</dd>
  </div>
</dl>
```

```css
.glossary { margin: 12px 0 20px; }
.glossary-item { padding: 12px 0; border-bottom: 1px solid var(--color-border-light); }
.glossary-item:last-child { border-bottom: 0; }
.glossary-item dt { font-weight: 600; color: var(--color-heading); margin-bottom: 4px; }
.glossary-item dt code { margin-left: 8px; }
.glossary-item dd { color: var(--color-text-primary); line-height: 1.75; }
```

**P2 结构化规则块** — 触发条件：长文本（段落**或表格单元格**）中含「加粗引导句 + ①②③/分点」。引导句提升为块内小标题，①②③ 转为编号子列表：

```html
<div class="rule-block">
  <div class="rule-block__lead">加粗引导句</div>
  <ol class="rule-steps">
    <li>第一点……</li>
    <li>第二点……</li>
  </ol>
</div>
```

```css
.rule-block + .rule-block { margin-top: 10px; }
.rule-block__lead { font-weight: 600; color: var(--color-heading); margin-bottom: 4px; }
.rule-steps { margin: 4px 0 4px 20px; }
.rule-steps li { margin-bottom: 6px; line-height: 1.75; }
```

**P3 舒适表格** — 触发条件：全文所有 `<table>`（含附录表格）。

```css
table { font-size: 14px; line-height: 1.7; }
table th { font-weight: 600; padding: 12px 16px; }
table td { padding: 12px 16px; vertical-align: top; }
tbody tr:nth-child(even) { background: var(--color-bg-hover); }  /* 斑马纹 */
tbody tr:hover { background: rgba(64,158,255,0.06); }           /* 行 hover */
/* 长表 sticky 表头（吸附在固定头下方） */
thead th { position: sticky; top: var(--header-height); z-index: 5; }
/* 长文本描述列 */
table td.desc, table td:last-child:not(:first-child) { line-height: 1.8; }
/* 首列 ID 胶囊化 */
table td.id-badge { white-space: nowrap; }
.id-badge {
  display: inline-block; padding: 2px 10px; border-radius: 10px;
  background: rgba(64,158,255,0.10); color: var(--color-primary);
  font-size: 12px; font-weight: 700;
}
```

> ⚠️ 列宽规则：ID/编号/引用章节等短列固定窄宽（72–130px），描述列自适应；禁止四列均分。
> ⚠️ sticky 表头仅对 ≥8 行的长表启用，短表（如示例对照表）不必 sticky。

**P4 伪标题清理** — 触发条件：用 `<p><strong>x.x.x 标题</strong></p>` 冒充章节标题的。一律改为真实 h4/h5（含 `id`），纳入标题层级与导航体系。

#### C. 存量适用说明

- 存量 HTML 刷新时**逐节过一遍全文**，产出改造清单随 commit 记录
- 模式套用只改 HTML 标签与 CSS，业务文字零改动；diff 验证文字一致性
- writer 重新生成 HTML 时，MD → HTML 的映射按本节模式产出，不再自由发挥

---

### H08：流程图规则ID tooltip（鼠标悬停显示规则描述）

**规则**：mermaid 渲染完成后，JS 后处理 SVG，把含 `R0x` 模式（`R01`/`R02`/...）的 `<text>` 节点绑定 tooltip，悬停时显示该规则的描述文字。规则描述从 MD 的 §2.4 业务规则索引表抽取。tooltip 文案格式固定为「【R0x】规则名称：规则描述」（含规则 ID 前缀，例如「【R05】触发事件规则：6 类入池；空态提示…」）。

**触发条件**：节点文案引用规则ID（writer.md §2.1/§2.2.x/§2.3 流程图节点已普遍埋点 R0x）。

**CSS**：

```css
/* ========== 规则 ID tooltip ========== */
.mermaid svg text[data-rule-tip] {
  cursor: help;
  text-decoration: underline dotted rgba(108, 99, 255, 0.6);
  text-underline-offset: 3px;
}
.rule-tip-pop {
  position: fixed;
  z-index: 10004;
  max-width: 380px;
  background: #1a1a2e;
  color: #fff;
  font-size: 13px;
  line-height: 1.6;
  padding: 8px 12px;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.12s ease;
  transform: translate(-50%, -100%);
}
.rule-tip-pop.show { opacity: 1; }
```

**HTML**：在 `</body>` 前追加一个全局 tooltip 容器：

```html
<div class="rule-tip-pop" id="ruleTipPop" role="tooltip"></div>
```

**JavaScript**（追加在 `<script>` 末尾，mermaid 渲染回调中执行）：

```javascript
// ===== H08：规则ID tooltip =====
// 规则描述字典：从当前页面的 §2.4 规则表自动抽取，规则ID -> 描述
function extractRuleTips() {
  const map = {};
  // 优先匹配 §2.4「业务规则索引」表
  document.querySelectorAll('main table').forEach(tbl => {
    const rows = tbl.querySelectorAll('tbody tr');
    rows.forEach(tr => {
      const cells = tr.querySelectorAll('td');
      const m = (cells[0]?.textContent || '').match(/R\d{2}/);
      if (m && cells[1]) {
        // 文案格式：【R05】规则名称：规则描述
        map[m[0]] = '【' + m[0] + '】' + cells[1].textContent.trim() + '：' + (cells[2]?.textContent.trim() || '');
      }
    });
  });
  return map;
}

function bindRuleTips() {
  const tipMap = extractRuleTips();
  const pop = document.getElementById('ruleTipPop');
  if (!pop) return;
  const re = /\bR\d{2}\b/g;
  document.querySelectorAll('.mermaid svg text').forEach(text => {
    const raw = text.textContent || '';
    if (!re.test(raw)) return;
    re.lastIndex = 0;
    const ids = raw.match(re) || [];
    const desc = ids.map(id => tipMap[id]).filter(Boolean).join('\n\n');
    if (!desc) return;
    text.setAttribute('data-rule-tip', desc.replace(/\n/g, ' '));
    text.addEventListener('mouseenter', e => {
      pop.textContent = desc;
      pop.classList.add('show');
      const r = text.getBoundingClientRect();
      pop.style.left = (r.left + r.width / 2) + 'px';
      pop.style.top = (r.top - 6) + 'px';
    });
    text.addEventListener('mouseleave', () => pop.classList.remove('show'));
  });
}

// 在 mermaid 完成渲染后执行（mermaid.run() 返回的 then）
if (typeof mermaid !== 'undefined' && mermaid.run) {
  mermaid.run().then(bindRuleTips);
} else {
  // 兼容旧版 startOnLoad
  document.addEventListener('DOMContentLoaded', () => setTimeout(bindRuleTips, 500));
}
```

> ⚠️ 规则描述来自 MD 的 §2.4 表格，HTML 渲染时由 JS 自动抽取。MD 源不需要修改（图节点文案保持纯文本 `R01` 即可），实现完全在 HTML 后处理层。
> ⚠️ 历史 flowdia `.chip` 渲染的存量 PRD HTML 不适用本规则（H08 仅对 mermaid 流程图生效）；flowdia 维护规则见 `docs/rules/flow-diagram-standard.md`。

### H09：变更记录渐进展开（折叠 + 查看更多）

**规则**：附录「变更记录」表格默认显示最新 3 条，其余隐藏；底部「查看更多」按钮每次点击展开 10 条。MD 源表格保持完整，HTML 层通过 JS 折叠。变更记录表格行按日期时间降序排列（最新在最上），默认显示的前 3 行即最新 3 条。

**触发条件**：`<table>` 在附录「变更记录」章节（章节标题含「变更记录」）且行数 > 3。

**CSS**：

```css
/* ========== H09 变更记录渐进展开 ========== */
.change-log-btn {
  display: inline-block;
  margin: 12px 0 0;
  padding: 6px 16px;
  background: #fff;
  border: 1px solid var(--color-primary);
  color: var(--color-primary);
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.change-log-btn:hover { background: var(--color-primary); color: #fff; }
.change-log-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.change-log-info { margin-left: 8px; color: #909399; font-size: 12px; }
.change-log-btn.hidden,
.change-log-row.hidden { display: none; }
```

**JavaScript**（追加在 `<script>` 末尾）：

```javascript
// ===== H09：变更记录渐进展开 =====
(function initChangeLog() {
  // 定位附录「变更记录」表格（首个变更记录章节）
  const heads = [...document.querySelectorAll('main h3, main h4')];
  const target = heads.find(h => /变更记录/.test(h.textContent));
  if (!target) return;
  const tbl = target.nextElementSibling;
  if (!tbl || tbl.tagName !== 'TABLE') return;
  const rows = [...tbl.querySelectorAll('tbody tr')];
  const KEEP = 3, STEP = 10;
  if (rows.length <= KEEP) return;
  rows.slice(KEEP).forEach(r => r.classList.add('change-log-row', 'hidden'));
  const btn = document.createElement('button');
  btn.className = 'change-log-btn';
  btn.type = 'button';
  btn.textContent = '查看更多';
  const info = document.createElement('span');
  info.className = 'change-log-info';
  function updateInfo() {
    const hidden = rows.filter(r => r.classList.contains('hidden')).length;
    btn.disabled = hidden === 0;
    btn.textContent = hidden === 0 ? '已全部展开' : `查看更多（剩余 ${hidden} 条）`;
  }
  btn.addEventListener('click', () => {
    const toShow = rows.filter(r => r.classList.contains('hidden')).slice(0, STEP);
    toShow.forEach(r => r.classList.remove('hidden'));
    updateInfo();
  });
  tbl.insertAdjacentElement('afterend', btn);
  tbl.insertAdjacentElement('afterend', info);
  updateInfo();
})();
```

> ⚠️ 「最新 3 条」指表格中靠前的行（变更记录按日期时间降序排列，最新在第一行）。按钮文案随剩余数动态更新；展开完显示「已全部展开」并禁用。

---

### H10：流程图「复制为图片」按钮

**规则**：所有 mermaid 渲染图（`.diagram-card` 容器）右上角显示「复制为图片」小按钮，点击将图复制为 PNG 到剪贴板。按钮由 JS 在 mermaid 渲染完成后动态注入，不改图容器结构。

**降级链**（必须按序实现）：① `navigator.clipboard.write(ClipboardItem PNG)` → ②剪贴板不可用（file:// 非安全上下文等）→ 自动下载 PNG 文件 → ③canvas 转换失败（htmlLabels 的 foreignObject 可能触发 tainted）→ 复制图源码（SVG XML）兜底。每步结果用 toast 明示用户。

**CSS**：

```css
/* ========== H10：流程图「复制为图片」按钮 ========== */
.diagram-card { position: relative; }
.diagram-copy-btn {
  position: absolute; top: 8px; right: 8px; z-index: 5;
  width: 28px; height: 28px; border-radius: 6px; padding: 0;
  background: rgba(255,255,255,0.92); border: 1px solid var(--color-border);
  color: #666; font-size: 14px; cursor: pointer;
  opacity: 0.55; transition: all 0.15s;
  display: inline-flex; align-items: center; justify-content: center;
}
.diagram-copy-btn:hover {
  opacity: 1; color: var(--color-primary); border-color: var(--color-primary);
  box-shadow: 0 2px 6px rgba(0,0,0,0.12);
}
.diagram-copy-toast {
  position: fixed; top: 70px; left: 50%; transform: translateX(-50%);
  z-index: 10005; background: rgba(0,0,0,0.75); color: #fff;
  padding: 8px 18px; border-radius: 20px; font-size: 13px;
  opacity: 0; transition: opacity 0.2s; pointer-events: none;
}
.diagram-copy-toast.show { opacity: 1; }
```

**JavaScript**（追加在 `<script>` 末尾，挂在 mermaid 渲染回调链上）：

```javascript
// ===== H10：流程图「复制为图片」按钮 =====
function initDiagramCopyButtons() {
  document.querySelectorAll('.diagram-card').forEach(card => {
    if (card.querySelector('.diagram-copy-btn')) return;   // 幂等
    if (!card.querySelector('svg')) return;                // mermaid 未渲染完成不注入
    card.style.position = 'relative';
    const btn = document.createElement('button');
    btn.className = 'diagram-copy-btn';
    btn.type = 'button';
    btn.title = '复制为图片';
    btn.setAttribute('aria-label', '复制为图片');
    btn.textContent = '⧉';
    btn.addEventListener('click', e => { e.stopPropagation(); copyDiagramAsImage(card); });
    card.appendChild(btn);
  });
}

async function copyDiagramAsImage(card) {
  const svgEl = card.querySelector('svg');
  if (!svgEl) return;
  const xml = new XMLSerializer().serializeToString(svgEl);
  try {
    const url = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(xml);
    const img = new Image();
    await new Promise((res, rej) => { img.onload = res; img.onerror = rej; img.src = url; });
    const vb = svgEl.viewBox && svgEl.viewBox.baseVal;
    const w = (vb && vb.width) || svgEl.clientWidth || 800;
    const h = (vb && vb.height) || svgEl.clientHeight || 600;
    const scale = 2;  // 2x 输出保证清晰度
    const canvas = document.createElement('canvas');
    canvas.width = w * scale; canvas.height = h * scale;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, canvas.width, canvas.height);  // 白底防透明
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
    if (!blob) throw new Error('toBlob null');
    if (navigator.clipboard && window.ClipboardItem) {
      try {
        await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
        diagramCopyToast('已复制图片到剪贴板');
        return;
      } catch (e) { /* 剪贴板不可用，降级下载 */ }
    }
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'diagram.png';
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 5000);
    diagramCopyToast('剪贴板不可用，已下载 PNG');
  } catch (err) {
    try { await navigator.clipboard.writeText(xml); diagramCopyToast('图片转换受限，已复制图源码'); }
    catch (e2) { diagramCopyToast('复制失败'); }
  }
}

function diagramCopyToast(msg) {
  const old = document.querySelector('.diagram-copy-toast');
  if (old) old.remove();
  const t = document.createElement('div');
  t.className = 'diagram-copy-toast';
  t.textContent = msg;
  document.body.appendChild(t);
  requestAnimationFrame(() => t.classList.add('show'));
  setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 250); }, 1800);
}
```

**挂接**：在 mermaid 渲染回调链追加（与 H08 同链）：

```javascript
if (typeof mermaid !== 'undefined' && mermaid.run) {
  mermaid.run().then(() => { bindRuleTips(); initDiagramCopyButtons(); });
} else {
  document.addEventListener('DOMContentLoaded', () => setTimeout(() => { bindRuleTips(); initDiagramCopyButtons(); }, 500));
}
```

> ⚠️ `htmlLabels: true` 时 mermaid 用 foreignObject 渲染文本，Chrome 对自包含 data-URI SVG（无外部资源/脚本）允许 canvas 转换；少数环境触发 tainted 时走降级链③复制图源码，用户不丢信息。
> ⚠️ 状态机图（stateDiagram-v2）同为 `.diagram-card` 包裹，自动纳入本规则，无需额外处理。

---

### H11：附录「相关规范」链接新窗口打开

**规则**：附录「相关规范」小节（h3/h4 标题含「相关规范」）内指向 `docs/rules/ui-standard/index.html` 的 `<a>` 链接，由 JS 后处理加 `target="_blank" rel="noopener noreferrer"`，点击在新标签页打开。MD 标准链接语法 `[文字](路径)` 不支持 `target` 属性，须在 HTML 渲染层注入。

**触发条件**：`<main>` 内 h3/h4 标题含「相关规范」的小节下的 `<a>` 且 href 含 `ui-standard/index.html`。

**JavaScript**（追加在 `<script>` 末尾）：

```javascript
// ===== H11：附录「相关规范」链接新窗口打开 =====
(function initAppendixUiLink() {
  const heads = [...document.querySelectorAll('main h3, main h4')];
  const head = heads.find(h => h.textContent.includes('相关规范'));
  if (!head) return;
  let el = head.nextElementSibling;
  while (el && !/^H[1-6]$/.test(el.tagName)) {
    el.querySelectorAll('a').forEach(a => {
      const href = a.getAttribute('href') || '';
      if (href.includes('ui-standard/index.html')) {
        a.setAttribute('target', '_blank');
        a.setAttribute('rel', 'noopener noreferrer');
      }
    });
    el = el.nextElementSibling;
  }
})();
```

> ⚠️ 该规则仅作用于附录「相关规范」小节内的 UI 规范链接，不影响正文其他链接。

---

## 检验清单

> HTML 渲染版生成后、卡点②提交前必须逐项执行。统一命令：`python3 scripts/prd_html_check.py <prd.html>`（脚本同目录须有同名 .md 权威源）。每项标注【机器可验】（引用规则 W21/W27）。任一断言 FAIL 不得 commit。

- [ ] 【机器可验】**标签配对**：`<style>`/`<script>`/`<iframe>` 起止数相等（脚本断言1；防线背景：生成脚本对已含标签的 CSS/JS 片段二次包裹会产生连续重复起始标签，导致 CSS `:root` 变量块被解析器丢弃、布局塌陷）
- [ ] 【机器可验】**CSS 变量完整性**：首个 `<style>` 块内 `:root` 存在，`--sidebar-width`/`--header-height` 非空（脚本断言2；直接抓二次包裹 bug）
- [ ] 【机器可验】**mermaid 图源一致**：HTML 内 `<pre class="mermaid">` 各块 unescape 后与 MD 的 ` ```mermaid ` 块逐字相等（脚本断言3；引用 D06，禁止双份维护）
- [ ] 【机器可验】**原型嵌入完整性**：`class="proto-embed"` 数 = `<iframe src="../prototype/` 数（脚本断言4）
- [ ] 【机器可验】**章节锚点连通**：sidebar `nav-item` 的 href 指向的 id 在 `<main>` 内存在（脚本断言5，含 h2/h3/h4）
- [ ] 【机器可验】**标注点内容一致**：每个 `anno-detail-data` JSON 可解析，items 数 = 同 `data-section` 的 `anno-table tr[data-anno]` 行数，每 item 含 summary/fields/interactions/validations 四核心字段（脚本断言6；对应 writer.md Step3-i）
- [ ] 【机器可验】**标注点注入完整性**：每个 proto-embed 的 iframe 原型文件含 annotation-marker 样式 + toggle-annotations 监听 + annotation-clicked 回传（脚本断言7；防漏写，对应 proto_agent.md 页面级标注点注入规则）
- [ ] 【机器可验】**规则 ID tooltip**：含 `R0x` 的 mermaid SVG `<text>` 节点已绑定 `data-rule-tip`，hover 触发 `#ruleTipPop` 显示规则描述（H08）
- [ ] 【机器可验】**变更记录渐进展开**：附录「变更记录」表格行数 >3 时，仅前 3 行可见，底部「查看更多」按钮存在且初始可点，hidden 行 class 含 `change-log-row hidden`（H09）
- [ ] 【机器可验】**复制为图片按钮**：每个 `.diagram-card` 内含 `.diagram-copy-btn`（mermaid 渲染后由 JS 注入），点击后走「剪贴板 PNG → 下载 PNG → 复制图源码」降级链并有 toast 反馈（H10）
- [ ] 【机器可验】**附录「相关规范」链接**：附录含指向 `ui-standard/index.html` 的 `<a>` 且含 `target="_blank"`（H11；脚本断言9）

---

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-08-11 17:00 | v1.8 | ①新增 H11「附录「相关规范」链接新窗口打开」：JS 后处理给附录「相关规范」小节内指向 ui-standard/index.html 的 `<a>` 加 target="_blank" rel="noopener noreferrer"；②检验清单加 1 项【机器可验】（断言9）；③对齐模板 v4.2 附录新增 A. 相关规范小节 | 本文件 + `templates/prd_template.md` v4.2 + `scripts/prd_html_check.py` 断言9 + `docs/agents/prd_stages/writer.md` v1.7 |
| 2026-08-10 16:00 | v1.7 | ①新增 H10「流程图复制为图片按钮」：所有 .diagram-card 右上角小按钮，点击 SVG→canvas(白底2x)→PNG 复制剪贴板，降级链=下载PNG→复制图源码，toast 反馈；②检验清单加 1 项【机器可验】 | 本文件 + `scripts/prd_html_check.py` 断言8 |
| 2026-08-10 15:30 | v1.6 | ⑤H08 规则描述删「（或附录 A）」兜底（附录 A 随模板 v4.1 移除）；⑥H09 删「附录 A 不应用此规则」注意事项、表述「附录 B」改「附录『变更记录』章节」、补「表格行按日期时间降序，前 3 行即最新 3 条」；⑦检验清单「附录 B」表述同步 | 本文件 + `templates/prd_template.md` v4.1 + `docs/agents/prd_stages/writer.md` v1.6 |
| 2026-08-10 15:10 | v1.5 | H08 tooltip 文案补规则 ID 前缀：「规则名称：描述」→「【R0x】规则名称：描述」（示例「【R05】触发事件规则：6 类入池…」），规则描述行同步补格式说明 | 本文件 |
| 2026-08-10 14:20 | v1.5 | ①新增 H08「流程图规则ID tooltip」：JS 后处理 mermaid SVG，把含 `R0x` 的 `<text>` 节点绑定 hover tooltip，规则描述从 §2.4 表格自动抽取（MD 源不变）；②新增 H09「变更记录渐进展开」：附录 B 默认 3 条 + 查看更多按钮每次 +10；③检验清单新增 2 项【机器可验】；④渲染范围移除架构图（与 PRD 删第5章同步） | 本文件 + `docs/rules/prd-diagram-standard.md` D03（补 H08 引用） |
| 2026-08-10 14:20 | v1.4 | ①新增「检验清单」章节（6 项【机器可验】，统一引用 `scripts/prd_html_check.py`，对应 W27）；防线背景：v1.3 前无任何 HTML 结构校验，生成脚本二次包裹 `<style>`/`<script>` 导致 CSS `:root` 丢失、布局塌陷的事故无法在生成时拦截 | 本文件 + `scripts/prd_html_check.py`（新建）+ `docs/rules/sop-writing-standard.md` W27 + `docs/agents/prd_stages/writer.md` v1.5 |
| 2026-08-04 09:10 | v1.3 | ①H06 整节重写：flowdia 交互组件 → mermaid.js CDN 原生渲染（固定 mermaid@10.9.3 初始化配置、`<pre class="mermaid">` 逐字拷贝 MD 权威源、渲染范围扩至状态图/角色图/架构图、PRD 语境禁用 flowdia）；②H07-A3 补 F11 衔接句（MD 源头段落长度已约束，B 层只负责结构呈现）；③关联文档改指 `docs/rules/prd-diagram-standard.md` | 本文件 + `docs/rules/prd-diagram-standard.md`（新建）+ `docs/rules/flow-diagram-standard.md` v1.4（适用范围收缩） |
| 2026-07-29 | v1.2 | 新增 H07 文字排版规范（通篇）：A 基础层（排版变量 16px/1.75/38em、1.25 模数标题层级、窄正文+宽表格、scroll-margin-top、中文两端对齐、strong 样式）+ B 模式层（P1 定义列表 / P2 结构化规则块 / P3 舒适表格 / P4 伪标题清理）+ C 存量适用红线（文字零改动、MD 权威源） | 本文件 + `versions/eBayPLP广告策略_v0.1.0/prd/eBayPLP广告策略-prd.html`（首个验证样本） |
| 2026-07-28 | v1.1 | ①按 `docs/rules/sop-writing-standard.md` §2.1 补 frontmatter + 属性表 + 头部 blockquote（含「代码级规范，允许超行」例外声明）；②文末补附录变更记录；③H01-H06 编号与全部 CSS/JS 代码一字未改，文件未拆分、结构未变动 | 本文件 |
