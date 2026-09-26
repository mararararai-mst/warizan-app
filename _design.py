# -*- coding: utf-8 -*-
"""わり算アプリ デザイン引き継ぎ書との突き合わせ（機械で測る分だけ）

  python _design.py

  shared/design/デザイン引き継ぎ書.md の 2-1／2-2／2-4 と 第4層、
  education/_lib/教材アプリのチェック基準.md の §8-3／§10-2 のうち、
  数字で出せるものを全状態で測る。目で見る分はここには入らない。
"""
import sys, os, json, threading, functools, http.server, socketserver
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); APP = os.path.basename(HERE)
PORT = 8819
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
class Srv(socketserver.TCPServer): allow_reuse_address = True
srv = Srv(("127.0.0.1", PORT), functools.partial(Quiet, directory=ROOT)); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{PORT}/{APP}/index.html'

import re
src = open(os.path.join(HERE, '_trace.py'), encoding='utf-8').read()
m = re.search(r'STATES = \[(.*?)\n\]', src, re.S)
STATES = eval('[' + m.group(1) + '\n]')

# ---------------------------------------------------------------- 測るJS
FIG_JS = r"""
() => {
  const svg = document.getElementById('fig');
  const vb  = svg.viewBox.baseVal;
  const root = svg.getScreenCTM().inverse();
  let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9, n=0;
  const rad = [];
  svg.querySelectorAll('*').forEach(e=>{
    if(!e.getBBox || !(e instanceof SVGGraphicsElement)) return;
    if(e.tagName==='g'||e.tagName==='svg'||e.tagName==='defs') return;
    const cs = getComputedStyle(e);
    if(cs.display==='none'||cs.visibility==='hidden'||+cs.opacity===0) return;
    let b; try{ b=e.getBBox(); }catch(_){ return; }
    if(!b.width && !b.height) return;
    const m = root.multiply(e.getScreenCTM());
    const pts=[[b.x,b.y],[b.x+b.width,b.y],[b.x,b.y+b.height],[b.x+b.width,b.y+b.height]]
      .map(([px,py])=>{const p=svg.createSVGPoint();p.x=px;p.y=py;return p.matrixTransform(m);});
    const xs=pts.map(p=>p.x), ys=pts.map(p=>p.y);
    x0=Math.min(x0,...xs); x1=Math.max(x1,...xs); y0=Math.min(y0,...ys); y1=Math.max(y1,...ys); n++;
  });
  // クッキーの実寸（.ck の中の いちばん外の円）
  svg.querySelectorAll('.ck').forEach(g=>{
    const c = g.querySelector('circle');
    if(c) rad.push(+(c.getBoundingClientRect().width).toFixed(1));
  });
  if(!n) return null;
  return {n, x0,y0,x1,y1, vw:vb.width, vh:vb.height, rad:[...new Set(rad)].sort((a,b)=>a-b)};
}
"""

TEXT_JS = r"""
() => {
  const lum = c => { const f=v=>{v/=255; return v<=.04045? v/12.92 : Math.pow((v+.055)/1.055,2.4);};
                     return .2126*f(c[0])+.7152*f(c[1])+.0722*f(c[2]); };
  const num = s => (s.match(/[\d.]+/g)||[]).map(Number);
  const bgOf = el => { let e=el; while(e && e!==document.documentElement){
      const c=getComputedStyle(e).backgroundColor, v=num(c);
      if(v.length>=3 && (v.length<4 || v[3]>0.6)) return v; e=e.parentElement; }
      return [255,247,234]; };
  const out=[];
  document.querySelectorAll('*').forEach(el=>{
    if(el.closest('svg')) return;
    const t=[...el.childNodes].filter(n=>n.nodeType===3 && n.nodeValue.trim()).map(n=>n.nodeValue.trim()).join('');
    if(!t) return;
    const cs=getComputedStyle(el), r=el.getBoundingClientRect();
    if(!r.width || !r.height || cs.visibility==='hidden' || cs.display==='none') return;
    if(el.closest('[hidden]')) return;
    const fg=num(cs.color), bg=bgOf(el);
    const a=lum(fg)+.05, b=lum(bg)+.05;
    const ratio = +(Math.max(a,b)/Math.min(a,b)).toFixed(2);
    out.push({t:t.slice(0,18), px:+parseFloat(cs.fontSize).toFixed(1), ratio,
              sel: el.tagName.toLowerCase()+(el.className&&el.className.baseVal===undefined?'.'+String(el.className).trim().split(/\s+/).join('.'):'')});
  });
  return out;
}
"""

ANCHOR_JS = r"""
() => {
  const o={};
  ['#qcard','#status','#btnrow','#eq','#msg','#nextrow','.side','main'].forEach(s=>{
    const e=document.querySelector(s); if(!e) return;
    const r=e.getBoundingClientRect(); o[s]=Math.round(r.top);
  });
  return o;
}
"""

STATIC_JS = r"""
() => {
  const shadow=new Set(), dim=[], border=[];
  document.querySelectorAll('*').forEach(el=>{
    const cs=getComputedStyle(el), r=el.getBoundingClientRect();
    if(!r.width) return;
    const bs=cs.boxShadow;
    if(bs && bs!=='none'){ (bs.split(/,(?![^()]*\))/)).forEach(s=>{
      const n=(s.match(/-?[\d.]+px/g)||[]).map(parseFloat);
      if(n.length>=3 && n[2]>0) shadow.add(el.tagName.toLowerCase()+'.'+String(el.className||'').trim().split(/\s+/)[0]+' → '+s.trim());
    });}
    const op=+cs.opacity;
    if(op<1 && op>0.2 && (el.tagName==='BUTTON'||el.closest('button')===el) && !el.disabled)
      dim.push(el.tagName.toLowerCase()+'.'+String(el.className||'').trim().split(/\s+/).join('.')+' opacity='+op+' 「'+el.innerText.trim().slice(0,10)+'」');
    if(el.tagName==='BUTTON'||el.classList.contains('chip')){
      const bw=parseFloat(cs.borderTopWidth)||0;
      if(bw>0 && !el.classList.contains('on') && !el.classList.contains('hit'))
        border.push(el.tagName.toLowerCase()+'.'+String(el.className||'').trim().split(/\s+/).join('.')+' border='+bw+'px '+cs.borderTopColor);
    }
  });
  return {shadow:[...shadow], dim:[...new Set(dim)], border:[...new Set(border)]};
}
"""

def main():
    W, H = 1280, 800
    rows, texts, anchors, statics = [], {}, {}, None
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(viewport={'width': W, 'height': H}, device_scale_factor=1)
        pg = ctx.new_page(); pg.goto(URL); pg.wait_for_function("document.fonts.status==='loaded'", timeout=8000)
        for name, js in STATES:
            pg.evaluate("() => { window.__instant = true; " + js + "; }")
            f = pg.evaluate(FIG_JS)
            if f:
                cx = (f['x0'] + f['x1']) / 2; cy = (f['y0'] + f['y1']) / 2
                rows.append(dict(name=name,
                                 dx=round((cx - f['vw'] / 2) / f['vw'] * 100, 1),
                                 dy=round((cy - f['vh'] / 2) / f['vh'] * 100, 1),
                                 fill=round((f['x1'] - f['x0']) * (f['y1'] - f['y0']) / (f['vw'] * f['vh']) * 100),
                                 hgt=round((f['y1'] - f['y0']) / f['vh'] * 100),
                                 rad=f['rad']))
            texts[name] = pg.evaluate(TEXT_JS)
            anchors[name] = pg.evaluate(ANCHOR_JS)
            if statics is None or name == '3 できた':
                statics = pg.evaluate(STATIC_JS)
        ctx.close(); br.close()
    srv.shutdown()

    print('=' * 72)
    print('A. 図の寄りと空き（viewBox 1000x620 に対する、描かれているもの全部の外接箱）')
    print('   ルール＝中心ずれ 8%以上でアウト（引き継ぎ書 第3層／メモリ）／高さ60%未満は「絵が小さい」の目安')
    print('=' * 72)
    for r in rows:
        ng = []
        if abs(r['dx']) >= 8: ng.append(f"よこに{r['dx']:+.1f}%ずれ")
        if abs(r['dy']) >= 8: ng.append(f"たてに{r['dy']:+.1f}%ずれ")
        if r['hgt'] < 60:     ng.append(f"たての占め {r['hgt']}%")
        print(f"  {'✗' if ng else '○'} {r['name']:<18} よこ{r['dx']:+6.1f}% たて{r['dy']:+6.1f}% たての占め{r['hgt']:3}%  {' / '.join(ng)}")

    print()
    print('=' * 72)
    print('B. クッキーの大きさ（同じ状態の中で ちがう大きさが混ざっていないか）')
    print('=' * 72)
    for r in rows:
        if len(r['rad']) > 1:
            print(f"  ✗ {r['name']:<18} {r['rad']}  最大/最小 = {r['rad'][-1]/r['rad'][0]:.2f}倍")

    print()
    print('=' * 72)
    print('C. 文字の明暗比（第4層「補助テキストを薄くしない」＝4.5:1。app-audit は 3.0 でしか見ていない）')
    print('=' * 72)
    bad = {}
    for name, lst in texts.items():
        for it in lst:
            if it['ratio'] < 4.5:
                bad.setdefault((it['sel'], it['ratio'], it['px']), set()).add(it['t'])
    for (sel, ratio, px), ts in sorted(bad.items(), key=lambda k: k[0][1]):
        print(f"  ✗ {ratio:>5}:1  {px:>5}px  {sel:<28} 例「{list(ts)[0]}」")
    if not bad: print('  ○ なし')

    print()
    print('=' * 72)
    print('D. 動かない要素（チェック基準 §10-2：全状態で top の種類が1つ）')
    print('=' * 72)
    keys = sorted({k for a in anchors.values() for k in a})
    for k in keys:
        v = sorted({a[k] for a in anchors.values() if k in a})
        print(f"  {'○' if len(v) == 1 else '✗'} {k:<10} 種類{len(v):>3}  {v[:8]}{' …' if len(v) > 8 else ''}")

    print()
    print('=' * 72)
    print('E. 引き継ぎ書 2-2 との突き合わせ（静的）')
    print('=' * 72)
    print('  ぼかしのある影（2-2 境界「ぼかし影を使わない」／2026-09-22「ぼかし影をなくす」を めっちゃいい と評価）')
    for s in statics['shadow']: print('    ✗ ' + s)
    print('  未選択を うすくしている操作（2-2「未選択のほうを薄くする方法は選ばれなかった」）')
    for s in statics['dim']: print('    ✗ ' + s)
    print('  選ばれていないのに枠がある（2-2「枠がつくのは いま選ばれていることを示すときだけ」）')
    for s in statics['border'][:12]: print('    ✗ ' + s)

if __name__ == '__main__':
    main()
