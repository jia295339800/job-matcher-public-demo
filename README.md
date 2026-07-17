# Job Matcher Demo

一个可公开展示的求职岗位匹配 Demo。

- 仓库：<https://github.com/jia295339800/job-matcher-public-demo>
- 在线演示：<https://htmlpreview.github.io/?https://github.com/jia295339800/job-matcher-public-demo/blob/main/docs/index.html>

这个仓库包含经过筛选并脱敏的公开岗位信息和演示逻辑：企业名称、薪资及相关文字已隐藏，来源 URL 保留用于打开真实 JD；不包含真实简历、个人信息、猎聘/BOSS 登录态或任何授权 token。招聘页面可能随时间关闭或更新，链接以打开后的最新页面为准。

## 当前 Demo 能做什么

- 展示来自本地 Job Matcher 岗位池的公开职位信息、匹配分和审计详情；
- 点击岗位卡片上的 `✓` / `✕` 保留“合适/不合适”标记，标记会保存在当前浏览器；
- 点击“复制标记 JSON”导出当前标记，便于回到 Job Matcher 继续筛选；
- 每个岗位的来源名称都是可点击链接，可打开真实 JD 页面核验；
- 点击“刷新岗位”，模拟从职位源获取下一批职位；
- 对已有职位做去重，已有职位的 `new` 状态会被清除；
- 只有本次首次进入职位库的职位显示 `NEW`；
- 保留岗位的匹配分、薪资、地点、JD 要求、匹配优势/短板、审计证据和外部接口信息；
- 页面和本地服务均不需要 LLM；页面可由 GitHub Pages 或本地 HTTP 服务直接运行。

## 运行

需要 Python 3.10+，无第三方依赖：

```bash
python app/server.py
```

然后打开 <http://127.0.0.1:8765>。

仓库的 `docs/` 目录还包含一个无需后端的 GitHub Pages 静态演示版。发布后直接打开 Pages 链接即可使用“刷新岗位”和“重置演示”，不需要安装 Python、运行命令或配置 LLM。

演示流程：

1. 页面初始展示种子岗位；
2. 点击“刷新岗位”；
3. 新批次里的新职位显示 `NEW`；
4. 再次刷新后，上一批的 `NEW` 标签消失，只有新批次首次出现的职位保留 `NEW`。

## 目录结构

```text
app/
  server.py          # 本地 HTTP 服务（兼容旧的模拟 API）
docs/
  index.html         # GitHub Pages / 本地共用的静态演示版
  public_jobs.json   # 脱敏岗位详情与来源链接
data/
  seed_jobs.json     # 旧 API 兼容用的脱敏模拟职位和刷新批次
tests/
  test_store.py      # new/existing 增量逻辑测试
```

## 生产版如何接入

公开页面使用 `docs/public_jobs.json` 展示本地 Job Matcher 已整理的公开岗位；本地服务仍保留一组脱敏模拟 API 作为工程演示。生产版可以把 `fetch_candidates()` 替换为：

- 猎聘 CLI；
- BOSS/MCP 或其他招聘平台连接器；
- 公司官网、公开职位 API 或人工导入的数据源。

推荐采用两种刷新模式：

- **快速刷新**：只检索、去重和标记 `new`，不调用 LLM；
- **完整刷新**：只对新增或过期职位做 JD 抽取、语义匹配和评分，已有职位复用缓存。

LLM 不是页面刷新和增量合并的必需项。它主要用于新 JD 的语义解析、匹配解释和复杂评分。真实凭证应保存在本地服务端环境变量或系统密钥中，不能写进前端页面或提交到 GitHub。

## 说明

这个仓库是产品/工程能力演示，不代表真实岗位数据或真实匹配结果。生产版还需要增加登录态管理、平台服务条款控制、请求限流、任务队列、JD 抓取容错和持久化数据库。
