# JS 片段库（shadow DOM 穿透）

全部片段通过 `agent-browser eval "<片段>"` 执行。**所有片段必须 IIFE 包裹**——eval 作用域全局共享，裸 `const`/`let` 第二次执行即报 `Identifier has already been declared`。

## 1. 通用：shadow DOM 内按精确文本查找并点击

```js
(() => {
  function findText(root, txt) {
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while (n = w.nextNode()) { if (n.textContent.trim() === txt) return n.parentElement; }
    return null;
  }
  const ma = document.querySelector('micro-app');
  const t = ma && ma.shadowRoot ? findText(ma.shadowRoot, '目标文字') : findText(document, '目标文字');
  if (!t) return 'not found';
  t.click();
  return 'clicked: ' + t.tagName;
})()
```

适用：侧边栏菜单（首页/经营/选品/资金/数据/营销/管理）、类目标签（图书教培）、排序项（热销优先/高佣金优先）、弹窗按钮（我知道了）、首页卡片按钮（橱窗管理）。

## 2. 模糊匹配点击（按钮文字与相邻文本粘连时）

```js
(() => {
  function findFuzzy(root, part) {
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while (n = w.nextNode()) { if (n.textContent.trim().indexOf(part) >= 0) return n.parentElement; }
    return null;
  }
  const ma = document.querySelector('micro-app');
  const t = findFuzzy(ma.shadowRoot, '去绑定');
  if (!t) return 'not found';
  t.click();
  return 'clicked: [' + t.textContent.trim() + ']';
})()
```

实战案例：首页公众号栏「暂无账号，去绑定」——精确匹配「去绑定」失败，模糊匹配命中整个字符串后成功。

## 3. 列出 shadow root 全部可点击文本（探路用）

```js
(() => {
  const sr = document.querySelector('micro-app').shadowRoot;
  const w = document.createTreeWalker(sr, NodeFilter.SHOW_TEXT);
  const out = [];
  let n;
  while (n = w.nextNode()) {
    const s = n.textContent.trim();
    if (s && s.length < 20) out.push(s);
  }
  return out.join(' | ');
})()
```

## 4. 正文数据切片提取

```js
(() => {
  const sr = document.querySelector('micro-app').shadowRoot;
  const t = sr.textContent || '';
  const i = t.indexOf('锚定关键词');
  return i >= 0 ? t.slice(i, i + 3000) : 'anchor not found; head: ' + t.slice(0, 200);
})()
```

注意：切片尾部会带出 `<style>` 内容（`--weuiDesktop_...` CSS 变量），读到 `:root {` 即可截断。

## 5. 搜索框 focus + 键盘注入

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

focus 后执行：

```bash
./node_modules/.bin/agent-browser keyboard inserttext "认知觉醒 周岭"
```

再点击「搜索」按钮（用片段 1）。

## 6. 诊断：shadow root 是否存在 / micro-app 数量

```js
(() => {
  const mas = document.querySelectorAll('micro-app');
  return 'micro-apps: ' + mas.length + '; url: ' + location.href +
    (mas[0] && mas[0].shadowRoot ? '; shadow ok' : '; NO SHADOW (未登录或加载中)');
})()
```

返回 `NO SHADOW` 通常意味着登录超时或页面未加载完成，先 sleep 再试，仍不行走重登录流程。

## 7. 下拉选择（选品广场筛选器）

筛选器（商品排序/服务保障/月销量/好评率/店铺评分/佣金比例）都是「点击展开 → 点击选项」两步：

1. 片段 1 点击筛选器当前值（如「按推荐顺序」）
2. sleep 2
3. 片段 1 点击选项（如「热销优先」）
4. sleep 5 等列表刷新

# 页面结构备忘

- **登录页**（超时后）：`heading "登录超时，请重新 登录"` + `link "登录"`——这个登录链接**不在 shadow root 里**，普通 `click e2` 或 `find text "登录" click` 即可
- **首页卡片**：账号名/带货等级/信用分 → 数据看板（近7日成交金额/订单/预计佣金）→ 橱窗卡片（N件在售 + 橱窗管理/预览/分享）→ 视频号卡片 → 公众号卡片（已绑定显示账号名，未绑定显示「暂无账号，去绑定」）→ 0保证金权益横幅
- **橱窗管理页**：筛选区（商品来源/售卖状态/展示状态）→ 商品列表（商品信息/讲解回放/价格/佣金率/投流佣金率/库存/操作：隐藏·置顶·移除·详情）→ 底部批量操作
- **选品广场**：搜索框 → 类目行（更多折叠）→ 筛选行（商品排序/服务保障/价格/月销量/好评率/店铺评分）→ 商品卡片流（商品名/月销/标识/店铺/评分/赚/到手价/佣金率/联系商家/加橱窗）
- **「加橱窗」按钮**：写操作。点击后可能弹「投流佣金说明」确认框（我已阅读并同意《优选联盟投流佣金使用须知》）——先向用户请示，确认后连点两步

# 已验证的任务模板

## A. 橱窗商品全量核对

首页 → 片段 1 点「橱窗管理」→ 片段 4 以「商品管理」为锚切片（长度给 3000+，9 件商品约需 3000 字符）→ 正则/人工整理为表格：商品 | 店铺 | 价格 | 佣金率 | 单笔 | 服务费标识 | 库存。

## B. 单商品多店铺佣金对比

选品广场 → 片段 5 搜索「书名 作者」→ 片段 1 点「搜索」→ 片段 4 以「月销」为锚切片 → 每店一行：店铺 | 价格 | 佣金 | 标识 | 月销 | 评分 → 按「佣金率 × 价格可信度（到手价是否 Publishers 定价）× 月销量」推荐。

**坑：目标店铺在商品搜索里排序波动极大**。同一店铺时隔半小时再搜可能翻 6+ 屏都找不到（推荐序和高佣序都如此）。解法：**直接按店铺名搜索**（搜索框支持检索店铺，placeholder 明示「可通过关键词检索店铺、商品」）——搜「合月同行」直接命中其全部在联盟商品，一次到位。

## C. 加橱窗（写操作，先请示）

选品广场找到目标卡片（店铺名搜索最快）→ 用 TreeWalker 从「店铺名」文本节点向上找卡片容器（特征：同时含「到手价」和「加橱窗」且长度 <600 字符）→ 在容器内点「加橱窗」→ 验证按钮文字变「已添加」。若弹「投流佣金说明」确认框，需再点「我已阅读并同意」。最终去橱窗管理页确认商品数 +1。

```js
// 卡片定位 + 点击（已验证可用的完整逻辑）
(() => {
  const sr = document.querySelector('micro-app').shadowRoot;
  const w = document.createTreeWalker(sr, NodeFilter.SHOW_TEXT);
  let n, storeEl = null;
  while (n = w.nextNode()) { if (n.textContent.trim() === '店铺名') { storeEl = n.parentElement; break; } }
  if (!storeEl) return 'store not found';
  let card = storeEl;
  for (let i = 0; i < 12; i++) {
    if (card.parentElement && card.textContent.indexOf('加橱窗') >= 0
        && card.textContent.indexOf('到手价') >= 0 && card.textContent.length < 600) break;
    card = card.parentElement;
    if (!card) return 'card boundary lost';
  }
  const btns = [];
  const w2 = document.createTreeWalker(card, NodeFilter.SHOW_TEXT);
  let m;
  while (m = w2.nextNode()) { if (m.textContent.trim() === '加橱窗') btns.push(m.parentElement); }
  if (!btns.length) return 'no button';
  btns[0].click();
  return 'clicked';
})()
```

## D. 类目热销榜

选品广场 → 点「更多」展开 → 点类目 → 排序选「热销优先」→ 翻页滚动 + 片段 4 切片。

## 8. 文件上传（mp 后台传图等场景）

- `upload <selector> <files...>` 可传多个文件；**只支持纯 CSS 选择器**，`>> nth=1` 会报 CDP 错误
- 页面上的 `input[type=file]` 多为隐藏且可能有多个——先用 eval 打印每个 input 的父链定位唯一容器，再写精确 CSS 选择器，如 `div.weui-desktop-upload input[type=file]`
- 传完验证：数 `img[src*=mmbiz]` 数量 / 确认占位文案消失
- mp 后台（mp.weixin.qq.com）与小店后台同理：页面无 micro-app，直接 document 查询；token 在 URL 里，登录过期后换新 token 重开即可

> 小绿书草稿批量创建 + 配图上传的完整流程（登录/token/注入/保存/规格/死路清单）见 `references/mp-draftbox.md`。
