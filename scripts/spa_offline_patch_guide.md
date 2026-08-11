# SPA 离线快照 CSS 补丁指南

> 适用于：Vue/React 等 SPA 页面爬取后生成的离线 HTML 快照。
> 核心原则：移除 JS 后，所有 JS 动态管理的样式都需要用纯 CSS 补偿。

---

## 一、爬虫阶段应做的事（自动化，无需人工干预）

### 1.1 移除所有 `<script>` 标签

防止 Vue/React 重新挂载、路由跳转、数据重渲染。

```python
soup = BeautifulSoup(html, 'html.parser')
for tag in soup.find_all('script'):
    tag.decompose()
```

### 1.2 移除 JS 固化的内联高度/overflow

JS 运行时会向 DOM 元素注入 `style="height: 668px"` 等内联样式。这些值是运行时计算的，硬编码后无法自适应屏幕，会导致内容溢出或被裁剪。

**关键**：移除以下元素的内联 `style` 中的 `height`、`overflow` 属性：

| 元素 | 需移除的内联属性 | 原因 |
|------|------------------|------|
| `.vxe-table--body-wrapper` | `height: XXXpx` | 固定值不适配容器，用 calc 替代 |
| `#app-container` | JS 设置的 overflow | 与 scoped CSS 冲突 |
| `.el-table__body-wrapper` | JS 设置的 height | 同上 |

```python
# 移除 vxe-table body-wrapper 的固定高度（JS 注入的内联 style）
for tag in soup.select('.vxe-table--body-wrapper'):
    tag.attrs.pop('style', None)
```

### 1.3 资源本地化检查清单

| 资源类型 | 检查项 | 失败表现 |
|----------|--------|----------|
| `@font-face` url() | 是否有 `/static/`、`//cdn.xxx.com` 等绝对路径 | 字体图标空白（☐ ✕ → □） |
| `@font-face` src | 是否有 base64 data URI（正常的，无需处理） | — |
| `<link href>` | CSS/ICO 是否已下载到本地 | 样式丢失、favicon 缺失 |
| `<img src>` | 图片是否已下载到本地 | 图片裂图 |
| CSS 中的 `url()` | 字体、背景图是否已本地化 | 图标缺失 |

### 1.4 移除 `fixed--hidden` 类

vxe-table 固定列在主表格中标记为 `visibility: hidden`，实际内容在克隆的 fixed wrapper 中。离线快照应直接在主表格中显示所有列。

```python
for tag in soup.select('.fixed--hidden'):
    tag['class'] = [c for c in tag.get('class', []) if c != 'fixed--hidden']
```

---

## 二、自动注入的 CSS 补丁（按需组合）

爬虫脚本在生成最终 HTML 时，应自动在 `<head>` 中注入以下 `<style>` 补丁。

### 2.1 基础补丁（所有 SPA 通用）

```css
/* 防止页面跳转 */
/* 已通过移除 <script> 解决，无需额外 CSS */
```

### 2.2 Vue scoped CSS overflow 冲突

**问题**：Vue scoped CSS 用 `[data-v-xxx]` 属性选择器，优先级很高。多个 scoped 规则可能冲突（如 `.hasTagsView` vs `.notebook`），线上靠 JS 内联 style 解决。

**通用解法**：

```css
#app-container { overflow: hidden !important; }
```

### 2.3 vxe-table 补丁

```css
/* 隐藏固定列克隆 wrapper（内容已在主表格中） */
.vxe-table--fixed-left-wrapper,
.vxe-table--fixed-right-wrapper { display: none !important; }

/* 表头固定（纵向滚动时） */
.vxe-table--main-wrapper .vxe-table--header-wrapper {
  position: sticky !important;
  top: 0 !important;
  z-index: 5 !important;
  background: #fff !important;
}

/* 表体滚动：用 calc 替代 JS 硬编码高度 */
/* 开销 = navbar(40) + search(50) + toolbar(40) + table_header(40) + footer(40) + padding(20) = 230px */
/* 根据实际页面结构调整这个值 */
.vxe-table--main-wrapper .vxe-table--body-wrapper {
  height: calc(100vh - 270px) !important;
  min-height: 200px !important;
  overflow: auto !important;
}

/* 保险：覆盖可能残留的 fixed--hidden */
.fixed--hidden { visibility: visible !important; }
```

### 2.4 横向冻结列（vxe-table）

```css
/* 勾选列 — 左侧冻结 */
th[colid="col_2"], td[colid="col_2"] {
  position: sticky !important;
  left: 0 !important;
  z-index: 3 !important;
  background: #fff !important;
}
.vxe-table--header-wrapper th[colid="col_2"] { z-index: 6 !important; }

/* 操作列 — 右侧冻结（colid 按实际页面调整） */
th[colid="col_N"], td[colid="col_N"] {
  position: sticky !important;
  right: 0 !important;
  z-index: 3 !important;
  background: #fff !important;
}
.vxe-table--header-wrapper th[colid="col_N"] { z-index: 6 !important; }
```

**注意**：`colid` 需要根据实际页面的列定义确定。冻结列的父容器链上不能有 `overflow: hidden`，否则 sticky 被裁剪。

### 2.5 Element UI 分页补丁

```css
.el-pagination {
  display: flex !important;
  align-items: center !important;
  flex-wrap: wrap !important;
  gap: 4px !important;
  padding: 6px 12px !important;
  font-size: 13px !important;
  color: #606266 !important;
}
.el-pagination button,
.el-pagination .el-pager li,
.el-pagination .el-pagination__total,
.el-pagination .el-pagination__jump {
  font-size: 13px !important;
  color: #606266 !important;
  line-height: 28px !important;
  min-width: 30px !important;
  height: 28px !important;
  display: inline-flex !important;
  align-items: center !important;
  border: 1px solid #dcdfe6 !important;
  border-radius: 2px !important;
  background: #fff !important;
  cursor: pointer !important;
  margin: 0 2px !important;
}
.el-pagination .el-pager li.active {
  color: #409eff !important;
  border-color: #409eff !important;
}
```

---

## 三、检验清单

生成 HTML 后，自动验证以下项目：

- [ ] 无 `<script>` 标签
- [ ] 无外部 URL 引用（`//cdn`、`/static/`、`http://`）
- [ ] 无 `fixed--hidden` 类残留
- [ ] body-wrapper 无固定 px 高度（应为 calc 或 auto）
- [ ] 字体文件全部本地化
- [ ] 用浏览器打开验证：表格内容可见、上下滚动正常、左右滚动正常、冻结列生效、分页可见

---

## 四、关键经验教训

| 教训 | 正确做法 |
|------|----------|
| JS 硬编码的高度值（668px）被固化到 HTML | 爬虫阶段移除这些内联 style，用 CSS calc 替代 |
| 逐个修 CSS 导致反复回退（改了 A 坏了 B） | 先分析完整的高度/overflow 链条，一次性设计补丁 |
| `position: sticky` 列不生效 | 检查祖先容器是否有 `overflow: hidden`，有则改为 `visible` 或 `auto` |
| scoped CSS 选择器优先级很高 | 用 `!important` 或匹配 `[data-v-xxx]` 选择器覆盖 |
| 分页/表格反复互斥 | 用 `calc()` 让高度自适应，而非固定值或 flex 链 |
| 字体图标空白 | 爬虫阶段检查所有 `@font-face url()` 和 CSS `url()`，确保本地化 |
