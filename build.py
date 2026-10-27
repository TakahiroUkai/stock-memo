#!/usr/bin/env python3
"""data/picks.json から静的サイト(docs/)を生成する。
毎日の更新: data/picks.json の配列の先頭に1件追加して `python3 build.py` を実行する。
公開リポジトリなので、非公開の評価データ(チェック表・特定の専門家名など)は絶対にここへ入れない。"""
import json, html, os, re, shutil, sys
SITE = "注目銘柄メモ"
TAGLINE = "今は目立たないが、これから重要になりそうな日本企業の個人調査メモ"
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")
AD_SLOT = '<aside class="ad" aria-label="広告"><!-- AdSense承認後、ここに広告コードを貼る --><span>広告枠</span></aside>'
DISC = ("本ページは個人の調査メモであり、特定の銘柄の売買を勧めるものではありません。"
        "掲載内容の正確性には注意していますが、誤りや時間の経過による変化があり得ます。"
        "投資の判断はご自身の責任で行ってください。株価などの数値は記載時点のものです。")

CSS = """:root{--bg:#f4f5f7;--s:#fff;--fg:#1c2330;--mu:#5b6575;--ln:#d9dee6;--ac:#1f4fb4;--acs:#e5ecfa}
@media(prefers-color-scheme:dark){:root{--bg:#0f141c;--s:#171e29;--fg:#e6eaf1;--mu:#9aa4b5;--ln:#2a3342;--ac:#8fb0ff;--acs:#1d2a47}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.8 "Noto Sans JP",-apple-system,"Hiragino Sans",sans-serif;padding:0 16px 48px}
.wrap{max-width:760px;margin:0 auto}header{padding:22px 0 8px}header a{color:inherit;text-decoration:none}
h1{font-size:1.6rem;line-height:1.35;margin:0}.tag{color:var(--mu);font-size:.88rem;margin:4px 0 0}
nav.links{font-size:.85rem;margin:10px 0}nav.links a{color:var(--ac);margin-right:14px}
.list{background:var(--s);border:1px solid var(--ln);border-radius:10px;overflow:hidden}
.list a{display:grid;grid-template-columns:6rem 1fr;gap:10px;padding:12px 14px;border-top:1px solid var(--ln);color:inherit;text-decoration:none}
.list a:first-child{border-top:0}.list a:hover{background:var(--acs)}.list .d{color:var(--mu);font-size:.82rem}.list .t{color:var(--mu);font-size:.85rem;grid-column:2}
article{background:var(--s);border:1px solid var(--ln);border-radius:10px;padding:18px 16px;margin-top:12px}
article h2{font-size:1.4rem;line-height:1.4;margin:0 0 4px}article h3{font-size:1.1rem;margin:22px 0 8px;padding-top:14px;border-top:1px solid var(--ln)}
.theme{color:var(--mu);margin:0 0 12px}.concl{background:var(--acs);border-radius:8px;padding:12px 14px;margin:12px 0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(7rem,1fr));gap:1px;background:var(--ln);border:1px solid var(--ln);border-radius:8px;overflow:hidden;margin:12px 0}
.stats div{background:var(--s);padding:8px 12px}.stats dt{font-size:.72rem;color:var(--mu);margin:0}.stats dd{margin:0;font-weight:700}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:.88rem}th,td{border-bottom:1px solid var(--ln);padding:6px 8px;text-align:left;vertical-align:top}th{color:var(--mu);white-space:nowrap}
.note,.src,.disc{font-size:.82rem;color:var(--mu)}.src a{color:var(--ac);overflow-wrap:anywhere}.disc{border-top:1px solid var(--ln);padding-top:12px;margin-top:18px}
.ad{margin:18px 0;min-height:90px;border:1px dashed var(--ln);border-radius:8px;display:flex;align-items:center;justify-content:center;color:var(--mu);font-size:.75rem}
footer{margin-top:24px;font-size:.8rem;color:var(--mu)}footer a{color:var(--ac)}"""

def page(title, body, depth=0, desc=""):
    pre = "../" * depth
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc or TAGLINE)}">
<link rel="stylesheet" href="{pre}style.css"></head><body><div class="wrap">
<header><h1><a href="{pre}index.html">{SITE}</a></h1><p class="tag">{TAGLINE}</p>
<nav class="links"><a href="{pre}index.html">新着一覧</a><a href="{pre}about.html">このサイトについて・免責</a></nav></header>
{body}
<footer><p>{DISC}</p><p><a href="{pre}about.html">このサイトについて</a></p></footer></div></body></html>"""

def post(p):
    st = "".join(f"<div><dt>{k}</dt><dd>{html.escape(v)}</dd></div>" for k, v in
                 [("株価", f"{p['price']}({p['asOf']})"), ("最低購入代金", p["minBuy"]), ("PER", p["per"]), ("PBR", p["pbr"]), ("配当利回り", p["yield"])])
    secs = ""
    for i, s in enumerate(p["sections"]):
        secs += f"<h3>{html.escape(s['title'])}</h3>{s['html']}"
        if i == 0: secs += AD_SLOT
    src = "".join(f'<li><a href="{html.escape(x["url"])}" rel="noopener">{html.escape(x["title"])}</a></li>' for x in p["sources"])
    body = (f'<article><div class="note">{p["date"]} ／ 証券コード {html.escape(p["code"])}</div><h2>{html.escape(p["name"])}</h2>'
            f'<p class="theme">{html.escape(p["theme"])}</p><dl class="stats">{st}</dl><p class="concl">{p["conclusion"]}</p>{secs}'
            f'{AD_SLOT}<h3>参考にした資料</h3><ul class="src">{src}</ul><p class="disc">{DISC}</p></article>')
    return page(f"{p['name']}({p['code']}) | {SITE}", body, 1, p["theme"])

def main():
    src = os.path.join(ROOT, "data", "picks.json")
    picks = json.load(open(src, encoding="utf8"))
    # 公開前の安全確認: 専門家名(U+7AAA U+7530)が混ざっていたら中止する
    assert "\u7aaa\u7530" not in json.dumps(picks, ensure_ascii=False), "非公開の評価内容が混ざっています"
    os.makedirs(os.path.join(OUT, "posts"), exist_ok=True)
    for f in os.listdir(os.path.join(OUT, "posts")): os.remove(os.path.join(OUT, "posts", f))
    rows = ""
    for p in picks:
        open(os.path.join(OUT, "posts", p["id"] + ".html"), "w", encoding="utf8").write(post(p))
        rows += f'<a href="posts/{p["id"]}.html"><span class="d">{p["date"]}</span><span><b>{html.escape(p["name"])}</b>({html.escape(p["code"])})</span><span class="t">{html.escape(p["theme"])}</span></a>'
    idx = f'<p class="note">全{len(picks)}件。新しい順です。</p><nav class="list">{rows}</nav>{AD_SLOT}'
    open(os.path.join(OUT, "index.html"), "w", encoding="utf8").write(page(SITE, idx))
    about = (f"<article><h2>このサイトについて</h2><p>今は目立たないが、今後重要性が増しそうな日本の上場企業を、事業内容を中心にまとめた個人の調査メモです。"
             f"株価指標や用語の簡単な解説もつけています。</p><h3>免責事項</h3><p>{DISC}</p>"
             f"<p>情報の出典は各記事の末尾に記載しています。確認できなかった項目は「未確認」と書き、推測では埋めないようにしています。</p>"
             f"<h3>広告について</h3><p>当サイトは広告を掲載することがあります。広告の内容と記事の評価は無関係です。</p></article>")
    open(os.path.join(OUT, "about.html"), "w", encoding="utf8").write(page("このサイトについて | " + SITE, about))
    open(os.path.join(OUT, "style.css"), "w", encoding="utf8").write(CSS)
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    print("built", len(picks), "posts")

if __name__ == "__main__":
    main()
