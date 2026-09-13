# -*- coding: utf-8 -*-
import html
from data import SESSION, CATEGORIES
import astro

def esc(s):
    return html.escape(str(s), quote=True)

ASTRO_LABELS = {
    "best": ("◎ 강력 추천", "astro-best", "촬영 강력 추천"),
    "ok":   ("○ 촬영 가능", "astro-ok", "촬영 가능"),
    "hard": ("△ 상급자용", "astro-hard", "상급자용"),
    "visual": ("— 안시 위주", "astro-visual", "안시 위주"),
}

KIND_ORDER = ["행성·달", "은하", "산광성운", "행성상성운", "산개성단", "구상성단", "이중성·변광성", "애스터리즘"]

def classify_kind(item, cat_id):
    c = item["cat"]
    if cat_id == "solar":
        return "행성·달"
    if "은하" in c:
        return "은하"
    if "산광성운" in c:
        return "산광성운"
    if "행성상성운" in c:
        return "행성상성운"
    if "구상성단" in c:
        return "구상성단"
    if "애스터리즘" in c:
        return "애스터리즘"
    if "이중성" in c or "다중성" in c or "변광성" in c:
        return "이중성·변광성"
    if "산개성단" in c or "항성운" in c:
        return "산개성단"
    return "기타"


def compute_tonight_window(item):
    win = item.get("win")
    if win is not None:
        start_h, end_h = win
        if start_h <= 1e-6 and end_h >= astro.SESSION_HOURS - 1e-6:
            return "20:00~06:00 밤새 관측 가능", end_h
        if start_h <= 1e-6:
            return f"20:00~{astro.clock_str(end_h)} 관측 가능", end_h
        if end_h >= astro.SESSION_HOURS - 1e-6:
            return f"{astro.clock_str(start_h)}부터 새벽까지 관측 가능", end_h
        return f"{astro.clock_str(start_h)}~{astro.clock_str(end_h)} 관측 가능", end_h

    ra = item.get("ra")
    dec = item.get("dec")
    if ra == "ALDEBARAN_PROXY":
        ra, dec = astro.ALDEBARAN_RA, astro.ALDEBARAN_DEC
    if ra is None or dec is None:
        return "정보 없음", 5.0
    return astro.observing_window_for(ra, dec)


def stars_html(n):
    return "".join('<span class="star on">★</span>' if i < n else '<span class="star">★</span>' for i in range(5))


def render_card(item, cat_id, idx):
    tag = item.get("flag")
    flag_html = f'<div class="flag">⚠ {esc(tag)}</div>' if tag else ""
    sep_row = ""
    if item.get("sep"):
        sep_row = f'''
            <div class="stat">
              <span class="stat-label">각거리</span>
              <span class="stat-value">{esc(item["sep"])}</span>
            </div>'''
    astro_key = item.get("astro", "ok")
    astro_label, astro_class, astro_short = ASTRO_LABELS[astro_key]
    astro_note = item.get("astro_note", "")
    visual = item.get("visual", 3)
    kind = classify_kind(item, cat_id)
    win_text, win_key = compute_tonight_window(item)
    mag_num = item.get("mag_num", 99)

    data_name = f"{item['name_kr']} {item['name_en']}".lower()

    return f'''
        <article class="card" data-name="{esc(data_name)}" data-cat="{esc(cat_id)}"
                 data-visual="{visual}" data-astro="{esc(astro_key)}" data-kind="{esc(kind)}"
                 data-urgency="{win_key:.2f}" data-mag="{mag_num}">
          <div class="card-top">
            <div class="card-heading">
              <h3>{esc(item['name_kr'])}</h3>
              <p class="card-en">{esc(item['name_en'])}</p>
            </div>
            <span class="badge {astro_class}" title="{esc(astro_note)}">{astro_label}</span>
          </div>
          <div class="chiprow">
            <span class="chip chip-type">{esc(item['cat'])}</span>
            <span class="chip chip-const">{esc(item['const'])}</span>
          </div>
          <div class="visual-row" title="안시관측 추천도 {visual}/5">
            <span class="visual-label">안시 추천도</span>
            <span class="stars">{stars_html(visual)}</span>
          </div>
          {flag_html}
          <div class="window-row">
            <span class="window-icon">🕐</span>
            <span class="window-text">오늘 밤: {esc(win_text)}</span>
          </div>
          <div class="stats">
            <div class="stat">
              <span class="stat-label">밝기(등급)</span>
              <span class="stat-value">{esc(item['mag'])}</span>
            </div>
            <div class="stat">
              <span class="stat-label">겉보기 크기</span>
              <span class="stat-value">{esc(item['size'])}</span>
            </div>{sep_row}
            <div class="stat">
              <span class="stat-label">거리</span>
              <span class="stat-value">{esc(item['dist'])}</span>
            </div>
            <div class="stat stat-wide">
              <span class="stat-label">적정 관측 시기(일반)</span>
              <span class="stat-value">{esc(item['season'])}</span>
            </div>
          </div>
          <p class="note">{esc(item['note'])}</p>
          <p class="astro-note"><strong>촬영 팁:</strong> {esc(astro_note)}</p>
          <a class="photolink" href="{esc(item['link'])}" target="_blank" rel="noopener">사진·상세정보 보기 (Wikipedia) ↗</a>
        </article>'''

def render_category(cat):
    items_html = "\n".join(render_card(it, cat["id"], i) for i, it in enumerate(cat["items"]))
    return f'''
      <section class="category" id="{esc(cat['id'])}" data-section="1">
        <div class="cat-head">
          <span class="cat-emoji">{cat['emoji']}</span>
          <div>
            <h2>{esc(cat['title'])}</h2>
            <p class="cat-desc">{esc(cat['desc'])}</p>
          </div>
          <span class="cat-count">{len(cat['items'])}개 대상</span>
        </div>
        <div class="grid">
          {items_html}
        </div>
      </section>'''

nav_chips = "\n".join(
    f'<a href="#{esc(c["id"])}" class="navchip">{c["emoji"]} {esc(c["title"].split(" —")[0].split(" (")[0])}</a>'
    for c in CATEGORIES
)

sections_html = "\n".join(render_category(c) for c in CATEGORIES)

kind_options = "\n".join(f'<option value="{esc(k)}">{esc(k)}</option>' for k in KIND_ORDER)

total_objects = sum(len(c["items"]) for c in CATEGORIES)

HTML = f'''<title>파주 관측 노트</title>
<meta name="description" content="2026년 9월 19일 파주 안시관측 세션을 위한 대상별 정리 자료 (사진 링크·등급·크기·적정시기·촬영추천·안시추천도 필터/정렬)">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,700;1,9..144,500&family=IBM+Plex+Sans+KR:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{{
    --bg: #0c1120;
    --bg-2: #10182c;
    --surface: #141d33;
    --surface-2: #1a2540;
    --border: #2a3757;
    --border-soft: #202c4a;
    --text: #e9edf7;
    --text-dim: #aab4d1;
    --text-faint: #7684a8;
    --accent: #e7b768;
    --accent-2: #f0cf94;
    --violet: #b7a2e8;
    --teal: #7fd8c8;
    --rose: #e79bb0;
    --blue: #8ab4e8;
    --danger: #e88a6f;
    --best: #7fd8a0;
    --ok: #8ab4e8;
    --hard: #e79bb0;
    --visual: #cbb4e8;
    --star-on: #e7b768;
    --star-off: #3a4568;
    --shadow: 0 12px 30px -12px rgba(0,0,0,0.55);
    --font-display: "Fraunces", "Noto Serif KR", serif;
    --font-body: "IBM Plex Sans KR", "Pretendard", -apple-system, sans-serif;
    --font-mono: "IBM Plex Mono", ui-monospace, monospace;
    color-scheme: dark;
  }}

  :root[data-theme="light"]{{
    --bg:#f6f4ee;
    --bg-2:#efece2;
    --surface:#ffffff;
    --surface-2:#f2f0e6;
    --border:#ddd7c4;
    --border-soft:#e6e1d2;
    --text:#211d15;
    --text-dim:#5b5643;
    --text-faint:#8b8567;
    --accent:#a9761f;
    --accent-2:#c78f2f;
    --star-off: #ddd5bd;
    --shadow: 0 10px 26px -14px rgba(60,50,20,0.28);
    color-scheme: light;
  }}

  /* red-light (night vision) mode: overrides everything to shades of red */
  :root[data-redlight="on"]{{
    --bg:#0a0000;
    --bg-2:#120202;
    --surface:#170303;
    --surface-2:#1d0404;
    --border:#4a0d0d;
    --border-soft:#330909;
    --text:#ff6a5a;
    --text-dim:#c94b3f;
    --text-faint:#8a332b;
    --accent:#ff8a6a;
    --accent-2:#ff9d80;
    --violet:#ff6a5a; --teal:#ff6a5a; --rose:#ff6a5a; --blue:#ff6a5a;
    --best:#ff8a6a; --ok:#ff8a6a; --hard:#ff8a6a; --visual:#ff8a6a;
    --star-on:#ff8a6a; --star-off:#3a1210;
    --shadow: none;
    color-scheme: dark;
  }}
  :root[data-redlight="on"] img,
  :root[data-redlight="on"] .cat-emoji {{ filter: grayscale(1) sepia(1) hue-rotate(-40deg) saturate(4); }}

  *{{ box-sizing: border-box; }}
  body{{
    margin:0;
    background:
      radial-gradient(ellipse 80% 50% at 20% -10%, rgba(231,183,104,0.08), transparent 60%),
      radial-gradient(ellipse 60% 40% at 90% 10%, rgba(138,180,232,0.07), transparent 55%),
      var(--bg);
    color: var(--text);
    font-family: var(--font-body);
    line-height:1.6;
    padding: 0 0 80px;
    transition: background-color .2s ease, color .2s ease;
  }}
  a {{ color: var(--accent); }}
  h1,h2,h3{{ font-family: var(--font-display); font-weight:700; text-wrap: balance; margin:0; }}

  .wrap{{ max-width: 1180px; margin: 0 auto; padding: 0 20px; }}

  /* ---------- controls (theme / redlight) ---------- */
  .controls{{
    position: sticky; top:0; z-index: 40;
    display:flex; justify-content:flex-end; gap:8px;
    padding: 10px 20px;
    background: linear-gradient(to bottom, var(--bg) 70%, transparent);
    backdrop-filter: blur(6px);
  }}
  .ctl-btn{{
    font-family: var(--font-body); font-size:12.5px; font-weight:600;
    background: var(--surface); color: var(--text-dim);
    border:1px solid var(--border); border-radius:999px;
    padding:7px 14px; cursor:pointer; display:flex; align-items:center; gap:6px;
  }}
  .ctl-btn:hover{{ color:var(--text); border-color: var(--accent); }}
  .ctl-btn[aria-pressed="true"]{{ background: var(--accent); color:#1a1204; border-color: var(--accent); }}

  /* ---------- hero ---------- */
  .hero{{ padding: 8px 20px 30px; }}
  .hero-inner{{
    max-width:1180px; margin:0 auto;
    border:1px solid var(--border-soft); border-radius:20px;
    background: linear-gradient(160deg, var(--surface), var(--bg-2));
    padding: 34px clamp(20px,4vw,48px);
    box-shadow: var(--shadow);
    position: relative; overflow:hidden;
  }}
  .hero-eyebrow{{
    font-family: var(--font-mono); font-size:12px; letter-spacing:.14em; text-transform:uppercase;
    color: var(--accent); margin:0 0 10px;
  }}
  .hero h1{{ font-size: clamp(28px,4.4vw,42px); margin-bottom:8px; }}
  .hero-sub{{ color: var(--text-dim); font-size:15.5px; max-width: 62ch; margin:0 0 24px; }}
  .hero-stats{{
    display:grid; grid-template-columns: repeat(auto-fit,minmax(150px,1fr));
    gap:1px; background: var(--border-soft); border:1px solid var(--border-soft);
    border-radius:14px; overflow:hidden;
  }}
  .hero-stat{{ background: var(--surface); padding:14px 16px; }}
  .hero-stat .k{{ font-size:11.5px; color:var(--text-faint); text-transform:uppercase; letter-spacing:.08em; margin-bottom:5px;}}
  .hero-stat .v{{ font-family: var(--font-mono); font-size:15px; color:var(--text); font-variant-numeric: tabular-nums; }}
  .hero-note{{ margin-top:18px; font-size:13.5px; color:var(--text-dim); border-left:3px solid var(--accent); padding-left:12px; }}

  /* ---------- nav ---------- */
  .navbar{{
    position: sticky; top:44px; z-index:30;
    background: var(--bg); border-bottom:1px solid var(--border-soft);
    padding: 10px 20px;
  }}
  .navbar-inner{{ max-width:1180px; margin:0 auto; display:flex; gap:8px; flex-wrap:wrap; align-items:center; }}
  .navchip{{
    font-size:13px; font-weight:600; color:var(--text-dim); text-decoration:none;
    background: var(--surface); border:1px solid var(--border-soft); border-radius:999px;
    padding:6px 12px; white-space:nowrap;
  }}
  .navchip:hover{{ color:var(--text); border-color:var(--accent); }}
  .search{{
    flex: 0 1 200px;
    font-family:var(--font-body); font-size:13.5px;
    background: var(--surface); border:1px solid var(--border-soft); color:var(--text);
    border-radius:999px; padding:7px 14px;
  }}
  .search::placeholder{{ color: var(--text-faint); }}

  /* ---------- filter bar ---------- */
  .filterbar{{
    max-width:1180px; margin: 14px auto 0; padding: 16px 20px;
    display:flex; flex-direction:column; gap:14px;
  }}
  .filter-panel{{
    background: var(--surface); border:1px solid var(--border-soft); border-radius:14px;
    padding: 16px 18px; display:flex; flex-direction:column; gap:14px;
  }}
  .filter-row{{ display:flex; flex-wrap:wrap; gap:18px 26px; align-items:flex-end; }}
  .filter-group{{ display:flex; flex-direction:column; gap:6px; min-width:180px; }}
  .filter-group label.fg-label{{ font-size:11px; text-transform:uppercase; letter-spacing:.07em; color:var(--text-faint); }}
  .filter-group select{{
    font-family: var(--font-body); font-size:13.5px; color:var(--text);
    background: var(--surface-2); border:1px solid var(--border-soft); border-radius:8px;
    padding:7px 10px;
  }}
  .visual-slider-row{{ display:flex; align-items:center; gap:10px; }}
  .visual-slider-row input[type=range]{{ width:140px; accent-color: var(--accent); }}
  .visual-slider-val{{ font-family: var(--font-mono); font-size:13px; color:var(--accent); min-width:70px; }}
  .astro-toggles{{ display:flex; gap:8px; flex-wrap:wrap; }}
  .astro-toggle{{
    font-size:12px; font-weight:600; font-family:var(--font-mono);
    padding:6px 11px; border-radius:999px; cursor:pointer; user-select:none;
    border:1px solid currentColor; background:transparent; opacity:0.35;
  }}
  .astro-toggle.on{{ opacity:1; }}
  .astro-toggle.astro-best{{ color: var(--best); }}
  .astro-toggle.astro-ok{{ color: var(--ok); }}
  .astro-toggle.astro-hard{{ color: var(--hard); }}
  .astro-toggle.astro-visual{{ color: var(--visual); }}
  .filter-actions{{ display:flex; gap:10px; align-items:center; margin-left:auto; }}
  .reset-btn{{
    font-size:12.5px; font-weight:600; color: var(--text-dim); background:none;
    border:1px solid var(--border-soft); border-radius:999px; padding:7px 14px; cursor:pointer;
  }}
  .reset-btn:hover{{ color:var(--text); border-color:var(--accent); }}
  .result-count{{ font-family: var(--font-mono); font-size:12.5px; color:var(--text-faint); }}
  .result-count b{{ color: var(--accent); }}

  /* ---------- legend ---------- */
  .legend{{
    max-width:1180px; margin: 0 auto; padding: 0 20px;
    display:flex; flex-wrap:wrap; gap: 10px 22px; font-size:12.5px; color:var(--text-dim);
  }}
  .legend b{{ color:var(--text); }}
  .legend .dot{{ display:inline-block; width:8px;height:8px;border-radius:50%; margin-right:6px; }}

  /* ---------- category ---------- */
  .category{{ max-width:1180px; margin: 46px auto 0; padding:0 20px; scroll-margin-top: 100px; }}
  .cat-head{{ display:flex; align-items:flex-start; gap:14px; margin-bottom:18px; flex-wrap:wrap; }}
  .cat-emoji{{ font-size:30px; line-height:1; }}
  .cat-head h2{{ font-size: clamp(20px,2.6vw,26px); }}
  .cat-desc{{ margin:4px 0 0; color:var(--text-dim); font-size:13.5px; max-width:70ch; }}
  .cat-count{{ margin-left:auto; font-family:var(--font-mono); font-size:12px; color:var(--text-faint); align-self:center; }}

  .grid{{ display:grid; grid-template-columns: repeat(auto-fill,minmax(300px,1fr)); gap:16px; }}
  #resultsWrap{{ max-width:1180px; margin: 26px auto 0; padding: 0 20px; }}
  #resultsHead{{ display:flex; align-items:baseline; gap:12px; margin-bottom:16px; flex-wrap:wrap; }}
  #resultsHead h2{{ font-size:20px; }}
  .empty-state{{ padding: 40px 0; text-align:center; color:var(--text-faint); font-size:14px; }}

  .card{{
    background: var(--surface); border:1px solid var(--border-soft); border-radius:14px;
    padding:18px; display:flex; flex-direction:column; gap:10px;
  }}
  .card-top{{ display:flex; justify-content:space-between; align-items:flex-start; gap:10px; }}
  .card-heading h3{{ font-size:18px; margin-bottom:2px; }}
  .card-en{{ margin:0; font-family:var(--font-mono); font-size:11.5px; color:var(--text-faint); }}

  .badge{{
    flex-shrink:0; font-size:11px; font-weight:600; font-family:var(--font-mono);
    padding:4px 9px; border-radius:999px; white-space:nowrap; cursor:help;
    border:1px solid currentColor;
  }}
  .astro-best{{ color: var(--best); }}
  .astro-ok{{ color: var(--ok); }}
  .astro-hard{{ color: var(--hard); }}
  .astro-visual{{ color: var(--visual); }}

  .chiprow{{ display:flex; gap:6px; flex-wrap:wrap; }}
  .chip{{
    font-size:11.5px; padding:3px 9px; border-radius:6px;
    background: var(--surface-2); color:var(--text-dim); border:1px solid var(--border-soft);
  }}

  .visual-row{{ display:flex; align-items:center; gap:8px; }}
  .visual-label{{ font-size:10.5px; text-transform:uppercase; letter-spacing:.06em; color:var(--text-faint); }}
  .stars{{ font-size:14px; letter-spacing:1px; }}
  .star{{ color: var(--star-off); }}
  .star.on{{ color: var(--star-on); }}

  .flag{{
    font-size:12px; color: var(--danger); background: color-mix(in srgb, var(--danger) 12%, transparent);
    border:1px solid color-mix(in srgb, var(--danger) 35%, transparent);
    border-radius:8px; padding:5px 9px;
  }}

  .window-row{{
    display:flex; align-items:center; gap:7px; font-size:12.5px; font-weight:600;
    background: var(--surface-2); border:1px solid var(--border-soft); border-radius:8px;
    padding:6px 10px; color: var(--accent);
  }}
  .window-icon{{ font-size:13px; }}

  .stats{{
    display:grid; grid-template-columns: 1fr 1fr; gap:8px 14px;
    border-top:1px dashed var(--border-soft); border-bottom:1px dashed var(--border-soft);
    padding: 10px 0;
  }}
  .stat{{ display:flex; flex-direction:column; gap:2px; }}
  .stat-wide{{ grid-column: 1 / -1; }}
  .stat-label{{ font-size:10.5px; text-transform:uppercase; letter-spacing:.06em; color:var(--text-faint); }}
  .stat-value{{ font-size:13.5px; color:var(--text); font-family: var(--font-mono); }}

  .note{{ margin:0; font-size:13.5px; color:var(--text-dim); }}
  .astro-note{{ margin:0; font-size:12.5px; color:var(--text-faint); }}
  .astro-note strong{{ color:var(--text-dim); }}

  .photolink{{
    margin-top:auto; align-self:flex-start; font-size:12.5px; font-weight:600;
    text-decoration:none; border-bottom:1px solid currentColor; padding-bottom:1px;
  }}

  footer{{ max-width:1180px; margin: 60px auto 0; padding: 24px 20px 0; color:var(--text-faint); font-size:12.5px; border-top:1px solid var(--border-soft); }}

  @media (max-width: 640px){{
    .navbar{{ top:0; }}
    .hero-stats{{ grid-template-columns: repeat(2,1fr); }}
    .search{{ flex-basis: 100%; order: 10; }}
    .filter-row{{ gap:14px 20px; }}
    .filter-actions{{ margin-left:0; width:100%; justify-content:space-between; }}
  }}
</style>

<div class="controls">
  <button class="ctl-btn" id="themeBtn" type="button" aria-pressed="false">🌗 밝은 화면</button>
  <button class="ctl-btn" id="redBtn" type="button" aria-pressed="false">🔴 야간 적색 모드</button>
</div>

<div class="hero">
  <div class="hero-inner">
    <p class="hero-eyebrow">Visual Observation Log · 안시관측 준비자료</p>
    <h1>파주 관측 노트 — 2026.09.19</h1>
    <p class="hero-sub">총 {total_objects}개 대상(태양계 6 + 딥스카이 {total_objects-6})의 사진 링크, 밝기 등급, 겉보기 크기, 안시관측 추천도(1~5★), 오늘 밤 실제 관측 가능 시간대, 촬영 추천 여부를 정리했습니다. 아래 필터·정렬로 원하는 대상만 골라보세요.</p>
    <div class="hero-stats">
      <div class="hero-stat"><div class="k">관측일</div><div class="v">{esc(SESSION['date'])}</div></div>
      <div class="hero-stat"><div class="k">장소</div><div class="v">{esc(SESSION['place'])}</div></div>
      <div class="hero-stat"><div class="k">일몰</div><div class="v">{esc(SESSION['sunset'])}</div></div>
      <div class="hero-stat"><div class="k">천문박명(밤 시작)</div><div class="v">{esc(SESSION['astro_dusk'])}</div></div>
      <div class="hero-stat"><div class="k">천문박명(밤 종료)</div><div class="v">{esc(SESSION['astro_dawn'])}</div></div>
      <div class="hero-stat"><div class="k">일출</div><div class="v">{esc(SESSION['sunrise'])}</div></div>
      <div class="hero-stat"><div class="k">달 위상</div><div class="v">{esc(SESSION['moon_phase'])}</div></div>
      <div class="hero-stat"><div class="k">월출 / 월몰</div><div class="v">{esc(SESSION['moonrise'])} / {esc(SESSION['moonset'])}</div></div>
    </div>
    <p class="hero-note">💡 <strong>운용 팁</strong> — "오늘 밤 관측 가능 시간대"는 파주(위도 약 37.8°N) 기준, 고도 20° 이상을 "쓸만한 고도"로 잡아 실제로 계산한 값입니다. 정렬을 <strong>"곧 지는 순"</strong>으로 바꾸면 지금 당장 우선 봐야 할 대상이 위로 올라옵니다. 일몰·박명·행성 시각은 근사치이니 실제 관측 며칠 전 다시 확인하세요.</p>
  </div>
</div>

<nav class="navbar">
  <div class="navbar-inner">
    {nav_chips}
    <input class="search" id="searchBox" type="text" placeholder="대상 이름으로 검색…" />
  </div>
</nav>

<div class="filterbar">
  <div class="filter-panel">
    <div class="filter-row">
      <div class="filter-group">
        <label class="fg-label" for="sortSelect">정렬 기준</label>
        <select id="sortSelect">
          <option value="default">기본 (카테고리순)</option>
          <option value="urgency">🕐 곧 지는 순 (오늘 밤 먼저 볼 것)</option>
          <option value="visual-desc">⭐ 안시 추천도 높은 순</option>
          <option value="mag-asc">✨ 밝은 순 (등급 낮은 순)</option>
          <option value="name">가나다순</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="fg-label" for="kindSelect">유형</label>
        <select id="kindSelect">
          <option value="all">전체 유형</option>
          {kind_options}
        </select>
      </div>
      <div class="filter-group">
        <label class="fg-label" for="visualSlider">안시관측 추천도 (최소)</label>
        <div class="visual-slider-row">
          <input type="range" id="visualSlider" min="1" max="5" step="1" value="1" />
          <span class="visual-slider-val" id="visualSliderVal">★1 이상 (전체)</span>
        </div>
      </div>
      <div class="filter-group">
        <label class="fg-label">촬영 추천도</label>
        <div class="astro-toggles" id="astroToggles">
          <button type="button" class="astro-toggle astro-best on" data-astro="best">◎ 강력추천</button>
          <button type="button" class="astro-toggle astro-ok on" data-astro="ok">○ 촬영가능</button>
          <button type="button" class="astro-toggle astro-hard on" data-astro="hard">△ 상급자용</button>
          <button type="button" class="astro-toggle astro-visual on" data-astro="visual">— 안시위주</button>
        </div>
      </div>
      <div class="filter-actions">
        <span class="result-count" id="resultCount"></span>
        <button type="button" class="reset-btn" id="resetBtn">↺ 필터 초기화</button>
      </div>
    </div>
  </div>
  <div class="legend">
    <span><span class="dot" style="background:var(--best)"></span><b>◎ 강력 추천</b> 촬영하기 좋은 대상</span>
    <span><span class="dot" style="background:var(--ok)"></span><b>○ 촬영 가능</b> 장비·기법이 더 필요</span>
    <span><span class="dot" style="background:var(--hard)"></span><b>△ 상급자용</b> 크고 어두운 하늘·장초점 필요</span>
    <span><span class="dot" style="background:var(--visual)"></span><b>— 안시 위주</b> 눈으로 색·분리 감상</span>
    <span>⭐ <b>안시 추천도</b>는 밝기+크기(표면밝기)+형태를 종합해 "맨눈/소형망원경으로 보기 좋은 정도"를 1~5로 평가한 값 (5=매우 쉬움, 1=암소하늘+대구경 필요)</span>
  </div>
</div>

<div id="resultsWrap" hidden>
  <div id="resultsHead">
    <h2 id="resultsTitle">검색 결과</h2>
    <span class="result-count" id="resultsHeadCount"></span>
  </div>
  <div class="grid" id="resultsGrid"></div>
  <p class="empty-state" id="emptyState" hidden>조건에 맞는 대상이 없습니다. 필터를 조정해보세요.</p>
</div>

{sections_html}

<footer>
  <p>자료 출처: Wikipedia(각 대상 문서), TheSkyLive, timeanddate.com, astronomy.com, telescopeadvisor.com 등 (2026년 9월 기준 검색). "오늘 밤 관측 가능 시간대"는 각 대상의 J2000 좌표로 파주 상공 고도를 직접 계산한 근사치이며, 태양계 천체(달·행성)는 검색된 출몰 시각을 바탕으로 한 근사치입니다. 실제 관측 전 최신 자료로 재확인하세요.</p>
</footer>

<script>
(function(){{
  var root = document.documentElement;
  function safeGet(k){{ try {{ return localStorage.getItem(k); }} catch(e) {{ return null; }} }}
  function safeSet(k,v){{ try {{ localStorage.setItem(k,v); }} catch(e) {{}} }}

  /* ---------- theme / redlight ---------- */
  var themeBtn = document.getElementById('themeBtn');
  var redBtn = document.getElementById('redBtn');

  var savedTheme = safeGet('obs-theme');
  if (savedTheme === 'light') {{ root.setAttribute('data-theme','light'); themeBtn.setAttribute('aria-pressed','true'); themeBtn.textContent = '🌙 어두운 화면'; }}
  var savedRed = safeGet('obs-redlight');
  if (savedRed === 'on') {{ root.setAttribute('data-redlight','on'); redBtn.setAttribute('aria-pressed','true'); }}

  themeBtn.addEventListener('click', function(){{
    var isLight = root.getAttribute('data-theme') === 'light';
    if (isLight) {{ root.removeAttribute('data-theme'); themeBtn.setAttribute('aria-pressed','false'); themeBtn.textContent = '🌗 밝은 화면'; safeSet('obs-theme','dark'); }}
    else {{ root.setAttribute('data-theme','light'); themeBtn.setAttribute('aria-pressed','true'); themeBtn.textContent = '🌙 어두운 화면'; safeSet('obs-theme','light'); }}
  }});

  redBtn.addEventListener('click', function(){{
    var isOn = root.getAttribute('data-redlight') === 'on';
    if (isOn) {{ root.removeAttribute('data-redlight'); redBtn.setAttribute('aria-pressed','false'); safeSet('obs-redlight','off'); }}
    else {{ root.setAttribute('data-redlight','on'); redBtn.setAttribute('aria-pressed','true'); safeSet('obs-redlight','on'); }}
  }});

  /* ---------- gather item data ---------- */
  var cardEls = Array.prototype.slice.call(document.querySelectorAll('.category .card'));
  var items = cardEls.map(function(el){{
    return {{
      el: el,
      name: el.getAttribute('data-name') || '',
      visual: parseInt(el.getAttribute('data-visual'), 10) || 1,
      astro: el.getAttribute('data-astro') || 'ok',
      kind: el.getAttribute('data-kind') || '기타',
      urgency: parseFloat(el.getAttribute('data-urgency')) || 99,
      mag: parseFloat(el.getAttribute('data-mag')),
      titleKr: el.querySelector('h3') ? el.querySelector('h3').textContent : ''
    }};
  }});

  var sections = Array.prototype.slice.call(document.querySelectorAll('.category'));
  var resultsWrap = document.getElementById('resultsWrap');
  var resultsGrid = document.getElementById('resultsGrid');
  var resultsHeadCount = document.getElementById('resultsHeadCount');
  var resultsTitle = document.getElementById('resultsTitle');
  var emptyState = document.getElementById('emptyState');
  var resultCount = document.getElementById('resultCount');

  var searchBox = document.getElementById('searchBox');
  var sortSelect = document.getElementById('sortSelect');
  var kindSelect = document.getElementById('kindSelect');
  var visualSlider = document.getElementById('visualSlider');
  var visualSliderVal = document.getElementById('visualSliderVal');
  var astroToggles = Array.prototype.slice.call(document.querySelectorAll('.astro-toggle'));
  var resetBtn = document.getElementById('resetBtn');

  var state = {{ q: '', sort: 'default', kind: 'all', minVisual: 1, astro: {{best:true, ok:true, hard:true, visual:true}} }};

  function isDefaultState(){{
    return state.q === '' && state.sort === 'default' && state.kind === 'all' && state.minVisual === 1 &&
      state.astro.best && state.astro.ok && state.astro.hard && state.astro.visual;
  }}

  function sortLabel(mode){{
    return {{
      urgency: '곧 지는 순',
      'visual-desc': '안시 추천도 높은 순',
      'mag-asc': '밝은 순',
      name: '가나다순',
      default: '기본'
    }}[mode] || mode;
  }}

  function render(){{
    var def = isDefaultState();
    resetBtn.style.visibility = def ? 'hidden' : 'visible';

    if (def) {{
      resultsWrap.hidden = true;
      sections.forEach(function(s){{ s.hidden = false; }});
      resultCount.textContent = '';
      return;
    }}

    sections.forEach(function(s){{ s.hidden = true; }});
    resultsWrap.hidden = false;

    var q = state.q.toLowerCase();
    var filtered = items.filter(function(it){{
      if (q && it.name.indexOf(q) === -1) return false;
      if (state.kind !== 'all' && it.kind !== state.kind) return false;
      if (it.visual < state.minVisual) return false;
      if (!state.astro[it.astro]) return false;
      return true;
    }});

    filtered.sort(function(a,b){{
      switch(state.sort){{
        case 'urgency': return a.urgency - b.urgency;
        case 'visual-desc': return b.visual - a.visual || a.urgency - b.urgency;
        case 'mag-asc': return a.mag - b.mag;
        case 'name': return a.titleKr.localeCompare(b.titleKr, 'ko');
        default: return 0;
      }}
    }});

    resultsGrid.innerHTML = '';
    filtered.forEach(function(it){{ resultsGrid.appendChild(it.el.cloneNode(true)); }});

    resultsTitle.textContent = (state.sort === 'default') ? '검색 결과' : sortLabel(state.sort);
    var countText = filtered.length + ' / ' + items.length + '개 대상';
    resultsHeadCount.textContent = countText;
    resultCount.innerHTML = '<b>' + filtered.length + '</b> / ' + items.length + '개 표시 중';
    emptyState.hidden = filtered.length !== 0;
  }}

  searchBox.addEventListener('input', function(){{ state.q = searchBox.value.trim(); render(); }});
  sortSelect.addEventListener('change', function(){{ state.sort = sortSelect.value; render(); }});
  kindSelect.addEventListener('change', function(){{ state.kind = kindSelect.value; render(); }});
  visualSlider.addEventListener('input', function(){{
    state.minVisual = parseInt(visualSlider.value, 10);
    visualSliderVal.textContent = (state.minVisual === 1) ? '★1 이상 (전체)' : ('★' + state.minVisual + ' 이상');
    render();
  }});
  astroToggles.forEach(function(btn){{
    btn.addEventListener('click', function(){{
      var key = btn.getAttribute('data-astro');
      state.astro[key] = !state.astro[key];
      btn.classList.toggle('on', state.astro[key]);
      render();
    }});
  }});
  resetBtn.addEventListener('click', function(){{
    state = {{ q: '', sort: 'default', kind: 'all', minVisual: 1, astro: {{best:true, ok:true, hard:true, visual:true}} }};
    searchBox.value = '';
    sortSelect.value = 'default';
    kindSelect.value = 'all';
    visualSlider.value = 1;
    visualSliderVal.textContent = '★1 이상 (전체)';
    astroToggles.forEach(function(btn){{ btn.classList.add('on'); }});
    render();
  }});

  render();
}})();
</script>
'''

with open("output.html", "w", encoding="utf-8") as f:
    f.write(HTML)

print("Wrote output.html,", total_objects, "objects,", len(CATEGORIES), "categories")
