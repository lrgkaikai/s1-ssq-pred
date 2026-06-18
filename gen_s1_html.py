# -*- coding: utf-8 -*-
"""生成 S1 预测对比网站 HTML，自动按期号倒序排列。
   运行此脚本即可重新生成 s1_results.html"""
import json, os, sys, re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('ssq_s1.py', encoding='utf-8').read().split('if __name__')[0])

all_reds = [reds for _, reds, _ in RAW_DATA]
all_blues = [blue for _, _, blue in RAW_DATA]
START_TEST = 10

# 生成逐期预测
rows = []
tr, tb = 0, 0
for test_idx in range(START_TEST, len(RAW_DATA)):
    period, actual_reds, actual_blue = RAW_DATA[test_idx]
    r_scores, _ = m10_cooccurrence(all_reds, all_blues, test_idx)
    _, b_scores = m12_exponential_decay(all_reds, all_blues, test_idx)
    z1p = top_n_in_zone(r_scores, Z1, 4)
    z2p = top_n_in_zone(r_scores, Z2, 4)
    z3p = top_n_in_zone(r_scores, Z3, 4)
    bp = top_n_blue(b_scores, 4)
    z1a = [r for r in actual_reds if r <= 11]
    z2a = [r for r in actual_reds if 12 <= r <= 22]
    z3a = [r for r in actual_reds if r >= 23]
    h1 = len(set(z1p) & set(z1a))
    h2 = len(set(z2p) & set(z2a))
    h3 = len(set(z3p) & set(z3a))
    bh = 1 if actual_blue in bp else 0
    th = h1 + h2 + h3
    tr += th; tb += bh
    rows.append(dict(period=period, z1p=z1p, z2p=z2p, z3p=z3p, bp=bp,
                     z1a=z1a, z2a=z2a, z3a=z3a, ba=actual_blue,
                     h1=h1, h2=h2, h3=h3, bh=bh, total_h=th))

nt = len(rows)
rows.reverse()
stats = dict(tests=nt, red_hits=tr, blue_hits=tb,
             rate=round(tr/(nt*6)*100, 1),
             first=rows[-1]['period'], last=rows[0]['period'],
             updated=datetime.now().strftime('%Y-%m-%d %H:%M'))

data_json = json.dumps(dict(stats=stats, rows=rows), ensure_ascii=False)

# 读取 HTML 模板
dirpath = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(dirpath, 's1_template.html')
out_path = os.path.join(dirpath, 's1_results.html')
with open(template_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 替换 DATA 占位符
html = html.replace('const DATA = __DATA_PLACEHOLDER__;',
                    'const DATA = %s;' % data_json)

# 更新时间戳
html = re.sub(r'更新于 [\d\-: ]+', '更新于 ' + stats['updated'], html)

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print('OK: %d期 | 命中率%.1f%% | %s~%s | 更新于%s' %
      (nt, stats['rate'], stats['first'], stats['last'], stats['updated']))
