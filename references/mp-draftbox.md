# 公众号小绿书草稿箱自动化（mp.weixin.qq.com）

把「写好的标题+正文+话题标签」批量灌进公众号草稿箱、给草稿传配图——发表按钮永远由用户按。

## 与带货助手的差异（先读这个）

| 维度 | store.weixin.qq.com（带货助手） | mp.weixin.qq.com（公众号后台） |
|---|---|---|
| 页面架构 | micro-app shadow DOM 穿透 | **普通 DOM，无 micro-app**，直接 querySelector |
| 会话独立性 | 独立扫码 | 独立扫码；**用户在其他设备登录会把本会话挤掉**（已发生） |
| token | 无 | URL 里带 `token=<数字>`，登录一次换一个，过期后从新登录页重新取 |
| 安全边界 | 写操作请示 | **只建草稿、只保存，绝不点「发表」**（发表=真人参与的红线动作） |

## 登录与 token

1. `open --headed "https://mp.weixin.qq.com"` → 若记住旧账号，点「扫码登录」切换
2. 截图二维码递给用户扫（用**公众号管理员**微信）
3. 登录后从 URL 提取 token：`location.href.match(/token=(\d+)/)`
4. 后续所有 URL 带 `&token=<数字>`；报「登录超时」就重走扫码

## 草稿列表（JSON 接口，页面内 fetch）

```js
// 在 mp.weixin.qq.com 任意已登录页面内 eval
fetch('/cgi-bin/appmsg?action=list_ex&begin=0&count=15&type=77&token=' + TOKEN + '&lang=zh_CN&sub=list&query=')
  .then(r => r.text())
  .then(t => { const d = JSON.parse(t); return JSON.stringify(d.app_msg_list.map(a => ({ title: a.title, id: a.appmsgid }))); })
```

`type=77` = 贴图（小绿书）。返回按创建时间倒序。

## 批量建草稿（核心流程）

**编辑器结构**（`appmsg_edit_v2&action=edit&isNew=1&type=77&createType=8&token=...`）：

- 标题：`[contenteditable=true]` 且 `data-placeholder` 含「标题」
- 描述区：标题之外的另一个 contenteditable；话题标签直接写 `#标签`，保存后平台自动识别
- 每次打开新编辑页会弹功能介绍弹窗，点「我知道了」关掉

**注入片段**（先 eval 一段 `window.__piece = {title, body}`，再执行）：

```js
(() => {
  const p = window.__piece;
  const eds = [...document.querySelectorAll('[contenteditable=true]')];
  const title = eds.find(e => (e.getAttribute('data-placeholder') || '').includes('标题'));
  const desc = eds.filter(e => e !== title).pop();
  title.innerText = p.title;
  title.dispatchEvent(new Event('input', { bubbles: true }));
  desc.innerText = p.body;                    // 正文段落用 \n\n 分隔，末尾加 "\n\n#标签1 #标签2"
  desc.dispatchEvent(new Event('input', { bubbles: true }));
  return 'filled: ' + p.title;
})()
```

**保存与循环**：

```js
(() => {
  const ack = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === '我知道了');
  if (ack) ack.click();
  const save = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === '保存为草稿');
  if (!save) return 'NO SAVE BTN';
  save.click();
  return 'saved';
})()
```

- **无图也能保存草稿**——图片位留空不影响建稿，后续再补
- 保存成功的判据：URL 从 `isNew=1` 变为 edit 模式，或页面出现「操作时间」
- 批量时循环：`open 新编辑页（URL 加随机 timestamp 防缓存）→ sleep 6 → 注入 → 保存 → sleep 3`
- 完成后用草稿列表接口核对数量与标题

## 给已有草稿传配图

1. 草稿列表找到目标 → 打开编辑页：`appmsg_edit_v2&action=edit&appmsgid=<id>&token=...&type=77`
2. 页面上有多个隐藏的 `input[type=file]`，**先打印父链找唯一容器**：

```js
(() => {
  return [...document.querySelectorAll('input[type=file]')].map((i, k) => {
    let p = i, chain = [];
    for (let x = 0; x < 5 && p.parentElement; x++) { p = p.parentElement; chain.push(p.tagName + '.' + (p.className || '').toString().slice(0, 40)); }
    return k + ': ' + chain.join(' < ');
  }).join('\n');
})()
```

3. 图片位的输入框特征：父链含 `weui-desktop-upload` / `pop-opr__item`（悬浮工具条）；顶栏下拉菜单里的 input（`tpl_dropdown_menu`）不是它
4. **upload 命令只支持纯 CSS 选择器**，`>> nth=1` 报 CDP 错误：

```bash
./node_modules/.bin/agent-browser upload "div.weui-desktop-upload input[type=file]" "图1.png" "图2.png"
```

5. 验证：数 `img[src*=mmbiz]` 的数量、确认「选择或拖拽图片」占位文案消失
6. 传完点「保存为草稿」

## 图片规格备忘

- 小绿书推荐 3:4 → **1242×1660**，PNG 约 80–90KB 属正常轻量
- 首图 = 金句卡（第一张上传的自动成为封面缩略图）
- 本地渲染管线：`小绿书带货/tools/quote_card.py`（若随账号迁移，用 PIL + 华文楷体重写）

## 标准工作流（一次性会话）

1. 扫码登录 → 取 token
2. 批量建稿（10 篇约 3 分钟）→ 列表核对
3. 按篇传图 → 保存
4. 汇报：「草稿已就位，请在 App 里逐篇检查 → 设定时 → 自己按发表」

## 已踩过的坑（勿重复）

- `upload "input[type=file] >> nth=1"` → CDP `DOM.describeNode` 错误，必须纯 CSS
- 点击「选择或拖拽图片」文字区域无效（原生文件选择器无法自动化），必须直接对 input setValue
- 用户在电脑端自行登录后，本浏览器会话即失效——重新扫码，不用排查
- eval 里 fetch 跨域没问题（同域），但要用 `.then` 链或提前包 async，返回值会被序列化
