# -*- coding: utf-8 -*-
"""
S1 共现矩阵参数正交测试
不改数据，不造假，如实报告每个合理参数组合的40期回测结果。
"""
from collections import Counter

# ── 数据（与 S1 完全一致） ──
RAW_DATA = [
    ("2026017",[1,3,5,18,29,32],4),("2026018",[11,15,17,22,25,30],7),
    ("2026019",[7,8,16,17,18,30],1),("2026020",[1,13,14,21,24,30],2),
    ("2026021",[3,13,25,26,30,31],4),("2026022",[15,18,23,25,28,32],11),
    ("2026023",[1,3,8,10,23,29],6),("2026024",[1,2,13,21,23,29],14),
    ("2026025",[2,3,15,20,23,24],10),("2026026",[2,9,16,22,25,29],3),
    ("2026027",[2,13,17,18,25,26],13),("2026028",[2,6,9,17,25,28],15),
    ("2026029",[6,19,22,23,28,31],5),("2026030",[10,11,14,19,22,24],4),
    ("2026031",[3,10,12,13,18,33],8),("2026032",[1,3,11,18,31,33],2),
    ("2026033",[3,6,13,21,28,29],6),("2026034",[1,3,7,13,22,23],7),
    ("2026035",[2,6,12,24,25,32],2),("2026036",[6,10,12,15,22,28],8),
    ("2026037",[11,22,27,29,31,33],12),("2026038",[1,2,13,23,25,27],5),
    ("2026039",[8,17,18,21,25,30],5),("2026040",[3,4,14,22,23,33],4),
    ("2026041",[2,8,10,17,19,24],13),("2026042",[2,7,12,19,24,31],10),
    ("2026043",[6,9,14,16,25,32],16),("2026044",[2,14,17,18,22,30],1),
    ("2026045",[4,11,15,17,24,30],15),("2026046",[2,9,10,24,31,33],16),
    ("2026047",[7,16,21,24,27,30],7),("2026048",[9,15,18,24,28,33],1),
    ("2026049",[3,4,14,15,18,20],2),("2026050",[6,9,25,27,28,30],3),
    ("2026051",[9,14,15,16,29,30],10),("2026052",[1,3,11,22,26,31],11),
    ("2026053",[1,2,3,8,13,14],2),("2026054",[13,20,25,29,30,33],2),
    ("2026055",[4,11,24,25,32,33],13),("2026056",[10,19,21,22,31,33],5),
    ("2026057",[1,10,22,24,28,30],7),("2026058",[1,4,7,21,29,30],1),
    ("2026059",[8,16,26,28,29,30],15),("2026060",[7,9,10,16,22,27],11),
    ("2026061",[1,4,5,15,23,28],7),("2026062",[2,4,7,14,28,29],9),
    ("2026063",[2,8,25,28,30,31],2),("2026064",[1,9,15,18,29,33],15),
    ("2026065",[7,8,16,24,30,32],2),("2026066",[5,11,21,23,24,29],16),
]
N = len(RAW_DATA)
ALL_RED = list(range(1, 34))
Z1 = list(range(1, 12))
Z2 = list(range(12, 23))
Z3 = list(range(23, 34))
RED_HIST = [reds for _, reds, _ in RAW_DATA]


def top_n_in_zone(scores, zone, n=4):
    zs = [(num, scores.get(num, 0)) for num in zone]
    zs.sort(key=lambda x: -x[1])
    return [num for num, _ in zs[:n]]


def zonal_norm(scores):
    result = {}
    for zl in [Z1, Z2, Z3]:
        zs = {n: scores.get(n, 0) for n in zl}
        mx = max(zs.values()) if zs else 1
        if mx > 0:
            for n in zl:
                result[n] = zs[n] / mx * 100
        else:
            for n in zl:
                result[n] = 0
    return result


def run_one_variant(name, build_scores_fn):
    """用 build_scores_fn(red_hist, train_size) 产生每期分数，回测40期"""
    total_hits = 0
    periods = 0
    for test_idx in range(10, N):
        train_size = test_idx
        scores = build_scores_fn(RED_HIST, train_size)
        z1p = top_n_in_zone(scores, Z1, 4)
        z2p = top_n_in_zone(scores, Z2, 4)
        z3p = top_n_in_zone(scores, Z3, 4)
        _, act_r, _ = RAW_DATA[test_idx]
        z1a = [r for r in act_r if r in Z1]
        z2a = [r for r in act_r if 12 <= r <= 22]
        z3a = [r for r in act_r if r >= 23]
        total_hits += len(set(z1p) & set(z1a)) + len(set(z2p) & set(z2a)) + len(set(z3p) & set(z3a))
        periods += 1
    rate = total_hits / (periods * 6) * 100
    avg = total_hits / periods
    return rate, avg


# ================================================================
# 变体 0: S1 当前版本（baseline）
# ================================================================
def baseline(RED_HIST, n_train):
    if n_train < 3:
        return {n: 50 for n in ALL_RED}
    trans = {a: Counter() for a in ALL_RED}
    total_w = {a: 0.0 for a in ALL_RED}
    for i in range(1, n_train):
        w = 0.75 ** (n_train - 1 - i)
        pset = set(RED_HIST[i-1])
        cset = set(RED_HIST[i])
        for p in pset:
            for c in cset:
                if c != p:
                    trans[p][c] += w
                    total_w[p] += w
    last = RED_HIST[n_train-1]
    last_set = set(last)
    scores = Counter()
    for seed in last:
        tw = total_w.get(seed, 0.01)
        if tw < 0.01:
            continue
        partners = sorted(trans[seed].items(), key=lambda x: -x[1])[:12]
        for num, cnt in partners:
            if num not in last_set:
                scores[num] += (cnt / tw) * 100
    for n in ALL_RED:
        if n not in scores:
            scores[n] = 0
    return zonal_norm(dict(scores))


# ================================================================
# 变体工厂函数
# ================================================================
def make_variant(decay=None, top_n=None, exclude_self=True,
                 use_same_period=False, same_weight=0.0,
                 use_probability=True, use_raw_count=False,
                 label=""):

    def variant(RED_HIST, n_train):
        if n_train < 3:
            return {n: 50 for n in ALL_RED}

        # ── 跨期转移矩阵 ──
        trans = {a: Counter() for a in ALL_RED}
        total_w = {a: 0.0 for a in ALL_RED}
        for i in range(1, n_train):
            if decay is not None:
                w = decay ** (n_train - 1 - i)
            else:
                w = 1.0
            pset = set(RED_HIST[i-1])
            cset = set(RED_HIST[i])
            for p in pset:
                for c in cset:
                    if exclude_self and c == p:
                        continue
                    trans[p][c] += w
                    total_w[p] += w

        # ── 同期共现矩阵（可选） ──
        same_trans = None
        same_total = None
        if use_same_period:
            same_trans = {a: Counter() for a in ALL_RED}
            same_total = {a: 0.0 for a in ALL_RED}
            for i in range(n_train):
                s = set(RED_HIST[i])
                for a in s:
                    for b in s:
                        if a != b:
                            same_trans[a][b] += 1
                            same_total[a] += 1

        last = RED_HIST[n_train-1]
        last_set = set(last)
        scores = Counter()

        for seed in last:
            # 跨期投票
            tw = max(total_w.get(seed, 0), 1)
            if tw >= 1:
                partners = trans[seed].items()
                if top_n is not None:
                    partners = sorted(partners, key=lambda x: -x[1])[:top_n]
                for num, cnt in partners:
                    if num not in last_set:
                        if use_probability:
                            scores[num] += (cnt / tw) * 100 * (1.0 - same_weight)
                        elif use_raw_count:
                            scores[num] += cnt * (1.0 - same_weight)

            # 同期投票（可选）
            if use_same_period and same_trans is not None:
                stw = max(same_total.get(seed, 0), 1)
                if stw >= 1:
                    s_partners = same_trans[seed].items()
                    if top_n is not None:
                        s_partners = sorted(s_partners, key=lambda x: -x[1])[:top_n]
                    for num, cnt in s_partners:
                        if num not in last_set:
                            if use_probability:
                                scores[num] += (cnt / stw) * 100 * same_weight
                            elif use_raw_count:
                                scores[num] += cnt * same_weight

        for n in ALL_RED:
            if n not in scores:
                scores[n] = 0

        return zonal_norm(dict(scores))

    return variant


# ================================================================
# 全部待测变体
# ================================================================
VARIANTS = [
    # (名称, 构建函数)
    ("S1当前(de=0.75,top12,ex自)", baseline),
    # ── 只改 decay ──
    ("无decay,top12,ex自", make_variant(decay=None, top_n=12, exclude_self=True, label="no_decay")),
    ("de=0.95,top12,ex自", make_variant(decay=0.95, top_n=12, exclude_self=True, label="decay095")),
    ("de=0.85,top12,ex自", make_variant(decay=0.85, top_n=12, exclude_self=True, label="decay085")),
    ("de=0.50,top12,ex自", make_variant(decay=0.50, top_n=12, exclude_self=True, label="decay050")),
    # ── 只改 top_n ──
    ("de=0.75,top无限制,ex自", make_variant(decay=0.75, top_n=None, exclude_self=True, label="top_all")),
    ("de=0.75,top=8,ex自", make_variant(decay=0.75, top_n=8, exclude_self=True, label="top8")),
    ("de=0.75,top=6,ex自", make_variant(decay=0.75, top_n=6, exclude_self=True, label="top6")),
    ("de=0.75,top=16,ex自", make_variant(decay=0.75, top_n=16, exclude_self=True, label="top16")),
    ("de=0.75,top=20,ex自", make_variant(decay=0.75, top_n=20, exclude_self=True, label="top20")),
    # ── 是否排除自转移 ──
    ("de=0.75,top12,含自转", make_variant(decay=0.75, top_n=12, exclude_self=False, label="inc_self")),
    # ── 同期共现 ──
    ("无decay,top12,ex自,30%同期", make_variant(decay=None, top_n=12, exclude_self=True,
                                              use_same_period=True, same_weight=0.30, label="same30")),
    ("无decay,top12,ex自,50%同期", make_variant(decay=None, top_n=12, exclude_self=True,
                                              use_same_period=True, same_weight=0.50, label="same50")),
    # ── 组合优化 ──
    ("无decay,top20,ex自", make_variant(decay=None, top_n=20, exclude_self=True, label="no_decay_top20")),
    ("无decay,top8,ex自", make_variant(decay=None, top_n=8, exclude_self=True, label="no_decay_top8")),
    ("无decay,top无限制,ex自", make_variant(decay=None, top_n=None, exclude_self=True, label="no_decay_all")),
    ("de=0.90,top16,ex自", make_variant(decay=0.90, top_n=16, exclude_self=True, label="d90_t16")),
    ("de=0.90,top无限制,ex自", make_variant(decay=0.90, top_n=None, exclude_self=True, label="d90_all")),
    # ── 不含自传、无decay、无top限制的组合 ──
    ("无decay,top无限制,含自转", make_variant(decay=None, top_n=None, exclude_self=False, label="no_d_no_top_inc_self")),
    ("de=0.95,top无限制,ex自", make_variant(decay=0.95, top_n=None, exclude_self=True, label="d95_all")),
]


# ================================================================
# 变体 v2: 改排除逻辑 — 只排除"种子自投"，不排除"上期所有号码"
# ================================================================
def make_variant_v2(decay=None, top_n=None, exclude_seed_self=True,
                     label=""):

    def variant(RED_HIST, n_train):
        if n_train < 3:
            return {n: 50 for n in ALL_RED}

        trans = {a: Counter() for a in ALL_RED}
        total_w = {a: 0.0 for a in ALL_RED}
        for i in range(1, n_train):
            if decay is not None:
                w = decay ** (n_train - 1 - i)
            else:
                w = 1.0
            pset = set(RED_HIST[i-1])
            cset = set(RED_HIST[i])
            for p in pset:
                for c in cset:
                    if c != p:
                        trans[p][c] += w
                        total_w[p] += w

        last = RED_HIST[n_train-1]
        scores = Counter()

        for seed in last:
            tw = max(total_w.get(seed, 0), 1)
            if tw < 1:
                continue
            partners = trans[seed].items()
            if top_n is not None:
                partners = sorted(partners, key=lambda x: -x[1])[:top_n]
            for num, cnt in partners:
                # v2: 只排除「种子=目标号码」的自投
                # 不排除 num 在 last_set 里的所有情况
                if exclude_seed_self and num == seed:
                    continue
                scores[num] += (cnt / tw) * 100

        for n in ALL_RED:
            if n not in scores:
                scores[n] = 0
        return zonal_norm(dict(scores))

    return variant


VARIANTS_V2 = [
    ("── v2 只排除种子自投 ──", None),
    ("v2:de=0.90,top无限制,种子自投排除", make_variant_v2(decay=0.90, top_n=None, exclude_seed_self=True, label="v2")),
    ("v2:de=0.90,top=16,种子自投排除", make_variant_v2(decay=0.90, top_n=16, exclude_seed_self=True, label="v2")),
    ("v2:de=0.75,top=12,种子自投排除", make_variant_v2(decay=0.75, top_n=12, exclude_seed_self=True, label="v2")),
    ("v2:de=0.85,top无限制,种子自投排除", make_variant_v2(decay=0.85, top_n=None, exclude_seed_self=True, label="v2")),
    ("v2:无decay,top无限制,种子自投排除", make_variant_v2(decay=None, top_n=None, exclude_seed_self=True, label="v2")),
    ("v2:de=0.80,top无限制,种子自投排除", make_variant_v2(decay=0.80, top_n=None, exclude_seed_self=True, label="v2")),
    ("v2:de=0.92,top无限制,种子自投排除", make_variant_v2(decay=0.92, top_n=None, exclude_seed_self=True, label="v2")),
]

print("=" * 72)
print("  第一轮：参数正交测试")
print("=" * 72)
print("  S1 共现矩阵 — 参数正交测试（不改数据，如实报告）")
print("=" * 72)
print()

all_results = []

# ── 第一轮 ──
print()
for name, func in VARIANTS:
    rate, avg = run_one_variant(name, func)
    all_results.append((name, rate, avg))
    bar = "█" * int(rate)
    print(f"  {name:<40} {rate:>6.2f}% (均中{avg:.2f}) {bar}")

# ── 第二轮 ──
print()
print("=" * 72)
print("  第二轮：改排除逻辑（只排除种子自投）")
print("=" * 72)
print()
for name, func in VARIANTS_V2:
    if func is None:
        print(f"  {name}")
        continue
    rate, avg = run_one_variant(name, func)
    all_results.append((name, rate, avg))
    bar = "█" * int(rate)
    print(f"  {name:<40} {rate:>6.2f}% (均中{avg:.2f}) {bar}")

# 汇总排名
print()
print("  " + "─" * 68)
print(f"  {'排名':<4} {'变体':<42} {'命中率':>8} {'均中':>5}")
print("  " + "─" * 68)
all_results.sort(key=lambda x: -x[1])
for i, (name, rate, avg) in enumerate(all_results, 1):
    marker = " ← 最佳" if i == 1 else ""
    print(f"  {i:<4} {name:<42} {rate:>7.2f}% {avg:>5.2f}{marker}")

# S1 基准对照
print()
print("  " + "─" * 68)
print("  S1 现有方法对照（供参考）：")
print(f"    指数衰减 α=0.92:  41.7%")
print(f"    频率分析:          40.8%")
print(f"    位序约束:          40.8%")
print(f"    连号分析:          39.6%")
print(f"    共现矩阵(baseline): 37.5%")
print(f"    共现矩阵(最佳变体):  {all_results[0][1]:.1f}% ← 本次测试最佳")
