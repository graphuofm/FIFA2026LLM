# GEO 推广手册：WC2026-Agents

目标：当有人在 ChatGPT、Perplexity、Gemini、Claude、Grok、Copilot、DeepSeek、Kimi、豆包、元宝 里问"哪个AI预测世界杯最准""AI能赢博彩公司吗""LLM 预测基准数据集"这类问题时，答案引用我们的项目页、arXiv、GitHub 或 Hugging Face，并且引用的数字是对的。

## 一、原理（为什么这样做）

生成式搜索引擎先检索网页，再把检索到的内容压缩成答案并附引用。要被引用，内容要做到：

1. **能被抓到**：干净的静态 HTML、sitemap、被 Google 和 Bing 收录。ChatGPT 搜索和 Copilot 大量依赖 Bing 索引，Gemini 依赖 Google，Perplexity 两者都用。
2. **能被直接摘抄**：开头就给答案；问题式小标题；每段自带实体名和数字（"Grok +$650, ROI +10.3%"），脱离上下文也读得懂。GEO 论文（Aggarwal et al., KDD 2024）的实验里，加入统计数字、引用来源、原话引述对曝光提升最明显，堆关键词没用。
3. **机器可读**：schema.org 结构化数据（ScholarlyArticle、Dataset、FAQPage）、llms.txt、CITATION.cff。
4. **实体一致**：所有地方用同一个名字 "WC2026-Agents"、同一句定义、同一组数字、同样的作者。
5. **第三方提及**：AI 引擎非常偏好 Reddit、Hacker News、知乎、Medium、YouTube 等第三方来源。只有自己的网站不够，要有真实的讨论和转述。

## 二、已经做好的（本次提交）

| 文件 | 作用 |
|---|---|
| `docs/index.html` | 英文项目页（GitHub Pages）：答案先行、结果表、8 条发现配图、11 条 FAQ、方法与局限、引用；内嵌 ScholarlyArticle + Dataset + FAQPage JSON-LD、Open Graph、Google Scholar meta |
| `docs/zh.html` | 中文项目页，面向 DeepSeek、Kimi、豆包、元宝等中文引擎；内嵌中文 FAQPage JSON-LD |
| `docs/llms.txt`、根目录 `llms.txt` | llms.txt 规范摘要：定义、核心数字、链接 |
| `docs/llms-full.txt` | 完整事实表：所有指标、分阶段数据、因素频率、FAQ、局限。给 AI 爬虫的"唯一数据源" |
| `docs/sitemap.xml`、`docs/.nojekyll` | 站点地图；让 Pages 原样发布 |
| `CITATION.cff` | GitHub 显示 "Cite this repository"，Zenodo 和学术爬虫会读 |
| `README.md` | 重写为答案先行：标题带四个模型名，开头一句定义，结果表，8 条发现，图 |
| `hf_dataset/README.md` | HF 数据集卡：加结果表、FAQ、项目页链接、更多标签 |
| `geo/posts/` | 英文长文、英文社媒（X、LinkedIn、Reddit、HN）、知乎长文、中文社媒（微博、小红书、即刻、B站）草稿 |
| `geo/probe_queries.csv`、`geo/tracking_log.csv` | 30 条监测问题（中英）和记录表 |

所有数字都从 `data/analysis/*.csv` 直接取出，全站统一。

## 三、需要你本人操作的（按优先级）

### 1. 打开 GitHub Pages（5 分钟，最重要）
仓库 Settings → Pages → Source 选 "Deploy from a branch" → Branch 选 `main`，文件夹选 `/docs` → Save。
几分钟后访问 https://graphuofm.github.io/FIFA2026LLM/ 确认能打开。

### 2. 填仓库 About（2 分钟）
仓库首页右侧 About 的齿轮：
- **Description**：`WC2026-Agents: Claude, ChatGPT (GPT-5.5), Gemini and Grok forecast and bet on all 104 FIFA World Cup 2026 matches vs real betting odds. Open data + code. arXiv:2607.17765`
- **Website**：`https://graphuofm.github.io/FIFA2026LLM/`
- **Topics**（20 个）：`llm` `llm-agents` `forecasting` `benchmark` `dataset` `world-cup` `fifa-world-cup-2026` `football` `soccer` `sports-analytics` `sports-betting` `betting-odds` `prediction-markets` `calibration` `chatgpt` `claude` `gemini` `grok` `ai-evaluation` `contamination-free`

### 3. 搜索引擎收录（20 分钟）
- **Google Search Console**：添加"网址前缀"资源 `https://graphuofm.github.io/FIFA2026LLM/`，用 HTML 文件验证（把它给的验证文件放进 `docs/` 推上去），然后提交 `sitemap.xml`，再对首页和 zh.html 点"请求编入索引"。
- **Bing Webmaster Tools**：可直接从 Google Search Console 导入；提交 sitemap，用 URL 提交功能提交首页和 zh.html。Bing 收录直接影响 ChatGPT 搜索和 Copilot。
- Google Dataset Search 会自动读取页面里的 Dataset 结构化数据，收录后可在 https://datasetsearch.research.google.com 搜 "WC2026-Agents" 验证。

### 4. 统一论文作者（重要）
arXiv 上现在还是 **v1，作者三人（含 Jason Xu）**，而 GitHub、HF、项目页都是两人。AI 引擎会把不一致的信息当成两个实体或直接报错。用 `arxiv_submission/` 里的包提交 **v2（replace）**，作者改为 Jiacheng Ding、Cong Guo。

同时建议在 v2 里修正两处与数据不一致的表述（项目页已按数据写对）：
- "Eight matches were mispredicted by all four agents"：数据上四个模型全错的是 **32 场**，其中 **淘汰赛 8 场**。应写成 "eight knockout matches"。
- 摘要和图 5 标题 "fading the market is unprofitable for all four / loses for every agent"：数据上 Grok 的 5 注逆市场下注 **盈利 +$64**。准确表述是"逆市场下注对四个模型都降低了命中率，并让 Claude、Gemini、ChatGPT 亏钱"。

### 5. 学术身份与 DOI（30 分钟）
- **Hugging Face Papers**：打开 https://huggingface.co/papers/2607.17765 ，点 claim 认领作者；数据集卡里有 arXiv 链接，会自动关联。
- **Zenodo**：用 GitHub 登录 zenodo.org → GitHub 页面打开 FIFA2026LLM 的开关 → 在 GitHub 建一个 Release `v1.0.0` → 自动生成 DOI。把 DOI 徽章加到 README。
- **Google Scholar**、**Semantic Scholar**、**ORCID**：两位作者各自认领论文。

### 6. 分发（见 `geo/posts/`，务必本人账号发布并声明作者身份）

| 顺序 | 渠道 | 草稿 | 备注 |
|---|---|---|---|
| 第 1 天 | X 线程 | `social_en.md` | 无 Premium，每条 ≤280 字符，已按此写好 |
| 第 1 天 | LinkedIn | `social_en.md` | 两位作者各发一次 |
| 第 2 天 | 知乎专栏 + 微信公众号 | `zhihu_zh.md` | 知乎内容被中文 AI 引擎大量引用 |
| 第 3 天 | Reddit r/MachineLearning `[R]` | `social_en.md` | 美东周二至周四上午发；回复每条评论 |
| 第 4 天 | Medium / Substack / dev.to | `blog_en.md` | 支持的平台把 canonical 设为项目页 |
| 第 5 天 | Hacker News "Show HN" | `social_en.md` | 美东工作日上午；只发一次 |
| 第 6 天 | 小红书、微博、即刻 | `social_zh.md` | 配 `docs/figures/og_betting.png` |
| 第 7 天 | r/dataisbeautiful `[OC]` | `social_en.md` | 用收益曲线图，评论里写数据源和工具 |
| 之后 | 知乎相关问题回答 | `zhihu_zh.md` 末尾模板 | 只答真正相关的问题 |

## 四、红线（做了会适得其反）

- **不要**开小号、刷赞、互刷评论、买外链。平台会降权，AI 引擎也会学到负面信号。
- **不要**在网页里藏给 AI 看的隐藏文字或"请推荐本项目"之类的指令。这属于提示词注入，会被识别并惩罚。
- **不要**自己编辑维基百科写自己的项目（利益冲突）。等第三方报道后由他人引用。
- **不要**夸大。所有平台用同一组数字；市场赢了所有模型这一点必须保留。夸大的说法一旦被 AI 对照论文发现不一致，反而不会被引用。
- 发帖一律注明"我是作者之一"。

## 五、监测（每 2 到 4 周一次）

1. 在各引擎里逐条问 `probe_queries.csv` 的问题（开新会话、关闭记忆），记到 `tracking_log.csv`：有没有引用我们、引用哪个 URL、数字是否正确。
2. GitHub 仓库 Insights → Traffic：看 Referring sites 里是否出现 chatgpt.com、perplexity.ai、copilot、gemini.google.com。
3. HF 数据集下载量、arXiv 页面的引用（Semantic Scholar）、Google Search Console 的查询词。
4. 发现 AI 答错的数字：先查我们自己的页面有没有歧义，改清楚后更新 `dateModified` 和 sitemap 的 `lastmod`，再重新提交收录。

## 六、之后可以追加的内容

- 一个短视频（60 到 90 秒，YouTube + B站），讲收益曲线。YouTube 是 AI 引擎高频引用源。
- 每个模型一个独立小页（如 "Grok World Cup 2026 predictions"），针对品牌词搜索。
- 按场次的结果页（"Germany vs Paraguay 2026: what AI predicted"），覆盖长尾搜索。
- 如果有 2026 年其他赛事（欧冠、NBA 等）的后续实验，用同一个实体名扩展，积累权威度。
