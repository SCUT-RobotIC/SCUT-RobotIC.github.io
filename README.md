# RobotIC · 华南理工大学机器人实验室

华南理工大学 RobotIC 机器人实验室的官方网站（机器人实验室介绍 + 招商合作 + 招新）。
纯静态站点，无需构建工具，直接由 GitHub Pages 托管。

- 站点地址：<https://robot-ic.com/>
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
| `models.html` | 三维模型：浏览器里 360° 查看历年机器人（three.js + glTF） |
| `404.html` | 自定义 404 页面 |

## 目录

```
.
├── index.html / lab.html / robots.html / models.html / sponsor.html / join.html / 404.html
├── assets/
│   ├── css/style.css      # 设计系统与全部样式（无框架）
│   ├── js/main.js         # 导航、滚动动效、标签页、灯箱（原生 JS）
│   ├── img/               # 站点使用的图片资源（已压缩）
│   ├── models/            # 三维模型（.glb）与 manifest.json
│   └── vendor/three/      # 本地内置的 three.js（不走 CDN）
├── tools/build_assets.py  # 从原始素材生成 web 图片
├── tools/cad_to_glb.py    # CAD（URDF/STEP/STL/3MF）→ glb
├── tools/serve.py         # 本地预览服务器（修正 .js 的 MIME）
├── sitemap.xml / robots.txt / .nojekyll
```

## 三维模型

`models.html` 用 three.js 在浏览器里渲染 `.glb`，无需安装任何软件。
浏览器读不了 SolidWorks 的 `.sldprt` / `.sldasm`，所以需要先导出一次中性格式：

1. **SolidWorks 里导出**：打开当年总装 → 另存为 `STEP`（保留零件颜色）或 `STL` / `3MF`（更轻，单色）。
   已有 URDF 包（`meshes/*.STL` + `.urdf`）的，直接把整个包目录丢进来也行。
2. **转成 glb**：

   ```powershell
   python tools/cad_to_glb.py "路径/总装.STEP" -o assets/models/r26-r1.glb
   python tools/cad_to_glb.py "路径/R2025.SLDASM" -o assets/models/r25-chassis.glb   # URDF 包目录
   ```

   脚本会自动：Z-up → Y-up、毫米 → 米、水平居中、底部贴地。
3. **挂到清单**：在 `assets/models/manifest.json` 的 `models` 数组里加一项（`name` / `season` / `file` / `triangles` / `size`），页面会自己出现新的模型标签。

转换依赖：`pip install trimesh`（网格）；要读 STEP 再加 `pip install cadquery`；
网格太大时 `pip install fast-simplification` 并在命令里加 `--target-tris 200000`。

单个模型建议控制在 3–8 MB（20–30 万三角面），再大手机加载会卡。

## 本地预览

站点是纯静态的，任选一种方式：

```powershell
# 推荐：带正确 MIME 的本地服务器（Windows 上裸 http.server 会把 .js 当 text/plain，
# 导致浏览器拒绝执行 ES module，三维页面加载不出来）
python tools/serve.py 8000
# 然后访问 http://127.0.0.1:8000

# 或者直接用浏览器打开（三维页面需要 http，file:// 会被 CORS 拦）
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

推送到 `main` 分支后，GitHub Pages 自动发布到 <https://robot-ic.com/>。
仓库内的 `.nojekyll` 会关闭 Jekyll 处理，静态文件按原样发布。

© 华南理工大学 RobotIC 机器人实验室
