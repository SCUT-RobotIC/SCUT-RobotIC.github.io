# RobotIC · 华南理工大学机器人实验室

华南理工大学 RobotIC 机器人实验室的官方网站（机器人实验室介绍 + 招商合作 + 招新）。
纯静态站点，无需构建工具，直接由 GitHub Pages 托管。

- 站点地址：<https://scut-robotic.github.io/>
- 赛事：ABU ROBOCON 全国大学生机器人大赛
- 实验室成立：2022 年 12 月 · 广州国际校区

## 页面结构

| 文件 | 内容 |
| --- | --- |
| `index.html` | 首页：实验室概览、赛季战绩、机器人、五个方向、合作伙伴、招商联络 |
| `lab.html` | 实验室：简介、四年时间线、组织架构、赛场之外的高光时刻、地址与联系 |
| `robots.html` | 机器人与战绩：机器人谱系、完整战绩、技术栈、图集（灯箱） |
| `sponsor.html` | 招商合作：为什么合作、12 项赞助商权益、支持形式、合作案例、伙伴、联系方式 |
| `join.html` | 加入我们：招新流程、五个组别（标签页）、科普组分级体系、FAQ、报名二维码 |
| `404.html` | 自定义 404 页面 |

## 目录

```
.
├── index.html / lab.html / robots.html / sponsor.html / join.html / 404.html
├── assets/
│   ├── css/style.css      # 设计系统与全部样式（无框架）
│   ├── js/main.js         # 导航、滚动动效、标签页、灯箱（原生 JS）
│   └── img/               # 站点使用的图片资源（已压缩）
├── tools/build_assets.py  # 从原始素材生成 web 图片
├── sitemap.xml / robots.txt / .nojekyll
```

## 本地预览

站点是纯静态的，任选一种方式：

```powershell
# 直接用浏览器打开
start index.html

# 或者起一个本地服务（推荐，路径与线上一致）
python -m http.server 8000
# 然后访问 http://127.0.0.1:8000
```

## 更新图片资源

`assets/img/` 中的图片由 `tools/build_assets.py` 从原始素材（队徽、赛季渲染图、
赞助商 LOGO、二维码）统一生成：裁边、压缩、生成 hero 图与 OG 分享图。

```powershell
python tools/build_assets.py
```

脚本默认从仓库同级的 `RobotIC网站` 素材目录读取源文件，输出到 `assets/img/`。
替换素材后重新运行即可，无需手动改尺寸。

## 设计说明

- 深色主题（`#0b0c0e`）+ RobotIC 红（`#e8261a`）+ 中性灰，呼应队徽与招商手册。
- 字体使用系统字体栈（含苹方 / 微软雅黑），不依赖外部 CDN，国内访问无阻塞。
- 所有交互为原生 JavaScript：移动端导航、滚动进入动画（`prefers-reduced-motion` 下自动关闭）、
  组别标签页、图片灯箱。禁用 JS 时内容依然完整可读。
- 响应式断点：1080 / 860 / 560。

## 内容来源

页面文字依据实验室《招商手册（26 年第 2 版）》与《27 赛季招新宣讲会》整理，
赛事成绩与合作伙伴信息同步自实验室公众号「RobotIC 机器人实验室」公开推文。

## 部署

推送到 `main` 分支后，GitHub Pages 自动发布到 <https://scut-robotic.github.io/>。
仓库内的 `.nojekyll` 会关闭 Jekyll 处理，静态文件按原样发布。

© 华南理工大学 RobotIC 机器人实验室
