"""Generate a self-contained HTML page for hand-labelling the validation sample.

    python src/rebuttal_make_label_tool.py   ->  rebuttal/label_tool.html

Open that file in a browser, label each item, then copy the CSV it produces back
into data/analysis/rebuttal/lexicon_validation_sample.csv and run
`python src/rebuttal_lexicon_sample.py score`.
Progress is kept in the browser, so it is safe to close and come back.
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "data" / "analysis" / "rebuttal" / "lexicon_validation_sample.csv"
OUTFILE = ROOT / "rebuttal" / "label_tool.html"

HTML = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lexicon validation labelling</title>
<style>
 :root{--ink:#1d232b;--ink2:#5a6270;--line:#dfe3e8;--bg:#fbfbfa;--card:#fff;--yes:#2f9e44;--no:#e03131;--accent:#1c6fd0}
 body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.7 system-ui,-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
 main{max-width:820px;margin:0 auto;padding:24px 18px 80px}
 h1{font-size:1.25rem;margin:0 0 4px}
 .rule{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:8px;padding:12px 16px;margin:14px 0;font-size:.93rem}
 .rule b{color:var(--accent)}
 .bar{height:8px;background:var(--line);border-radius:99px;overflow:hidden;margin:16px 0 6px}
 .bar>div{height:100%;background:var(--accent);width:0;transition:width .2s}
 .meta{color:var(--ink2);font-size:.85rem;display:flex;justify-content:space-between}
 .card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:14px 0;font-size:1.02rem;min-height:180px;white-space:pre-wrap}
 .btns{display:flex;gap:12px;flex-wrap:wrap}
 button{font:inherit;font-weight:650;padding:12px 22px;border-radius:9px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
 button.yes{background:var(--yes);color:#fff;border-color:var(--yes)}
 button.no{background:var(--no);color:#fff;border-color:var(--no)}
 button.ghost{color:var(--ink2)}
 kbd{background:#eef1f4;border:1px solid var(--line);border-bottom-width:2px;border-radius:5px;padding:1px 6px;font-size:.82em}
 textarea{width:100%;height:220px;font:12px/1.5 ui-monospace,Consolas,monospace;border:1px solid var(--line);border-radius:8px;padding:10px}
 .done{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px}
 a{color:var(--accent)}
</style></head><body><main>
<h1>关键词词典人工校验</h1>
<p class="meta">共 __N__ 条。判断每段推理文字<b>是否提到了博彩赔率或市场定价</b>。</p>

<div class="rule">
判断标准是:<b>这段文字有没有引用博彩市场的价格信息</b>。<br><br>
<b>标 1(是)</b>:提到赔率(-150、8/15、1.85 这类)、隐含概率、盘口、市场定价、"market prices them at"、博彩公司名(DraftKings、bet365、FanDuel、Vegas)、"betting favorite"。<br>
<b>标 0(否)</b>:只讲球队实力、状态、伤病、FIFA 排名、历史交锋。<br><br>
两个容易犹豫的情况:<br>
• 只说"某队是热门/clear favourite"但<b>没有</b>任何价格或赔率 &rarr; 标 <b>0</b><br>
• 提到 <b>Opta 超级计算机</b>或其他预测模型给出的百分比(不是博彩赔率)&rarr; 标 <b>0</b><br>
• 一段里既有 Opta 又有赔率 &rarr; 标 <b>1</b>(只要出现了赔率就算)
</div>

<div class="bar"><div id="prog"></div></div>
<div class="meta"><span id="count"></span><span id="idlab"></span></div>

<div id="view">
  <div class="card" id="text"></div>
  <div class="btns">
    <button class="yes" onclick="mark(1)">提到了赔率/市场 &nbsp;<kbd>1</kbd></button>
    <button class="no" onclick="mark(0)">没提到 &nbsp;<kbd>0</kbd></button>
    <button class="ghost" onclick="back()">上一条 &nbsp;<kbd>&larr;</kbd></button>
  </div>
</div>

<div id="done" class="done" style="display:none">
  <p><b>标完了。</b>把下面整段复制,粘贴覆盖 <code>data/analysis/rebuttal/lexicon_validation_sample.csv</code>,然后运行 <code>python src/rebuttal_lexicon_sample.py score</code>,或者直接把它贴回对话里给我。</p>
  <textarea id="out" readonly></textarea>
  <div class="btns" style="margin-top:10px">
    <button onclick="copyOut()">复制</button>
    <button class="ghost" onclick="reset()">全部重标</button>
  </div>
</div>

<script>
const ITEMS = __ITEMS__;
const KEY = "wc2026_lexicon_labels";
let labels = JSON.parse(localStorage.getItem(KEY) || "{}");
let i = 0;

function firstUnlabelled(){ for(let k=0;k<ITEMS.length;k++){ if(labels[ITEMS[k].id]===undefined) return k; } return ITEMS.length; }
function save(){ try{ localStorage.setItem(KEY, JSON.stringify(labels)); }catch(e){} }

function render(){
  const n = ITEMS.length, done = Object.keys(labels).length;
  document.getElementById("prog").style.width = (100*done/n) + "%";
  document.getElementById("count").textContent = "已标 " + done + " / " + n;
  if(i >= n){
    document.getElementById("view").style.display = "none";
    document.getElementById("done").style.display = "block";
    document.getElementById("idlab").textContent = "";
    let csv = "item_id,reasoning,human_cites_market\\n";
    for(const it of ITEMS){
      const v = labels[it.id]===undefined ? "" : labels[it.id];
      csv += it.id + ',"' + it.text.replace(/"/g,'""') + '",' + v + "\\n";
    }
    document.getElementById("out").value = csv;
    return;
  }
  document.getElementById("view").style.display = "block";
  document.getElementById("done").style.display = "none";
  document.getElementById("idlab").textContent = "第 " + (i+1) + " 条 (" + ITEMS[i].id + ")";
  document.getElementById("text").textContent = ITEMS[i].text;
}
function mark(v){ labels[ITEMS[i].id] = v; save(); i++; render(); }
function back(){ if(i>0){ i--; delete labels[ITEMS[i].id]; save(); render(); } }
function reset(){ if(confirm("清空所有标注?")){ labels = {}; save(); i = 0; render(); } }
function copyOut(){ const t = document.getElementById("out"); t.select(); document.execCommand("copy"); }
document.addEventListener("keydown", e => {
  if(e.key === "1") mark(1);
  else if(e.key === "0") mark(0);
  else if(e.key === "ArrowLeft") back();
});
i = firstUnlabelled();
render();
</script>
</main></body></html>
"""


def main():
    df = pd.read_csv(SAMPLE)
    items = [{"id": r.item_id, "text": str(r.reasoning)} for r in df.itertuples(index=False)]
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    html = HTML.replace("__ITEMS__", json.dumps(items, ensure_ascii=False)).replace("__N__", str(len(items)))
    OUTFILE.write_text(html, encoding="utf-8")
    print(f"wrote {OUTFILE} with {len(items)} items")


if __name__ == "__main__":
    main()
