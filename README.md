# 🦙 LaMa Studio

基于 [advimman/lama](https://github.com/advimman/lama)（WACV 2022，Resolution-robust Large Mask Inpainting with Fourier Convolutions）主要功能实现的图像修复 / 物体移除 Web 应用：**涂抹遮罩 → AI 补全**。

- 前端：**Vue 3 + TypeScript + Vite + Element Plus + Pinia + axios**
- 后端：**FastAPI + PyTorch（LaMa 权重）+ OpenCV（兜底引擎）**
- 推理封装：[simple-lama-inpainting](https://github.com/enesmsahin/simple-lama-inpainting)（LaMa TorchScript 权重的第三方 pip 封装）

## 功能

| 功能 | 说明 |
| --- | --- |
| 图片加载 | 点击 / 拖拽上传（png、jpg、webp），或一键载入**官方案例图片**（来自 LaMa 官方 notebook / 作者主页） |
| 遮罩绘制 | 画笔 / 橡皮 / 抓手、笔刷大小、6 种遮罩颜色、遮罩显隐与透明度，遮罩按**原图像素 1:1** 导出 |
| 画布操作 | 滚轮缩放（10%–800%，以光标为锚点）、拖动平移、适应窗口，快捷键 `+ - 0` |
| 辅助绘制 | 网格辅助（`G`）、纵向/横向十字辅助线（`H`）、`Shift` 约束水平/垂直直线 |
| 分步编辑 | 撤销 / 重做按**单笔**步进（`Ctrl+Z` / `Ctrl+Shift+Z`，最多 30 步），清空遮罩彻底清除 |
| AI 修复 | 白色遮罩区域被补全，支持 `auto / lama / opencv` 引擎、`dilate` 遮罩外扩、`refine`、`radius` |
| 结果对比 | 修复完成后**全屏对比视图**，可拖动分割线、一键下载 `inpainted.png`；**返回编辑后再次修复会覆盖原记录**，不会重复新增 |
| 历史记录 | 右侧可滚动列表，单条删除、清空全部，点击任意记录回到对比视图 |
| 引擎兜底 | LaMa 权重 / torch 不可用时自动降级到 OpenCV Telea 算法，界面会明确提示当前引擎 |
| 界面风格 | 星海壁纸背景（`frontend/public/background.jpg`，缓慢漂移动效）+ 深色液态玻璃面板，Element Plus 深色模式 |

## 目录结构

```
lama-studio/
├── frontend/                # Vue 3 + TS 前端
│   └── src/
│       ├── api/client.ts    # axios 封装（/api 代理）
│       ├── components/      # 左侧工具栏、画布、参数面板、历史记录、对比视图
│       ├── stores/editor.ts # Pinia 状态（遮罩、缩放、历史）
│       └── types/
│   └── public/samples/      # 官方案例图片
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # 应用入口、CORS
│   │   ├── config.py        # 环境变量配置
│   │   ├── routers/         # /api/health、/api/inpaint
│   │   └── services/        # image_utils / opencv_service / lama_service / engine
│   ├── tests/               # pytest（不依赖模型权重即可通过）
│   ├── requirements.txt     # 核心依赖
│   ├── requirements-lama.txt# LaMa 推理依赖（torch CPU 版）
│   └── run.ps1              # 一键启动
└── scripts/
    ├── download_model.ps1   # 下载 big-lama.pt 权重
    └── e2e_smoke.py         # 端到端冒烟测试（生成图片+遮罩 → 调 /api/inpaint）
```

## 快速开始

### 1. 后端

```powershell
cd lama-studio/backend

# 创建虚拟环境并安装核心依赖
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 安装 LaMa 推理依赖（CPU 版 torch，约 200MB+）
.\.venv\Scripts\python.exe -m pip install -r requirements-lama.txt --extra-index-url https://download.pytorch.org/whl/cpu

# 下载 LaMa 权重（约 200MB）到 backend/models/big-lama.pt
..\scripts\download_model.ps1

# 启动（自动设置 LAMA_MODEL / TORCH_HOME）
.\run.ps1
```

后端监听 `http://127.0.0.1:8000`，接口文档 `/docs`。

### 2. 前端

```powershell
cd lama-studio/frontend
npm install
npm run dev        # http://localhost:5173 ，/api 已代理到 8000
```

生产构建：`npm run build`（含 `vue-tsc` 类型检查）。

### 3. 验证（可选）

```powershell
# 单元 / 接口测试（不依赖模型权重，强制 opencv 引擎）
cd lama-studio\backend
.\.venv\Scripts\python.exe -m pytest -q

# 端到端冒烟：先启动后端，再另开一个终端
python ..\scripts\e2e_smoke.py --engine auto --out result.png
python ..\scripts\e2e_smoke.py --engine opencv --out result_opencv.png
```

`e2e_smoke.py` 会程序化生成一张带红色方块的图片与对应遮罩，调用 `POST /api/inpaint`，打印实际引擎、服务端耗时与输出尺寸。

### 4. 只想先跑起来（不装 torch / 不下权重）

只装 `requirements.txt` 后启动后端即可：LaMa 不可用时自动降级为 OpenCV 兜底引擎，`GET /api/health` 里的 `engine` 会返回 `opencv`，`fallback_reason` 说明原因。

## 环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `LAMA_MODEL` | `backend/models/big-lama.pt` | 本地 LaMa TorchScript 权重路径（由 `run.ps1` 设置） |
| `LAMA_MODEL_URL` | GitHub release `big-lama.pt` | 未设置 `LAMA_MODEL` 时的下载地址 |
| `LAMA_DEVICE` | `auto` | `auto` / `cpu` / `cuda` |
| `LAMA_ENGINE` | `auto` | 后端默认引擎：`auto` / `lama` / `opencv` |
| `TORCH_HOME` | `backend/.cache/torch` | torch hub 缓存目录（由 `run.ps1` 设置） |
| `MAX_UPLOAD_MB` | `25` | 上传大小上限 |
| `MAX_SIDE` | `4096` | 图片最长边上限 |
| `PORT` | `8000` | 后端端口 |

## API

### `GET /api/health`

```json
{
  "status": "ok",
  "version": "0.1.0",
  "engine": "lama",
  "model": "big-lama",
  "device": "cpu",
  "model_ready": true,
  "torch_available": true,
  "fallback_reason": null
}
```

### `POST /api/inpaint`

`multipart/form-data`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `image` | file | 原图（png / jpg / webp，≤ 25MB，最长边 ≤ 4096） |
| `mask` | file | PNG 遮罩，与图片解码后同尺寸，**白色 = 要修复的区域** |
| `options` | string(JSON) | `{"engine":"auto\|lama\|opencv","refine":false,"radius":3,"dilate":2}` |

`dilate` 为遮罩向外扩张的像素数（0–10，默认 2）：手绘遮罩通常紧贴物体边缘，先外扩几像素再修复可以消除残留的边缘轮廓，是缩小与官方效果差距最直接的手段。

成功返回 `image/png` 二进制，响应头带 `X-Inpaint-Engine`（实际使用的引擎）与 `X-Inpaint-Ms`（耗时毫秒）。失败返回 `{"detail": "..."}`（400 / 413 / 422 / 503）。

## 工作原理

1. 前端在**离屏 canvas**（尺寸 = 原图像素尺寸）上绘制遮罩，保证导出的 mask 与原图 1:1 对齐。
2. 图片 + 遮罩以 multipart 提交到 `POST /api/inpaint`。
3. 后端解码并校验尺寸，按 `options.engine` 选择引擎：
   - **lama**：懒加载 `SimpleLama`（TorchScript 权重），`mask > 0` 的区域由 Fourier 卷积网络补全；
   - **opencv**：`cv2.inpaint(INPAINT_TELEA)` 传统算法兜底。
4. 结果 PNG 返回前端，用对比滑块展示并可下载。

## 致谢

- [advimman/lama](https://github.com/advimman/lama) — LaMa 模型与论文
- [enesmsahin/simple-lama-inpainting](https://github.com/enesmsahin/simple-lama-inpainting) — 推理封装

```bibtex
@article{suvorov2021lama,
  title={LaMa: Resolution-robust Large Mask Inpainting with Fourier Convolutions},
  author={Suvorov, Roman and Logacheva, Elizaveta and Mashikhin, Anton and Remizova, Anastasia and Ashukha, Aleksei and Silvestrov, Aleksei and Kong, Naejin and Goka, Harshith and Park, Kiwoong and Lempitsky, Victor},
  journal={arXiv:2109.07161},
  year={2021}
}
```
