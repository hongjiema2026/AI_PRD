# 原型组件系统

基于 Preact + Vite 的轻量原型开发环境。

## 快速开始

```bash
cd templates/prototype
npm install
npm run dev
```

浏览器自动打开 http://localhost:3000

## 构建生产版本

```bash
npm run build
```

输出到 `dist/` 目录，可直接部署或本地打开。

## 项目结构

```
prototype/
├── src/
│   ├── components/     # 可复用组件
│   ├── pages/          # 页面组件
│   ├── styles/         # 样式文件
│   │   ├── variables.css  # 设计变量
│   │   ├── base.css       # 基础样式
│   │   └── components.css # 组件样式
│   ├── App.jsx         # 根组件
│   └── main.jsx        # 入口
├── index.html          # HTML 模板
├── vite.config.js      # Vite 配置
└── package.json
```

## 设计规范

- 使用 CSS 变量统一管理颜色、间距、字体
- 组件使用 BEM 风格命名
- 支持 Ant Design 配色的快速切换