# -*- coding: utf-8 -*-
"""わり算アプリ 動作トレース＋全状態スクショ（けテぶれの「テ」）

  python _trace.py               動作トレース（正解/不正解/連打/±/もどる/絵文字ゼロ/漢字の学年）＋JSエラー
  python _trace.py --shots DIR   全状態を 1280x800 / 1024x768 / 375x812 で撮り、contact sheet にまとめる
"""
import sys, os, re, threading, functools, http.server, socketserver, importlib.util
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); APP = os.path.basename(HERE)
PORT = 8815
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
class Srv(socketserver.TCPServer): allow_reuse_address = True
srv = Srv(("127.0.0.1", PORT), functools.partial(Quiet, directory=ROOT)); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{PORT}/{APP}/index.html'

FAIL, OKS = [], []
def check(cond, name, detail=''):
    (OKS if cond else FAIL).append(name + ('' if cond else f'  → {detail}'))

# 各段 最低2状態（はじめ／できた）＋ 数を変えた状態
STATES = [
 ('1 はじめ',        "setMode('mite'); goStage(0)"),
 ('1 3こ くばった',  "goStage(0); dealOne(); dealOne(); dealOne()"),
 ('1 できた',        "goStage(0); dealAll()"),
 ('2 はじめ',        "goStage(1)"),
 ('2 1人め',         "goStage(1); takeGroup()"),
 ('2 できた',        "goStage(1); takeGroup(); takeGroup(); takeGroup(); takeGroup()"),
 ('3 はじめ',        "goStage(2)"),
 ('3 まちがい',      "goStage(2); pick(0,'nin',document.querySelectorAll('#cmp0 .pick button')[1])"),
 ('3 できた',        "goStage(2); pick(0,'ko',document.querySelectorAll('#cmp0 .pick button')[0]); pick(1,'nin',document.querySelectorAll('#cmp1 .pick button')[1])"),
 ('4 はじめ',        "goStage(3)"),
 ('4 3×2',           "goStage(3); light(2,document.querySelectorAll('#strip button')[1])"),
 ('4 できた',        "goStage(3); light(4,document.querySelectorAll('#strip button')[3])"),
 ('5 はじめ',        "goStage(4)"),
 ('5 できた あまり2', "goStage(4); dealAll()"),
 ('5 あまりなし',    "P[5].a=12; goStage(4); dealAll(); P[5].a=14"),
 ('5 20こ 3人',      "P[5].a=20; goStage(4); dealAll(); P[5].a=14"),
 ('1 10こ 2人',      "P[1].a=10; P[1].b=2; goStage(0); dealAll(); P[1].a=12; P[1].b=3"),
 ('2 20こ 4こずつ',  "P[2].a=20; P[2].k=4; goStage(1); for(let i=0;i<5;i++)takeGroup(); P[2].a=12; P[2].k=3"),
 # じぶんでわかる（しきと答えを自分で入れる）
 ('1 じぶん しき',    "setMode('jibun'); goStage(0)"),
 ('1 じぶん まちがい', "setMode('jibun'); goStage(0); putTile(3); putTile(12)"),
 ('1 じぶん こたえ',  "setMode('jibun'); goStage(0); putTile(12); putTile(3); dealAll()"),
 ('1 じぶん できた',  "setMode('jibun'); goStage(0); putTile(12); putTile(3); dealAll(); putAns(4); putUnit('こ')"),
 ('2 じぶん こたえ',  "setMode('jibun'); goStage(1); putTile(12); putTile(3); for(let i=0;i<4;i++)takeGroup()"),
 ('2 じぶん できた',  "setMode('jibun'); goStage(1); putTile(12); putTile(3); for(let i=0;i<4;i++)takeGroup(); putAns(4); putUnit('人')"),
 ('5 じぶん こたえ',  "setMode('jibun'); goStage(4); putTile(14); putTile(3); dealAll()"),
 ('5 じぶん できた',  "setMode('jibun'); goStage(4); putTile(14); putTile(3); dealAll(); putAns(4); putAns(2); setMode('mite')"),
]

def run_state(pg, js):
    pg.evaluate("() => { window.__instant = true; " + js + "; }")

def trace(pg):
    E = lambda js: pg.evaluate(js)
    # ---------- ① 同じ数ずつ ----------
    run_state(pg, "goStage(0)")
    check(E("document.getElementById('navBackBtn').disabled"), '① はじめは もどる が押せない')
    check(E("document.querySelectorAll('#cookies .ck').length") == 12, '① クッキー12こ')
    check(E("document.querySelectorAll('#persons .person').length") == 3, '① 人3人')
    E("dealOne()"); check(E("S.dealt") == 1 and E("!document.getElementById('navBackBtn').disabled"), '① 1こ くばると もどる が押せる')
    E("dealOne(); dealOne()")
    check(E("!!document.getElementById('dealAllBtn')"), '① 1まわり くばると「のこりも くばる」が出る')
    check(E("[0,1,2].map(i=>document.querySelectorAll('#cookies .ck[data-fit-in=p'+i+']').length).join()") == '1,1,1', '① 順番に1こずつ')
    E("goBack()"); check(E("S.dealt") == 0 and E("S.stage") == 0, '① もどる＝やりなおし')
    E("dealAll()")
    check(E("S.done"), '① できた')
    check(E("[0,1,2].map(i=>document.querySelectorAll('#cookies .ck[data-fit-in=p'+i+']').length).join()") == '4,4,4', '① 4こずつ')
    check(E("document.querySelectorAll('#bubbles .bubble').length") == 3, '① ふきだし3つ')
    check(E("!document.getElementById('eq').hidden") and '12' in E("document.getElementById('eq').innerText"), '① しきが出る')
    check(E("document.querySelector('#eq .chip:nth-child(3)').classList.contains('c-plate')") and E("document.querySelector('#eq .chip:nth-child(5)').classList.contains('c-cookie')"), '① 3=あお 4=だいだい')
    check(E("!document.getElementById('nextrow').hidden"), '① つぎへ が出る')
    before = E("document.body.innerHTML.length"); E("dealOne(); dealAll()"); check(E("document.body.innerHTML.length") == before, '① できた後の連打で変わらない')
    E("hl('cookies'); hl('persons'); hl('perplate')"); check(E("document.querySelectorAll('.pulse').length") > 0, '① しきの数を おすと光る')
    # ±
    E("goStage(0); adjust('a',1)"); check(E("P[1].a") == 15, '① a＋ → 15')
    E("adjust('a',1); adjust('a',1)"); check(E("P[1].a") == 15, '① a は 5b=15 で止まる')
    E("adjust('b',1)"); check(E("P[1].b") == 4 and E("P[1].a") == 20, '① b＋ → 4人 20こ（1人分5は そのまま）')
    E("adjust('b',1)"); check(E("P[1].b") == 5 and E("P[1].a") == 20, '① b＋ → 5人 20こ')
    E("adjust('b',1)"); check(E("P[1].b") == 5, '① b は 5 で止まる')
    E("adjust('a',-1); adjust('a',-1); adjust('a',-1); adjust('a',-1)"); check(E("P[1].a") == 10, '① a− は 2b=10 で止まる')
    E("adjust('b',-1); adjust('b',-1); adjust('b',-1); adjust('b',-1)"); check(E("P[1].b") == 2 and E("P[1].a % 2 === 0 && P[1].a >= 4 && P[1].a <= 10"), '① b− → 2人、aは倍数')
    check(E("document.querySelectorAll('#cookies .ck').length === P[1].a"), '① ±のあと クッキーの数が合う')
    E("P[1].a=12; P[1].b=3; goStage(0)")
    # ---------- ② ○こずつ ----------
    E("goStage(1)")
    check(E("document.querySelectorAll('#persons .person').length") == 0, '② はじめは 人がいない')
    E("goBack()"); check(E("S.stage") == 0, '② 進みなしの もどる＝①へ')
    E("goStage(1); takeGroup()")
    check(E("S.persons") == 1 and E("document.querySelectorAll('#cookies .ck[data-fit-in=p0]').length") == 3, '② 3こ とる → 1人め 3こ')
    E("takeGroup(); takeGroup(); takeGroup()")
    check(E("S.done") and E("S.persons") == 4, '② 4人で できた')
    check(E("document.querySelector('#eq .chip:nth-child(3)').classList.contains('c-cookie')") and E("document.querySelector('#eq .chip:nth-child(5)').classList.contains('c-plate')"), '② 3=だいだい 4=あお（①と入れかわる）')
    before = E("document.body.innerHTML.length"); E("takeGroup()"); check(E("document.body.innerHTML.length") == before, '② できた後の連打で変わらない')
    E("adjust('k',1)"); check(E("P[2].k") == 4 and E("P[2].a") == 16, '② k＋ → 4こずつ 16こ（人数4は そのまま）')
    E("adjust('a',1); adjust('a',1); adjust('a',1)"); check(E("P[2].a") == 20, '② a は 5k=20 で止まる')
    E("adjust('k',1)"); check(E("P[2].k") == 5 and E("P[2].a") == 20, '② k＋ → 5こずつ 20こ')
    E("P[2].a=12; P[2].k=3; goStage(1)")
    # ---------- ③ くらべる ----------
    E("goStage(2)")
    check(E("document.querySelectorAll('#cmpTop .person').length") == 3 and E("document.querySelectorAll('#cmpBot .person').length") == 4, '③ 上3人・下4人')
    check(E("document.querySelectorAll('#cmpTop .ck').length") == 12 and E("document.querySelectorAll('#cmpBot .ck').length") == 12, '③ どちらも 12こ')
    E("pick(0,'nin',document.querySelectorAll('#cmp0 .pick button')[1])")
    check(E("S.ans[0]") is None and E("document.getElementById('msg').classList.contains('warn')"), '③ まちがい → ヒント（赤）')
    E("pick(0,'ko',document.querySelectorAll('#cmp0 .pick button')[0])")
    check(E("S.ans[0]") == 'ko' and E("document.querySelector('#cmpEq0 .chip:nth-child(5)').classList.contains('c-cookie')"), '③ 上：4こ が正解 → 4がだいだい')
    E("pick(0,'nin',document.querySelectorAll('#cmp0 .pick button')[1])"); check(E("S.ans[0]") == 'ko', '③ 答えたあとは変えられない')
    E("pick(1,'ko',document.querySelectorAll('#cmp1 .pick button')[0])"); check(E("S.ans[1]") is None, '③ 下：4こ は まちがい')
    E("pick(1,'nin',document.querySelectorAll('#cmp1 .pick button')[1])")
    check(E("S.done") and E("document.querySelector('#cmpEq1 .chip:nth-child(5)').classList.contains('c-plate')"), '③ 下：4人 が正解 → 4があお')
    check(E("!document.getElementById('nextrow').hidden"), '③ つぎへ が出る')
    # ---------- ④ かけ算 ----------
    E("goStage(3)")
    check(E("document.querySelectorAll('#strip button').length") == 9 and E("document.querySelectorAll('#strip button')[0].textContent") == '3×1=3', '④ 3のだん 9マス')
    check(E("document.querySelectorAll('#cookies .ck.dim').length") == 12, '④ はじめは 全部うすい')
    E("light(2,document.querySelectorAll('#strip button')[1])")
    check(E("document.querySelectorAll('#cookies .ck:not(.dim)').length") == 6 and 'たりない' in E("document.getElementById('status').innerText"), '④ 3×2 → 6こ 点く・たりない')
    E("light(5,document.querySelectorAll('#strip button')[4])")
    check('こえた' in E("document.getElementById('status').innerText"), '④ 3×5 → こえた')
    E("light(4,document.querySelectorAll('#strip button')[3])")
    check(E("S.done") and E("document.querySelectorAll('#strip button')[3].classList.contains('hit')"), '④ 3×4=12 で できた')
    check('÷' in E("document.getElementById('eq').innerText"), '④ わり算の しきも出る')
    st = E("document.getElementById('status').innerText"); E("light(6,document.querySelectorAll('#strip button')[5])"); check(E("document.getElementById('status').innerText") == st, '④ できた後は 変わらない')
    E("P[1].b=4; P[1].a=20; goStage(3)"); check(E("document.querySelectorAll('#strip button')[0].textContent") == '4×1=4' and E("document.querySelectorAll('#cookies .ck').length") == 20, '④ 数を変えると だんも変わる')
    E("P[1].a=12; P[1].b=3")
    # ---------- ⑤ あまり ----------
    E("goStage(4)")
    check(E("document.querySelectorAll('#cookies .ck').length") == 14 and E("document.querySelectorAll('#persons .person').length") == 3, '⑤ 14こ 3人')
    E("dealAll()")
    check(E("S.done") and not E("S.failed"), '⑤ できた')
    check(E("[0,1,2].map(i=>document.querySelectorAll('#cookies .ck[data-fit-in=p'+i+']').length).join()") == '4,4,4' and E("document.querySelectorAll('#cookies .ck[data-fit-in=tray]').length") == 2, '⑤ 4こずつ＋おぼんに 2こ もどる')
    check('あまり' in E("document.getElementById('eq').innerText") and '2' in E("document.getElementById('status').innerText"), '⑤ しきに あまり2')
    check(E("document.querySelectorAll('#eq .chip').length") == 4, '⑤ チップ4つ（あまり つき）')
    check(E("document.getElementById('nextBtn').textContent").startswith('さいしょから'), '⑤ 最後は「さいしょから」')
    E("P[5].a=12; goStage(4); dealAll()")
    check(E("S.done") and 'あまりはなし' in E("document.getElementById('status').innerText") and E("document.querySelectorAll('#eq .chip').length") == 3, '⑤ 12こなら あまりなし')
    E("P[5].a=20; P[5].b=2; goStage(4); dealAll()")
    check(E("[0,1].map(i=>document.querySelectorAll('#cookies .ck[data-fit-in=p'+i+']').length).join()") == '10,10', '⑤ 20こ2人 → 10こずつ（2だん）')
    E("P[5].a=6; P[5].b=5; goStage(4); dealAll()")
    check('1' in E("document.getElementById('status').innerText") and E("document.querySelectorAll('#cookies .ck[data-fit-in=tray]').length") == 1, '⑤ 6こ5人 → 1こずつ あまり1')
    E("adjust('a',-1)"); check(E("P[5].a") == 6, '⑤ a は 6 で止まる')
    E("adjust('a',1); adjust('b',1)"); check(E("P[5].a") == 7 and E("P[5].b") == 5, '⑤ ±が効く・bは5で止まる')
    E("P[5].a=14; P[5].b=3; goStage(4)")
    # さいしょから
    E("dealAll(); nextStage()"); check(E("S.stage") == 0, '⑤ さいしょから → ①')
    # 帯の ○
    check(E("document.querySelectorAll('#band .no.done').length") == 5, '帯の番号が5つとも緑（できた）')
    # ---------- じぶんでわかる ----------
    E("setMode('jibun'); goStage(0)")
    check(E("MODE") == 'jibun' and E("document.querySelector('#seg button.on').dataset.m") == 'jibun', 'じ 切り替えが効く')
    check(E("!document.getElementById('dealBtn')") and E("document.querySelectorAll('#eq .tiles .tile').length") == 4, 'じ① ボタンなし・タイル4つ')
    check(E("[...document.querySelectorAll('#eq .tiles .tile')].map(t=>+t.textContent).sort((a,b)=>a-b).join()") == '3,4,12,15', 'じ① タイル＝12,3,4,15')
    E("dealOne(); dealAll()"); check(E("S.dealt") == 0, 'じ① しきの前は くばれない')
    check(E("document.getElementById('navBackBtn').disabled"), 'じ① はじめは もどる が押せない')
    E("putTile(3); putTile(12)")
    check(E("J.slots.join()") == ',' and '先' in E("document.getElementById('msg').innerText") and E("document.getElementById('msg').classList.contains('warn')"), 'じ① 3÷12 → 順番のヒント・もどる')
    E("putTile(12); putTile(4)"); check('わる数は3' in E("document.getElementById('msg').innerText"), 'じ① 12÷4 → わる数のヒント')
    E("putTile(15); putTile(3)"); check('わられる数は12' in E("document.getElementById('msg').innerText"), 'じ① 15÷3 → わられる数のヒント')
    E("putTile(12)"); check(E("!document.getElementById('navBackBtn').disabled"), 'じ① タイルを置くと もどる が押せる')
    E("goBack()"); check(E("J.slots.join()") == ',' and E("S.stage") == 0, 'じ① もどる＝やりなおし')
    E("putTile(12); putTile(3)")
    check(E("J.phase") == 'deal' and E("!!document.getElementById('dealBtn')") and E("document.querySelectorAll('#eq .tiles').length") == 0, 'じ① 12÷3 → ○・くばるボタンが出る・タイル消える')
    check(E("document.querySelectorAll('#bRow .slot')[1].classList.contains('c-plate')"), 'じ① 正解で 3 があおになる')
    E("dealAll()")
    check(E("S.done") and E("J.phase") == 'kotae' and E("document.querySelectorAll('#bubbles .bubble').length") == 0, 'じ① 配り終わり → 答え入力（ふきだしは出ない）')
    check(E("document.querySelectorAll('#eq .keypad .tile').length") == 11 and E("document.querySelectorAll('#eq .units .tile').length") == 2, 'じ① キーパッド0〜10・単位2つ')
    E("putAns(3); putUnit('こ')"); check('かぞえて' in E("document.getElementById('msg').innerText") and E("J.ans[0]") is None, 'じ① 3こ → かぞえてのヒント・もどる')
    E("putAns(4); putUnit('人')"); check('「こ」' in E("document.getElementById('msg').innerText"), 'じ① 4人 → 単位のヒント')
    E("putAns(4); putUnit('こ')")
    check(E("J.phase") == 'done' and E("document.querySelectorAll('#bubbles .bubble').length") == 3 and 'せいかい' in E("document.getElementById('status').innerText"), 'じ① 4こ → せいかい・ふきだし3つ')
    check(E("document.querySelector('#eq .chip:nth-child(5)').classList.contains('c-cookie')") and E("!document.getElementById('nextrow').hidden"), 'じ① しきカード（4＝だいだい）・つぎへ')
    # ②
    E("goStage(1)"); check(E("document.querySelectorAll('#eq .tiles .tile').length") == 4 and E("!document.getElementById('takeBtn')"), 'じ② タイル4つ・とるボタンなし')
    E("takeGroup()"); check(E("S.persons") == 0, 'じ② しきの前は とれない')
    E("putTile(12); putTile(4)"); check('こずつだから' in E("document.getElementById('msg').innerText"), 'じ② 12÷4 → こずつのヒント')
    E("putTile(12); putTile(3); for(let i=0;i<4;i++)takeGroup()")
    check(E("S.done") and E("J.phase") == 'kotae' and E("document.querySelectorAll('#bubbles .bubble').length") == 0, 'じ② 4人 → 答え入力（番号ふきだしなし）')
    E("putAns(4); putUnit('こ')"); check('「人」' in E("document.getElementById('msg').innerText"), 'じ② 4こ → 単位のヒント')
    E("putAns(3); putUnit('人')"); check('人をかぞえて' in E("document.getElementById('msg').innerText"), 'じ② 3人 → かぞえてのヒント')
    E("putAns(4); putUnit('人')")
    check(E("J.phase") == 'done' and E("document.querySelectorAll('#bubbles .bubble').length") == 4 and E("document.querySelector('#eq .chip:nth-child(5)').classList.contains('c-plate')"), 'じ② 4人 → せいかい・番号ふきだし4つ・4があお')
    # ⑤
    E("goStage(4); putTile(14); putTile(3); dealAll()")
    check(E("S.done") and E("J.phase") == 'kotae' and E("document.querySelectorAll('#bRow .slot.ans').length") == 2 and E("document.querySelectorAll('#eq .units').length") == 0, 'じ⑤ 答え欄2つ（あまり）・単位なし')
    E("putAns(4); putAns(1)"); check('おぼん' in E("document.getElementById('msg').innerText") and E("J.ans.join()") == ',', 'じ⑤ あまり1 → おぼんのヒント')
    E("putAns(5); putAns(2)"); check('おさら' in E("document.getElementById('msg').innerText"), 'じ⑤ 5こ → おさらのヒント')
    E("putAns(4); putAns(2)")
    check(E("J.phase") == 'done' and 'あまる' in E("document.getElementById('status').innerText") and E("document.querySelectorAll('#eq .chip').length") == 4, 'じ⑤ 4あまり2 → せいかい・チップ4つ')
    E("P[5].a=12; goStage(4); putTile(12); putTile(3); dealAll(); putAns(4); putAns(0)")
    check(E("J.phase") == 'done' and 'あまりはなし' in E("document.getElementById('status').innerText"), 'じ⑤ 12こ → あまり0で せいかい')
    E("P[5].a=14")
    # ③④は もともと自分で答える → 同じ
    E("goStage(2)"); check(E("document.querySelectorAll('#cmp0 .pick button').length") == 2, 'じ③ 2択のまま')
    E("goStage(3)"); check(E("document.querySelectorAll('#strip button').length") == 9, 'じ④ 3のだんのまま')
    # ± でも しきづくりから
    E("goStage(0); putTile(12); adjust('a',1)"); check(E("J.phase") == 'shiki' and E("J.slots.join()") == ',' and E("P[1].a") == 15, 'じ± 数を変えると しきづくりからやり直し')
    E("P[1].a=12; setMode('mite'); goStage(0)")
    check(E("MODE") == 'mite' and E("!!document.getElementById('dealBtn')"), 'みてわかる に戻る')
    # ---------- 絵文字ゼロ・漢字の学年 ----------
    texts = []
    for name, js in STATES:
        run_state(pg, js)
        texts.append(E("document.body.innerText + ' ' + [...document.querySelectorAll('svg text')].map(t=>t.textContent).join(' ')"))
    allt = '\n'.join(texts)
    emo = re.findall(r'[\U0001F300-\U0001FAFF☀-➿️]', allt)
    check(not emo, '絵文字ゼロ', ''.join(set(emo)))
    kan = set(re.findall(r'[一-鿿]', allt))
    allowed = set()
    for g in ('bank_g1', 'bank_g2'):
        p = os.path.join(ROOT, '漢字マスターシート', g + '.py')
        spec = importlib.util.spec_from_file_location(g, p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        allowed |= {t[0] for t in m.PAIRS}
    over = sorted(kan - allowed)
    check(not over, '漢字は 小1・小2配当のみ', ''.join(over))
    # 文の途中の 半角スペース（ソース改行の混入）
    sp = re.findall(r'[ぁ-んァ-ン一-龥][ ](?=[ぁ-んァ-ン一-龥])', allt)
    # ※ このアプリは 分かち書き（「クッキー 12こを」）を意図して使うので、件数だけ出す
    print(f'  (分かち書きの空白 {len(sp)}件：意図したもの)')

LINES_JS = r"""() => {
  const out=[];
  const walk=(el)=>{ for(const nd of el.childNodes){
    if(nd.nodeType===3){
      const t=nd.nodeValue; if(!t.trim()) continue;
      const pe=nd.parentElement; if(!pe||pe.closest('svg')) continue;
      const cs=getComputedStyle(pe);
      if(cs.display==='none'||cs.visibility==='hidden'||pe.offsetParent===null) continue;
      const lines=[]; let cur='', prevTop=null;
      for(let i=0;i<t.length;i++){
        const r=document.createRange(); r.setStart(nd,i); r.setEnd(nd,i+1);
        const b=r.getBoundingClientRect(); if(b.width===0&&b.height===0){cur+=t[i];continue;}
        const top=Math.round(b.top);
        if(prevTop!==null&&top>prevTop+2){ lines.push(cur); cur=''; }
        prevTop=top; cur+=t[i];
      }
      lines.push(cur);
      if(lines.length>1) out.push({lines});
    } else if(nd.nodeType===1){
      const c=getComputedStyle(nd);
      if(c.display!=='none'&&c.visibility!=='hidden'&&nd.offsetParent!==null) walk(nd);
    } } };
  walk(document.body);
  return out;
}"""

def wrapcheck(browser):
    """折り返しが「文の途中」で起きていないか。
       孤立折り返し（最終行1〜2字）とは別物で、2026-09-20 にユーザー指摘で発覚するまで未測定だった。
       本文は jp() が文節を <span class="w"> で包むので、切れてよいのは文節の境目だけ。"""
    JP = r'[ぁ-んァ-ヶ一-龥ー]'
    bad = []
    for (w, h) in [(1280, 800), (1366, 768), (1024, 768), (820, 1180), (375, 812)]:
        ctx = browser.new_context(viewport={'width': w, 'height': h})
        pg = ctx.new_page(); pg.goto(URL); pg.wait_for_selector('#band button')
        for name, js in STATES:
            run_state(pg, js)
            for it in pg.evaluate(LINES_JS):
                ls = it['lines']
                for i in range(len(ls) - 1):
                    a = ls[i][-1:] ; c = ls[i + 1][:1]
                    if not a or not c: continue
                    why = None
                    if c in '。、！？）」': why = '行頭に句読点'
                    elif re.match(JP, a) and re.match(JP, c): why = '文の途中'
                    elif re.match(r'[0-9]', a) and re.match(JP, c): why = '数字と単位'
                    elif re.match(JP, a) and re.match(r'[0-9]', c): why = '数字の前'
                    if why: bad.append(f'{w}px {name} {why}: …{ls[i][-8:]} / {ls[i+1][:8]}…')
        ctx.close()
    check(not bad, '折り返しが文節の境目だけ（文の途中で切れない）', ' | '.join(dict.fromkeys(bad))[:400])


def shots(pg, outdir, browser):
    from PIL import Image
    os.makedirs(outdir, exist_ok=True)
    SIZES = [(1280, 800), (1024, 768), (375, 812)]
    KEY = {'1 はじめ', '1 できた', '2 できた', '3 できた', '4 できた', '5 できた あまり2'}
    files = {}
    for (w, h) in SIZES:
        ctx = browser.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1)
        p = ctx.new_page(); p.goto(URL); p.wait_for_function("document.fonts.status==='loaded'", timeout=8000)
        for i, (name, js) in enumerate(STATES):
            if w != 1280 and name not in KEY: continue
            run_state(p, js); p.wait_for_timeout(120)
            f = os.path.join(outdir, f'{w}x{h}_{i:02d}.png'); p.screenshot(path=f); files.setdefault((w, h), []).append((name, f))
            sh = p.evaluate("document.documentElement.scrollHeight"); sw = p.evaluate("document.documentElement.scrollWidth")
            if w >= 900 and sh > h + 1: print(f'  !! {w}x{h} {name}: 縦スクロール {sh}>{h}')
            if sw > w + 1: print(f'  !! {w}x{h} {name}: 横スクロール {sw}>{w}')
        ctx.close()
    # contact sheets
    from PIL import ImageDraw
    for (w, h), lst in files.items():
        per = 6 if w == 1280 else 6
        cols = 2 if w > 400 else 3
        sc = 0.5 if w > 400 else 0.6
        tw, th = int(w * sc), int(h * sc)
        for s in range(0, len(lst), per):
            chunk = lst[s:s + per]; rows = (len(chunk) + cols - 1) // cols
            sheet = Image.new('RGB', (cols * tw, rows * (th + 26)), '#222')
            d = ImageDraw.Draw(sheet)
            for j, (name, f) in enumerate(chunk):
                im = Image.open(f).resize((tw, th)); x = (j % cols) * tw; y = (j // cols) * (th + 26)
                sheet.paste(im, (x, y + 26)); d.text((x + 6, y + 6), f'{name}  {w}x{h}', fill='#fff')
            out = os.path.join(outdir, f'sheet_{w}_{s // per + 1}.png'); sheet.save(out); print('  sheet', out)

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1280, 'height': 800})
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append('console:' + m.text) if m.type == 'error' else None)
    pg.goto(URL); pg.wait_for_selector('#band button')
    if '--shots' in sys.argv:
        shots(pg, sys.argv[sys.argv.index('--shots') + 1], b)
    else:
        trace(pg)
        wrapcheck(b)
        print(f'OK {len(OKS)} / NG {len(FAIL)}')
        for f in FAIL: print('  ✗', f)
    errs = [e for e in errs if 'fonts.googleapis' not in e and 'fonts.gstatic' not in e]
    print('JSエラー:', len(errs)); [print('  ', e[:200]) for e in errs[:8]]
    b.close()
