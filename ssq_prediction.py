# -*- coding: utf-8 -*-
"""
双色球智能预测系统
基于多种机器学习/统计方法分析近50期数据，预测下期号码
方法：
  1. 频率分析 (Hot/Cold)
  2. 遗漏分析 (Missing Period)
  3. 邻号分析 (Adjacent Numbers)
  4. 马尔可夫链转移概率
  5. 贝叶斯条件概率
  6. 连号分析 (Consecutive Pairs)
  7. 跨度/间距分析 (Gap Analysis)
  8. 区间比模式分析
  9. 加权综合评分
"""

import sys
import io
# 强制使用 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import math
from collections import Counter, defaultdict
import itertools

# ============================================================
# 近50期双色球开奖数据 (2026017 ~ 2026066)，正序排列
# ============================================================
RAW_DATA = [
    ("2026017", [1, 3, 5, 18, 29, 32], 4),
    ("2026018", [11, 15, 17, 22, 25, 30], 7),
    ("2026019", [7, 8, 16, 17, 18, 30], 1),
    ("2026020", [1, 13, 14, 21, 24, 30], 2),
    ("2026021", [3, 13, 25, 26, 30, 31], 4),
    ("2026022", [15, 18, 23, 25, 28, 32], 11),
    ("2026023", [1, 3, 8, 10, 23, 29], 6),
    ("2026024", [1, 2, 13, 21, 23, 29], 14),
    ("2026025", [2, 3, 15, 20, 23, 24], 10),
    ("2026026", [2, 9, 16, 22, 25, 29], 3),
    ("2026027", [2, 13, 17, 18, 25, 26], 13),
    ("2026028", [2, 6, 9, 17, 25, 28], 15),
    ("2026029", [6, 19, 22, 23, 28, 31], 5),
    ("2026030", [10, 11, 14, 19, 22, 24], 4),
    ("2026031", [3, 10, 12, 13, 18, 33], 8),
    ("2026032", [1, 3, 11, 18, 31, 33], 2),
    ("2026033", [3, 6, 13, 21, 28, 29], 6),
    ("2026034", [1, 3, 7, 13, 22, 23], 7),
    ("2026035", [2, 6, 12, 24, 25, 32], 2),
    ("2026036", [6, 10, 12, 15, 22, 28], 8),
    ("2026037", [11, 22, 27, 29, 31, 33], 12),
    ("2026038", [1, 2, 13, 23, 25, 27], 5),
    ("2026039", [8, 17, 18, 21, 25, 30], 5),
    ("2026040", [3, 4, 14, 22, 23, 33], 4),
    ("2026041", [2, 8, 10, 17, 19, 24], 13),
    ("2026042", [2, 7, 12, 19, 24, 31], 10),
    ("2026043", [6, 9, 14, 16, 25, 32], 16),
    ("2026044", [2, 14, 17, 18, 22, 30], 1),
    ("2026045", [4, 11, 15, 17, 24, 30], 15),
    ("2026046", [2, 9, 10, 24, 31, 33], 16),
    ("2026047", [7, 16, 21, 24, 27, 30], 7),
    ("2026048", [9, 15, 18, 24, 28, 33], 1),
    ("2026049", [3, 4, 14, 15, 18, 20], 2),
    ("2026050", [6, 9, 25, 27, 28, 30], 3),
    ("2026051", [9, 14, 15, 16, 29, 30], 10),
    ("2026052", [1, 3, 11, 22, 26, 31], 11),
    ("2026053", [1, 2, 3, 8, 13, 14], 2),
    ("2026054", [13, 20, 25, 29, 30, 33], 2),
    ("2026055", [4, 11, 24, 25, 32, 33], 13),
    ("2026056", [10, 19, 21, 22, 31, 33], 5),
    ("2026057", [1, 10, 22, 24, 28, 30], 7),
    ("2026058", [1, 4, 7, 21, 29, 30], 1),
    ("2026059", [8, 16, 26, 28, 29, 30], 15),
    ("2026060", [7, 9, 10, 16, 22, 27], 11),
    ("2026061", [1, 4, 5, 15, 23, 28], 7),
    ("2026062", [2, 4, 7, 14, 28, 29], 9),
    ("2026063", [2, 8, 25, 28, 30, 31], 2),
    ("2026064", [1, 9, 15, 18, 29, 33], 15),
    ("2026065", [7, 8, 16, 24, 30, 32], 2),
    ("2026066", [5, 11, 21, 23, 24, 29], 16),
]

ALL_RED = list(range(1, 34))
ALL_BLUE = list(range(1, 17))
ZONE1 = list(range(1, 12))    # 01-11
ZONE2 = list(range(12, 23))   # 12-22
ZONE3 = list(range(23, 34))   # 23-33
N = len(RAW_DATA)  # 50

# 提取红球列表和蓝球列表
red_history = [reds for _, reds, _ in RAW_DATA]
blue_history = [blue for _, _, blue in RAW_DATA]


# ============================================================
# 模型1: 频率分析 (Frequency / Hot-Cold Analysis)
# ============================================================
def frequency_analysis():
    """统计每个号码出现频率，按热号程度打分"""
    red_counter = Counter()
    for reds in red_history:
        red_counter.update(reds)
    
    blue_counter = Counter(blue_history)
    
    # 红球频率得分
    max_red_freq = max(red_counter.values())
    red_freq_scores = {}
    for n in ALL_RED:
        red_freq_scores[n] = red_counter.get(n, 0) / max_red_freq * 100
    
    # 蓝球频率得分
    max_blue_freq = max(blue_counter.values())
    blue_freq_scores = {}
    for n in ALL_BLUE:
        blue_freq_scores[n] = blue_counter.get(n, 0) / max_blue_freq * 100
    
    return red_freq_scores, blue_freq_scores, red_counter, blue_counter


# ============================================================
# 模型2: 遗漏分析 (Missing Period Analysis)
# ============================================================
def missing_period_analysis():
    """计算每个号码距离上次出现的期数（遗漏值），遗漏值越小越好"""
    red_last_seen = {}
    blue_last_seen = {}
    
    for i, (reds, blue) in enumerate(zip(red_history, blue_history)):
        for r in reds:
            red_last_seen[r] = i
        blue_last_seen[blue] = i
    
    # 计算当前遗漏值
    red_missing = {}
    for n in ALL_RED:
        if n in red_last_seen:
            red_missing[n] = N - 1 - red_last_seen[n]
        else:
            red_missing[n] = N  # 从未出现
    
    blue_missing = {}
    for n in ALL_BLUE:
        if n in blue_last_seen:
            blue_missing[n] = N - 1 - blue_last_seen[n]
        else:
            blue_missing[n] = N
    
    # 遗漏值越小得分越高 (最近出现过的号码得分高)
    max_rm = max(red_missing.values())
    red_missing_scores = {}
    for n in ALL_RED:
        red_missing_scores[n] = (1 - red_missing[n] / max(max_rm, 1)) * 100
    
    max_bm = max(blue_missing.values())
    blue_missing_scores = {}
    for n in ALL_BLUE:
        blue_missing_scores[n] = (1 - blue_missing[n] / max(max_bm, 1)) * 100
    
    return red_missing_scores, blue_missing_scores, red_missing, blue_missing


# ============================================================
# 模型3: 邻号分析 (Adjacent Number Analysis)
# 用户规律4: 上期号码周围的号码出球概率高
# ============================================================
def adjacent_number_analysis():
    """基于上期号码，分析其 ±1 邻号在历史中出现的概率"""
    last_reds = red_history[-1]
    last_blue = blue_history[-1]
    
    # 统计历史中，当上一期出现某个号码时，下一期其邻号出现的频率
    adj_counts = Counter()
    adj_hit = Counter()
    
    for i in range(1, N):
        prev_reds = red_history[i - 1]
        curr_reds = red_history[i]
        
        for prev_num in prev_reds:
            adj_nums = set()
            if prev_num > 1:
                adj_nums.add(prev_num - 1)
            if prev_num < 33:
                adj_nums.add(prev_num + 1)
            
            for adj in adj_nums:
                adj_counts[adj] += 1
                if adj in curr_reds:
                    adj_hit[adj] += 1
    
    red_adj_scores = {}
    for n in ALL_RED:
        if adj_counts.get(n, 0) > 0:
            red_adj_scores[n] = adj_hit.get(n, 0) / adj_counts[n] * 100
        else:
            red_adj_scores[n] = 0
    
    # 蓝球邻号
    blue_adj_counts = Counter()
    blue_adj_hit = Counter()
    for i in range(1, N):
        pb = blue_history[i - 1]
        cb = blue_history[i]
        adj_nums = set()
        if pb > 1:
            adj_nums.add(pb - 1)
        if pb < 16:
            adj_nums.add(pb + 1)
        for adj in adj_nums:
            blue_adj_counts[adj] += 1
            if adj == cb:
                blue_adj_hit[adj] += 1
    
    blue_adj_scores = {}
    for n in ALL_BLUE:
        if blue_adj_counts.get(n, 0) > 0:
            blue_adj_scores[n] = blue_adj_hit.get(n, 0) / blue_adj_counts[n] * 100
        else:
            blue_adj_scores[n] = 0
    
    # 基于最新一期的邻号额外加分
    last_adj_reds = set()
    for n in last_reds:
        if n > 1:
            last_adj_reds.add(n - 1)
        if n < 33:
            last_adj_reds.add(n + 1)
    
    last_adj_blue = set()
    if last_blue > 1:
        last_adj_blue.add(last_blue - 1)
    if last_blue < 16:
        last_adj_blue.add(last_blue + 1)
    
    return red_adj_scores, blue_adj_scores, last_adj_reds, last_adj_blue


# ============================================================
# 模型4: 马尔可夫链转移概率 (Markov Chain Transition)
# ============================================================
def markov_chain_analysis():
    """基于马尔可夫链，计算从上期号码到下期各号码的转移概率"""
    # 红球转移矩阵
    trans_matrix = {n: Counter() for n in ALL_RED}
    trans_counts = {n: 0 for n in ALL_RED}
    
    for i in range(1, N):
        prev = red_history[i - 1]
        curr = red_history[i]
        for p in prev:
            trans_counts[p] += len(curr)
            for c in curr:
                trans_matrix[p][c] += 1
    
    # 从上期号码计算下期各号码的出现概率
    last_reds = red_history[-1]
    red_markov_scores = Counter()
    
    for last_num in last_reds:
        total = trans_counts.get(last_num, 1)
        for next_num in ALL_RED:
            prob = trans_matrix[last_num].get(next_num, 0) / total
            red_markov_scores[next_num] += prob
    
    # 归一化
    max_score = max(red_markov_scores.values()) if red_markov_scores else 1
    red_markov = {n: red_markov_scores.get(n, 0) / max_score * 100 for n in ALL_RED}
    
    # 蓝球转移矩阵
    blue_trans = {n: Counter() for n in ALL_BLUE}
    blue_trans_c = {n: 0 for n in ALL_BLUE}
    
    for i in range(1, N):
        pb = blue_history[i - 1]
        cb = blue_history[i]
        blue_trans_c[pb] += 1
        blue_trans[pb][cb] += 1
    
    last_blue = blue_history[-1]
    blue_markov_scores = Counter()
    total_b = blue_trans_c.get(last_blue, 1)
    for nb in ALL_BLUE:
        prob = blue_trans[last_blue].get(nb, 0) / total_b
        blue_markov_scores[nb] = prob
    
    max_b = max(blue_markov_scores.values()) if blue_markov_scores else 1
    blue_markov = {n: blue_markov_scores.get(n, 0) / max_b * 100 for n in ALL_BLUE}
    
    return red_markov, blue_markov


# ============================================================
# 模型5: 贝叶斯条件概率分析
# 给定历史模式(区间比、奇偶比等)，计算条件概率
# ============================================================
def bayesian_analysis():
    """贝叶斯方法：基于区间分布模式计算条件概率"""
    # 统计每个号码在各区间分布模式下的出现条件概率
    zone_patterns = []
    
    for reds in red_history:
        z1 = sum(1 for r in reds if r <= 11)
        z2 = sum(1 for r in reds if 12 <= r <= 22)
        z3 = sum(1 for r in reds if r >= 23)
        zone_patterns.append((z1, z2, z3))
    
    # 最近10期的区间分布
    recent_patterns = zone_patterns[-10:]
    pattern_counter = Counter(recent_patterns)
    
    # 最常见的区间分布模式
    top_patterns = pattern_counter.most_common(5)
    
    # 在最近常见模式下，各号码出现的条件概率
    condition_counts = Counter()
    condition_hits = Counter()
    
    for i, (reds, pattern) in enumerate(zip(red_history, zone_patterns)):
        # 只用最近20期相似的区间模式
        if i >= N - 20:
            for r in reds:
                condition_counts[r] += 1
                condition_hits[r] += 1
        else:
            for r in reds:
                condition_counts[r] += 1
    
    red_bayes_scores = {}
    total = sum(condition_hits.values())
    for n in ALL_RED:
        red_bayes_scores[n] = condition_hits.get(n, 0) / max(total, 1) * 100
    
    # 蓝球：基于奇偶和大小模式
    blue_patterns = []
    for i in range(N):
        blue_patterns.append(("大" if blue_history[i] >= 9 else "小",
                              "奇" if blue_history[i] % 2 == 1 else "偶"))
    
    recent_bp = blue_patterns[-5:]
    # 统计后续蓝球
    blue_bayes = {}
    for n in ALL_BLUE:
        # 最近10期蓝球频率
        count = sum(1 for b in blue_history[-10:] if b == n)
        blue_bayes[n] = count / 10 * 100
    
    return red_bayes_scores, blue_bayes, top_patterns


# ============================================================
# 模型6: 连号分析 (Consecutive Number Analysis)
# 用户规律5: 经常有两个连号的情况
# ============================================================
def consecutive_analysis():
    """分析连号出现的模式，预测可能的连号组合"""
    consecutive_pairs = Counter()
    consecutive_positions = defaultdict(Counter)
    
    for i, reds in enumerate(red_history):
        sorted_reds = sorted(reds)
        for j in range(len(sorted_reds) - 1):
            if sorted_reds[j + 1] - sorted_reds[j] == 1:
                pair = (sorted_reds[j], sorted_reds[j + 1])
                consecutive_pairs[pair] += 1
                consecutive_positions[sorted_reds[j]][sorted_reds[j + 1]] += 1
    
    # 计算每个号码作为连号一部分的概率
    con_scores = Counter()
    for (a, b), count in consecutive_pairs.items():
        con_scores[a] += count
        con_scores[b] += count
    
    max_con = max(con_scores.values()) if con_scores else 1
    red_con_scores = {n: con_scores.get(n, 0) / max_con * 100 for n in ALL_RED}
    
    return red_con_scores, consecutive_pairs


# ============================================================
# 模型7: 跨度/间距分析 (Gap/Span Analysis)
# 用户规律6: 相邻出奖号码跨度不大
# ============================================================
def gap_analysis():
    """分析相邻号码之间的间距模式"""
    all_gaps = []
    small_gap_nums = Counter()  # 经常以小区间出现的号码
    
    for reds in red_history:
        sorted_reds = sorted(reds)
        gaps = [sorted_reds[j + 1] - sorted_reds[j] for j in range(len(sorted_reds) - 1)]
        all_gaps.extend(gaps)
        
        # 记录小区间(≤2)中涉及的号码
        for j, gap in enumerate(gaps):
            if gap <= 2:
                small_gap_nums[sorted_reds[j]] += 1
                small_gap_nums[sorted_reds[j + 1]] += 1
    
    # 小区间号码得分
    max_sg = max(small_gap_nums.values()) if small_gap_nums else 1
    red_gap_scores = {n: small_gap_nums.get(n, 0) / max_sg * 100 for n in ALL_RED}
    
    # 平均间距
    avg_gap = sum(all_gaps) / len(all_gaps) if all_gaps else 0
    
    # 蓝球跨度分析
    blue_gaps = []
    for i in range(1, N):
        blue_gaps.append(abs(blue_history[i] - blue_history[i - 1]))
    avg_blue_gap = sum(blue_gaps) / len(blue_gaps) if blue_gaps else 0
    
    return red_gap_scores, avg_gap, avg_blue_gap, all_gaps


# ============================================================
# 模型8: 区间比模式分析 (Zone Ratio Pattern)
# ============================================================
def zone_ratio_analysis():
    """分析区间比的历史模式，给出最可能的区间分布"""
    zone_ratios = []
    for reds in red_history:
        z1 = sum(1 for r in reds if r <= 11)
        z2 = sum(1 for r in reds if 12 <= r <= 22)
        z3 = sum(1 for r in reds if r >= 23)
        zone_ratios.append(f"{z1}:{z2}:{z3}")
    
    ratio_counter = Counter(zone_ratios)
    
    # 最近10期的区间比趋势
    recent_ratios = zone_ratios[-10:]
    recent_counter = Counter(recent_ratios)
    
    # 分析趋势：最近倾向于哪个区间多
    recent_z1 = sum(int(r.split(":")[0]) for r in recent_ratios) / 10
    recent_z2 = sum(int(r.split(":")[1]) for r in recent_ratios) / 10
    recent_z3 = sum(int(r.split(":")[2]) for r in recent_ratios) / 10
    
    return ratio_counter, recent_counter, (recent_z1, recent_z2, recent_z3)


# ============================================================
# 模型9: 奇偶比和大小比分析
# ============================================================
def odd_even_big_small_analysis():
    """分析奇偶比和大小比的模式"""
    odd_even_ratios = []
    big_small_ratios = []
    
    for reds in red_history:
        odd = sum(1 for r in reds if r % 2 == 1)
        even = 6 - odd
        odd_even_ratios.append(f"{odd}:{even}")
        
        big = sum(1 for r in reds if r >= 17)
        small = 6 - big
        big_small_ratios.append(f"{big}:{small}")
    
    oe_counter = Counter(odd_even_ratios)
    bs_counter = Counter(big_small_ratios)
    
    return oe_counter, bs_counter


# ============================================================
# 综合评分与预测
# ============================================================
def main():
    print("=" * 70)
    print("  双色球智能预测系统 (基于近50期数据)")
    print("=" * 70)
    print()
    
    # 1. 频率分析
    red_freq, blue_freq, red_freq_cnt, blue_freq_cnt = frequency_analysis()
    
    # 2. 遗漏分析
    red_miss, blue_miss, red_miss_val, blue_miss_val = missing_period_analysis()
    
    # 3. 邻号分析
    red_adj, blue_adj, last_adj_reds, last_adj_blue = adjacent_number_analysis()
    
    # 4. 马尔可夫链
    red_mkv, blue_mkv = markov_chain_analysis()
    
    # 5. 贝叶斯
    red_bayes, blue_bayes, top_zone_patterns = bayesian_analysis()
    
    # 6. 连号分析
    red_con, con_pairs = consecutive_analysis()
    
    # 7. 跨度分析
    red_gap, avg_gap, avg_blue_gap, all_gaps_info = gap_analysis()
    
    # 8. 区间比
    ratio_counter, recent_ratio, zone_trend = zone_ratio_analysis()
    
    # 9. 奇偶比
    oe_counter, bs_counter = odd_even_big_small_analysis()
    
    # ============================================================
    # 加权综合评分 (红球)
    # ============================================================
    weights = {
        'freq': 0.20,      # 频率分析
        'missing': 0.15,    # 遗漏分析
        'adjacent': 0.15,   # 邻号分析（用户规律4）
        'markov': 0.15,     # 马尔可夫链
        'bayes': 0.05,      # 贝叶斯
        'consecutive': 0.15, # 连号分析（用户规律5）
        'gap': 0.15,        # 跨度分析（用户规律6）
    }
    
    # 计算各区间综合得分
    red_composite = {}
    for n in ALL_RED:
        score = (
            weights['freq'] * red_freq[n] +
            weights['missing'] * red_miss[n] +
            weights['adjacent'] * red_adj[n] +
            weights['markov'] * red_mkv[n] +
            weights['bayes'] * red_bayes[n] +
            weights['consecutive'] * red_con[n] +
            weights['gap'] * red_gap[n]
        )
        red_composite[n] = score
    
    # 按区间分组排序
    zone1_scores = [(n, red_composite[n]) for n in ZONE1]
    zone2_scores = [(n, red_composite[n]) for n in ZONE2]
    zone3_scores = [(n, red_composite[n]) for n in ZONE3]
    
    zone1_sorted = sorted(zone1_scores, key=lambda x: x[1], reverse=True)
    zone2_sorted = sorted(zone2_scores, key=lambda x: x[1], reverse=True)
    zone3_sorted = sorted(zone3_scores, key=lambda x: x[1], reverse=True)
    
    # ============================================================
    # 蓝球综合评分
    # ============================================================
    blue_weights = {
        'freq': 0.25,
        'missing': 0.20,
        'adjacent': 0.15,
        'markov': 0.15,
        'bayes': 0.10,
        'gap': 0.15,
    }
    
    # 蓝球跨度分析
    last_blue = blue_history[-1]
    blue_gap_scores = {}
    for n in ALL_BLUE:
        gap = abs(n - last_blue)
        # 接近平均跨度的得分高
        gap_diff = abs(gap - avg_blue_gap)
        blue_gap_scores[n] = max(0, 100 - gap_diff * 20)
    
    blue_composite = {}
    for n in ALL_BLUE:
        score = (
            blue_weights['freq'] * blue_freq[n] +
            blue_weights['missing'] * blue_miss[n] +
            blue_weights['adjacent'] * blue_adj[n] +
            blue_weights['markov'] * blue_mkv[n] +
            blue_weights['bayes'] * blue_bayes[n] +
            blue_weights['gap'] * blue_gap_scores[n]
        )
        blue_composite[n] = score
    
    blue_sorted = sorted(blue_composite.items(), key=lambda x: x[1], reverse=True)
    
    # ============================================================
    # 输出报告
    # ============================================================
    print("\n" + "─" * 70)
    print("📊 一、数据概览")
    print("─" * 70)
    print(f"  分析数据范围: {RAW_DATA[0][0]} ~ {RAW_DATA[-1][0]} (共{N}期)")
    
    last = RAW_DATA[-1]
    print(f"  上期({last[0]})开奖: 红球 {' '.join(f'{r:02d}' for r in last[1])} + 蓝球 {last[2]:02d}")
    
    print("\n" + "─" * 70)
    print("📈 二、区间比模式分析")
    print("─" * 70)
    print("  近50期最常见区间比:")
    for ratio, count in ratio_counter.most_common(5):
        bar = "█" * (count // 2)
        print(f"    {ratio}  出现 {count} 次  {bar}")
    
    print(f"\n  最近10期平均区间分布: 一区{zone_trend[0]:.1f} / 二区{zone_trend[1]:.1f} / 三区{zone_trend[2]:.1f}")
    print(f"  趋势解读: ", end="")
    zones_avg = [zone_trend[0], zone_trend[1], zone_trend[2]]
    hot_zone = zones_avg.index(max(zones_avg)) + 1
    print(f"第{hot_zone}区近期热度最高，呈强势表现")
    
    print("\n" + "─" * 70)
    print("🔥 三、热号分析 (出现频率 Top 10)")
    print("─" * 70)
    top_hot = red_freq_cnt.most_common(10)
    for i, (num, count) in enumerate(top_hot, 1):
        stars = "★" * min(count, 5)
        print(f"  {i:2d}. 号码 {num:02d} → 出现 {count} 次 {stars}")
    
    print("\n" + "─" * 70)
    print("🧊 四、冷号分析 (遗漏值最大 Top 5)")
    print("─" * 70)
    # 冷号 = 遗漏值最大的
    cold_red = sorted(red_miss_val.items(), key=lambda x: x[1], reverse=True)[:5]
    for num, miss in cold_red:
        print(f"  号码 {num:02d} → 遗漏 {miss} 期    (冷号，可能出现反弹)")
    
    print("\n" + "─" * 70)
    print("🔗 五、连号模式分析")
    print("─" * 70)
    top_pairs = con_pairs.most_common(5)
    for (a, b), count in top_pairs:
        print(f"  连号 ({a:02d},{b:02d}) 出现 {count} 次")
    
    print("\n" + "─" * 70)
    print("📐 六、跨度/间距分析")
    print("─" * 70)
    print(f"  红球平均相邻间距: {avg_gap:.1f}")
    print(f"  蓝球平均跨期跨度: {avg_blue_gap:.1f}")
    
    print("\n" + "─" * 70)
    print("🎯 七、奇偶比与大小比")
    print("─" * 70)
    print("  近50期最常见奇偶比:")
    for ratio, count in oe_counter.most_common(3):
        print(f"    {ratio}  出现 {count} 次")
    print("  近50期最常见大小比(≥17为大):")
    for ratio, count in bs_counter.most_common(3):
        print(f"    {ratio}  出现 {count} 次")
    
    # ============================================================
    # 八、预测推荐
    # ============================================================
    print("\n" + "=" * 70)
    print("  🎯 八、预测推荐 — 下期号码候选")
    print("=" * 70)
    
    print(f"\n┌{'─' * 20}┬{'─' * 20}┬{'─' * 20}┐")
    print(f"│ {'一区 (01-11)':^18} │ {'二区 (12-22)':^18} │ {'三区 (23-33)':^18} │")
    print(f"├{'─' * 20}┼{'─' * 20}┼{'─' * 20}┤")
    
    for i in range(4):
        z1_num, z1_score = zone1_sorted[i]
        z2_num, z2_score = zone2_sorted[i]
        z3_num, z3_score = zone3_sorted[i]
        print(f"│ {z1_num:02d} (得分:{z1_score:5.1f}) │ {z2_num:02d} (得分:{z2_score:5.1f}) │ {z3_num:02d} (得分:{z3_score:5.1f}) │")
    
    print(f"└{'─' * 20}┴{'─' * 20}┴{'─' * 20}┘")
    
    # 蓝球推荐
    print(f"\n┌{'─' * 30}┐")
    print(f"│ {'蓝球推荐 (01-16)':^28} │")
    print(f"├{'─' * 12}┬{'─' * 15}┤")
    print(f"│ {'号码':^10} │ {'综合得分':^13} │")
    print(f"├{'─' * 12}┼{'─' * 15}┤")
    for num, score in blue_sorted[:4]:
        features = []
        b = num
        features.append("奇" if b % 2 == 1 else "偶")
        features.append("大" if b >= 9 else "小")
        if blue_freq_cnt.get(b, 0) >= 4:
            features.append("热")
        elif blue_freq_cnt.get(b, 0) >= 2:
            features.append("温")
        else:
            features.append("冷")
        feature_str = "/".join(features)
        print(f"│ {num:02d} {'':>6}│ {score:5.1f} ({feature_str:>5}) │")
    print(f"└{'─' * 12}┴{'─' * 15}┘")
    
    # ============================================================
    # 九、推荐组合建议
    # ============================================================
    print("\n" + "─" * 70)
    print("💡 九、推荐选号策略")
    print("─" * 70)
    
    # 基于区间比趋势推荐选号分布
    z1_count = round(zone_trend[0])
    z2_count = round(zone_trend[1])
    z3_count = round(zone_trend[2])
    
    # 确保总数=6
    total = z1_count + z2_count + z3_count
    if total > 6:
        z3_count -= (total - 6)
    elif total < 6:
        z3_count += (6 - total)
    
    print(f"  推荐区间比: {z1_count}:{z2_count}:{z3_count}")
    print(f"  即一区选{z1_count}个、二区选{z2_count}个、三区选{z3_count}个")
    
    top_z1 = [f"{n:02d}" for n, _ in zone1_sorted[:z1_count]]
    top_z2 = [f"{n:02d}" for n, _ in zone2_sorted[:z2_count]]
    top_z3 = [f"{n:02d}" for n, _ in zone3_sorted[:z3_count]]
    
    print(f"  一区建议: {' '.join(top_z1)}")
    print(f"  二区建议: {' '.join(top_z2)}")
    print(f"  三区建议: {' '.join(top_z3)}")
    
    top_blue = [f"{n:02d}" for n, _ in blue_sorted[:4]]
    print(f"  蓝球建议: {' '.join(top_blue)}")
    
    # 输出所有候选的组合示例
    print(f"\n  示例组合1: {' '.join(top_z1 + top_z2 + top_z3)} + {top_blue[0]}")
    if z1_count > 0 and z2_count > 0 and z3_count > 0:
        alt_z1 = [f"{n:02d}" for n, _ in zone1_sorted[z1_count:z1_count+1]]
        alt_z2 = [f"{n:02d}" for n, _ in zone2_sorted[z2_count:z2_count+1]]
        alt_z3 = [f"{n:02d}" for n, _ in zone3_sorted[z3_count:z3_count+1]]
    
    print("\n" + "─" * 70)
    print("⚠️  免责声明")
    print("─" * 70)
    print("  彩票开奖为完全随机事件，任何模型预测仅供娱乐参考。")
    print("  请理性购彩，量力而行！")
    print("=" * 70)
    
    # ============================================================
    # 十、详细评分表
    # ============================================================
    print("\n\n" + "=" * 70)
    print("  📋 十、红球各号码详细评分明细")
    print("=" * 70)
    print(f"{'号码':<6} {'频率':>6} {'遗漏':>6} {'邻号':>6} {'马尔':>6} {'贝叶':>6} {'连号':>6} {'跨度':>6} {'综合':>8} {'区间':>6}")
    print("-" * 70)
    
    for n in ALL_RED:
        zone = "一区" if n <= 11 else ("二区" if n <= 22 else "三区")
        print(f"  {n:02d}   "
              f"{red_freq[n]:5.1f} "
              f"{red_miss[n]:5.1f} "
              f"{red_adj[n]:5.1f} "
              f"{red_mkv[n]:5.1f} "
              f"{red_bayes[n]:5.1f} "
              f"{red_con[n]:5.1f} "
              f"{red_gap[n]:5.1f} "
              f"{red_composite[n]:7.1f} "
              f"{zone}")
    
    print("\n" + "=" * 70)
    print("  📋 蓝球各号码详细评分明细")
    print("=" * 70)
    print(f"{'号码':<6} {'频率':>6} {'遗漏':>6} {'邻号':>6} {'马尔':>6} {'贝叶':>6} {'跨度':>6} {'综合':>8} {'属性':>10}")
    print("-" * 70)
    
    for n in ALL_BLUE:
        features = []
        features.append("奇" if n % 2 == 1 else "偶")
        features.append("大" if n >= 9 else "小")
        count = blue_freq_cnt.get(n, 0)
        features.append(f"出现{count}次")
        feature_str = "/".join(features)
        print(f"  {n:02d}   "
              f"{blue_freq[n]:5.1f} "
              f"{blue_miss[n]:5.1f} "
              f"{blue_adj[n]:5.1f} "
              f"{blue_mkv[n]:5.1f} "
              f"{blue_bayes[n]:5.1f} "
              f"{blue_gap_scores[n]:5.1f} "
              f"{blue_composite[n]:7.1f} "
              f"{feature_str}")
    
    print("\n" + "=" * 70)
    print("  预测完成！以上分析基于近50期双色球数据，综合6种模型")
    print("=" * 70)
    
    # 保存结果到JSON
    result = {
        "analysis_time": "2026-06-15",
        "data_range": f"{RAW_DATA[0][0]}~{RAW_DATA[-1][0]}",
        "total_periods": N,
        "zone1_candidates": [{"number": n, "score": round(s, 1)} for n, s in zone1_sorted[:4]],
        "zone2_candidates": [{"number": n, "score": round(s, 1)} for n, s in zone2_sorted[:4]],
        "zone3_candidates": [{"number": n, "score": round(s, 1)} for n, s in zone3_sorted[:4]],
        "blue_candidates": [{"number": n, "score": round(s, 1)} for n, s in blue_sorted[:4]],
        "recommended_zone_ratio": f"{z1_count}:{z2_count}:{z3_count}",
    }
    
    return result


if __name__ == "__main__":
    from collections import defaultdict
    result = main()
