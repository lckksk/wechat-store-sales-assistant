---
name: wechat-store-sales-assistant
description: 用 agent-browser 接管微信小店带货助手（视频号/公众号带货）网页后台与公众号小绿书草稿箱，代用户完成选品广场筛品、橱窗商品数据核对、佣金对比、榜单分析、批量建小绿书草稿、给草稿传配图等操作。当用户要求「替我操作带货助手/橱窗/选品中心」「拉一下橱窗数据」「对比某商品的佣金」「看看选品广场榜单」「把文案灌进草稿箱」「给草稿传图」，或任何需要操作 store.weixin.qq.com / mp.weixin.qq.com 后台的任务时使用。包含登录流程、micro-app shadow DOM 穿透模式、数据提取方法与安全边界。
agent_created: true
---

# 微信小店带货助手 · 浏览器自动化接管

## Overview

微信小店带货助手（`store.weixin.qq.com/talent/*`）没有开放 API，选品、橱窗管理只能人肉点页面。本 skill 让 agent 用 agent-browser 打开有界面浏览器，用户扫码登录一次，之后 agent 代为读数据、筛品、做佣金对比——把 15 分钟的手动筛品压缩到一条指令。

**已验证可完成的任务**：橱窗商品全量数据提取（价格/佣金率/单笔佣金/服务费标识/库存）、按书名搜索多店铺佣金对比、类目热销榜单提取、筛选器组合筛选（佣金比例/月销量/好评率/店铺评分）、**公众号小绿书草稿批量创建与配图上传**（mp.weixin.qq.com，见 `references/mp-draftbox.md`）。

**安全边界（必须遵守）**：
- **读操作直接执行**：页面浏览、数据提取、搜索、筛选、截图
- **写操作先请示**：加橱窗、移除、隐藏/取消隐藏、置顶、任何提交类按钮——每次先向用户报告将要点什么，得到确认再点
- 不触碰资金页面（提现、保证金缴纳）——即使用户要求，也引导用户自己去「资金」页操作

## 环境准备（首次约 5–10 分钟，之后跳过）

```bash
# 1. agent-browser 装进受管 Node workspace（不污染全局）
cd "C:/Users/Lenovo/.workbuddy/binaries/node/workspace"
npm install agent-browser

# 2. 下载 Chromium 内核（约 500MB，后台跑）
./node_modules/.bin/agent-browser install
```

Windows 下用 Git Bash 执行。所有命令通过 `./node_modules/.bin/agent-browser` 调用。

## 启动与登录

```bash
# 关键：--headed 有界面模式。无界面模式用户看不到窗口，扫码只能靠截图转发
./node_modules/.bin/agent-browser close   # 清掉可能残留的旧会话
./node_modules/.bin/agent-browser open --headed "https://store.weixin.qq.com/talent/home?from=platform"
```

**登录要点**：

1. 两个域名会话**完全独立**，各自扫一次码：
   - `channels.weixin.qq.com`（视频号助手：看播放数据、视频管理）
   - `store.weixin.qq.com`（小店带货助手：橱窗、选品、资金——本 skill 主战场）
2. 扫码必须用户配合。流程：截图 → `present_files` 递给用户 → 用户用**绑定了视频号的业务微信**扫 → 用户口头确认已扫 → agent 检查页面状态，若停留在确认页则替用户点「微信快捷登录」
3. 用户有多个微信号时，**先让用户核对手机确认页上的昵称再点确认**——扫错号是已发生过的坑（识别到主号「缄默」而非业务号）
4. 登录页若记住了上次的账号，点「使用其他头像、昵称或账号」重置二维码

**会话有效期很短**（实测约 10 分钟无操作即超时）。超时页面显示「登录超时，请重新登录」：点「登录」→ 新二维码 → 用户重扫。属于正常损耗，直接走流程，不用道歉拖延。

## 核心操作模式：micro-app shadow DOM 穿透（本 skill 的灵魂）

**页面结构**：带货助手的正文全部渲染在 `<micro-app>` 自定义元素的 shadow root 里（微前端架构）。后果：

- `agent-browser snapshot` 能穿透 shadow DOM，**元素可见但多无 ref**，StaticText 无法直接 click
- `click "text=xxx"`、`find text "xxx" click` **经常报 Element not found**（因为它们不穿透 micro-app 的 shadow root）
- 自研 eval 脚本不穿透就会一无所获

**标准操作模式——TreeWalker 穿透点击**：

```js
// 通过 eval 执行。IIFE 包裹防止 const 重声明报错（eval 作用域全局共享！）
(() => {
  function findText(root, txt) {
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while (n = w.nextNode()) { if (n.textContent.trim() === txt) return n.parentElement; }
    return null;
  }
  const ma = document.querySelector('micro-app');
  const t = ma && ma.shadowRoot ? findText(ma.shadowRoot, '橱窗管理') : findText(document, '橱窗管理');
  if (!t) return 'not found';
  t.click();
  return 'clicked';
})()
```

**精確文本匹配失败时**，改用 indexOf 模糊匹配（按钮文字可能和其他文字拼在同一节点，如「暂无账号，去绑定」）：

```js
if (n.textContent.trim().indexOf('去绑定') >= 0) { ... }
```

**其他关键命令**：

```bash
./node_modules/.bin/agent-browser eval "location.href"          # 导航是否成功的唯一可靠判据
./node_modules/.bin/agent-browser screenshot                    # 每次关键操作后截图确认
./node_modules/.bin/agent-browser keyboard inserttext "关键词"   # 输入框 focus 后用键盘注入，不走 fill
```

**已踩过的死路（勿重复）**：
- `eval "const el = ..."` 第二次执行报 `Identifier 'el' has already been declared` → 全部用 IIFE
- `document.elementFromPoint(x, y)` 定位 shadow DOM 内元素 → 返回的是外层容器，不可用
- `micro-app` 外层 iframe 是登录组件（无 src），与正文无关，勿浪费时间探查
- 对「橱窗管理」等按钮用 `mouse move/down/up` 坐标点击 → 点击事件不触发导航，必须 `element.click()`

## 数据提取模式

读正文用 `shadowRoot.textContent` 切片（比逐元素解析快且稳）：

```js
(() => {
  const sr = document.querySelector('micro-app').shadowRoot;
  const t = sr.textContent || '';
  const i = t.indexOf('商品管理');          // 锚定起始关键词
  return i >= 0 ? t.slice(i, i + 3000) : t.slice(0, 1500);
})()
```

返回的连续文本里，商品数据格式固定：`商品名...店铺名 价格 佣金率%（单笔¥x）库存数 操作项`。用正则或人工分段整理成表格。识别要点：

- `限免服务费` = 技术服务费（佣金 10%）免收，佣金全额到手——选品的优先标识
- `高赚` / `中赚` = 平台对佣金档位的标注，筛品优先「高赚」
- 月销格式 `8.7万+`、`393`

输入框定位（shadow root 内的 input）：

```js
(() => {
  const inputs = [];
  const walk = (node) => {
    if (node.querySelectorAll) {
      node.querySelectorAll('input').forEach(i => inputs.push(i));
      node.querySelectorAll('*').forEach(e => { if (e.shadowRoot) walk(e.shadowRoot); });
    }
  };
  walk(document.querySelector('micro-app').shadowRoot);
  if (!inputs.length) return 'no input';
  inputs[0].focus();
  return 'focused: ' + inputs[0].placeholder;
})()
```

## 页面地图（已验证的 URL）

| 页面 | URL | 说明 |
|---|---|---|
| 首页 | `https://store.weixin.qq.com/talent/home?from=platform` | 账号状态、橱窗入口、公众号绑定状态 |
| 橱窗管理 | `https://store.weixin.qq.com/talent/channel/window` | 从首页「橱窗管理」进入；9 件商品的完整佣金数据 |
| 选品广场 | `https://store.weixin.qq.com/talent/pool/home` | 搜索商品、类目筛选、多店佣金对比 |
| 视频号助手 | `https://channels.weixin.qq.com/platform` | 独立会话；侧边栏无带货入口，勿反复寻找 |

侧边栏菜单：首页 / 经营 / 选品（子菜单：选品广场·合作选品·招商中心·联盟规则）/ 资金 / 数据 / 营销 / 管理。选品广场类目里「图书教培」在「更多」折叠区。

## 标准工作流

1. `open --headed` 打开首页 → 检查是否要求登录（要求则走扫码流程）
2. 读首页确认账号状态（橱窗件数、信用分、绑定状态）
3. 按任务导航：数据核对 → 橱窗管理；筛品/对比 → 选品广场
4. TreeWalker eval 点击 + textContent 切片提取 → 整理成表格
5. 产出物存到用户的项目目录（如 `小绿书带货/` 下的编号文档），`present_files` 交付

更多可直接复制的 JS 片段和页面结构细节见 `references/js-snippets.md`。

**草稿箱任务**（把文案批量灌进公众号草稿箱、传配图）：架构与带货助手完全不同（普通 DOM、token 机制、只保存不发表），完整流程见 `references/mp-draftbox.md`。
