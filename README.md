# wechat-store-sales-assistant

微信小店带货助手（store.weixin.qq.com）的浏览器自动化操作 Skill。用 agent-browser 接管后台，代用户完成选品、橱窗数据核对、佣金对比。

## 安装

将本目录复制到 `~/.workbuddy/skills/wechat-store-sales-assistant`（或用 WorkBuddy 的技能导入），新会话即可自动触发。

## 结构

- `SKILL.md` — 核心流程：环境准备、扫码登录、micro-app shadow DOM 穿透模式、数据提取、安全边界
- `references/js-snippets.md` — 可直接复制的 JS 片段库与页面结构备忘

## 适用场景

- 「替我操作带货助手 / 橱窗 / 选品中心」
- 「拉一下橱窗商品的佣金数据」
- 「对比某本书在各店铺的佣金」
- 「看看选品广场图书类目的热销榜」

## 安全边界

只读操作（浏览、提取数据、搜索、截图）直接执行；写操作（加橱窗、移除、隐藏、置顶）每次先向用户请示；资金操作（提现、保证金）不代操作。
