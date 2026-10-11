import sys
from collections import Counter

import pandas as pd
import streamlit as st

from streamlib import PCSA, BloomFilter, CountMinSketch, HyperLogLog, generate_stream
from streamlib.source import aggregate, load_events

st.set_page_config(page_title="Stream Analytics Engine", layout="wide", page_icon="📊")


@st.cache_data(show_spinner="Loading events...")
def get_events(n, seed):
    return load_events(n, seed)


st.sidebar.title("Stream Analytics Engine")
n_events = st.sidebar.select_slider("Stream length", [10000, 25000, 50000, 100000], value=50000)
seed = st.sidebar.number_input("Random seed", 0, 10_000, 42)
events, source = get_events(n_events, seed)
st.sidebar.caption(f"Data source: **{source}**")

page = st.sidebar.radio("Module", [
    "1. Stream overview",
    "2. Live stream processing",
    "3. Bloom filter lab",
    "4. Cardinality lab (FM vs HLL)",
    "5. Heavy hitters (Count-Min)",
])
user_ids = [e["user_id"] for e in events]

if page == "1. Stream overview":
    st.title("📊 Stream overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Events", f"{len(events):,}")
    c2.metric("Distinct users (exact)", f"{len(set(user_ids)):,}")
    c3.metric("Time span", str(events[-1]["timestamp"] - events[0]["timestamp"]).split(".")[0])

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Actions")
        st.bar_chart(pd.DataFrame(aggregate("action", events), columns=["action", "count"]).set_index("action"))
    with col2:
        st.subheader("Pages")
        st.bar_chart(pd.DataFrame(aggregate("page", events), columns=["page", "count"]).set_index("page"))
    st.caption("Aggregations run as a MongoDB `$group` pipeline when connected, otherwise in Python.")

    st.subheader("User activity is heavy-tailed (Zipf)")
    freq = Counter(user_ids).most_common()
    st.line_chart(pd.DataFrame({"events per user": [c for _, c in freq]}), x_label="user rank", y_label="events")
    st.dataframe(pd.DataFrame(events[:200]), use_container_width=True, height=250)

elif page == "2. Live stream processing":
    st.title("⚡ Live stream processing")
    st.write("Events are consumed in micro-batches. All sketches update in a single pass; the exact set is "
             "kept only to show the ground truth.")
    batch = st.slider("Micro-batch size", 500, 5000, 2000, step=500)
    if st.button("▶ Start stream"):
        pcsa, hll = PCSA(256), HyperLogLog(10)
        bloom = BloomFilter(max(1, len(set(user_ids))), 0.01)
        cms = CountMinSketch(epsilon=0.001, top_k=5)
        exact, history, returning = set(), [], 0

        m1, m2, m3, m4 = [col.empty() for col in st.columns(4)]
        chart, table, bar = st.empty(), st.empty(), st.progress(0.0)
        for start in range(0, len(user_ids), batch):
            for uid in user_ids[start:start + batch]:
                pcsa.add(uid)
                hll.add(uid)
                cms.add(uid)
                returning += bloom.add(uid)
                exact.add(uid)
            processed = min(start + batch, len(user_ids))
            history.append({"events": processed, "Exact": len(exact),
                            "FM-PCSA": pcsa.estimate(), "HyperLogLog": hll.estimate()})
            m1.metric("Events processed", f"{processed:,}")
            m2.metric("Distinct (HLL)", f"{hll.estimate():,}", f"{(hll.estimate() - len(exact)) / len(exact):+.1%} vs exact")
            m3.metric("Returning visits (Bloom)", f"{returning:,}")
            m4.metric("Sketch memory", f"{(pcsa.memory_bytes + hll.memory_bytes + bloom.memory_bytes) / 1024:.1f} KB")
            chart.line_chart(pd.DataFrame(history).set_index("events"))
            table.dataframe(pd.DataFrame(cms.heavy_hitters(), columns=["Top users (Count-Min)", "est. events"]))
            bar.progress(processed / len(user_ids))

elif page == "3. Bloom filter lab":
    st.title("🛡️ Bloom filter lab")
    distinct = len(set(user_ids))
    c1, c2 = st.columns(2)
    n = c1.slider("Expected distinct users (n)", 1000, 100000, min(100000, max(1000, distinct)), step=1000)
    p = c2.select_slider("Target false-positive rate (p)", [0.1, 0.05, 0.01, 0.005, 0.001, 0.0001], value=0.01)
    bloom = BloomFilter(n, p)
    st.info(f"m = {bloom.size:,} bits (**{bloom.memory_bytes / 1024:.1f} KB**), k = **{bloom.hash_count}** hash functions")

    exact, new, returning, false_ret = set(), 0, 0, 0
    for uid in user_ids:
        if bloom.add(uid):
            returning += 1
            false_ret += uid not in exact
        else:
            new += 1
        exact.add(uid)
    probes = [f"absent_{i}" for i in range(20000)]
    measured = sum(x in bloom for x in probes) / len(probes)

    a, b, c, d = st.columns(4)
    a.metric("New users flagged", f"{new:,}", f"exact: {len(exact):,}", delta_color="off")
    b.metric("Returning visits", f"{returning:,}")
    c.metric("Measured FP rate", f"{measured:.3%}", f"theory {bloom.theoretical_fp_rate():.3%}", delta_color="off")
    d.metric("Memory vs exact set", f"{bloom.memory_bytes / 1024:.0f} KB", f"set: {sys.getsizeof(exact) / 1024:.0f} KB+", delta_color="off")
    if n < len(exact):
        st.warning(f"n is smaller than the real number of distinct users ({len(exact):,}), so the filter is "
                   "over-full and the FP rate exceeds the target. This is the classic sizing mistake.")

    st.subheader("Memory vs false-positive trade-off")
    rows = [{"target p": r, "memory (KB)": BloomFilter(n, r).memory_bytes / 1024} for r in
            (0.1, 0.05, 0.01, 0.005, 0.001, 0.0005, 0.0001)]
    st.line_chart(pd.DataFrame(rows).set_index("memory (KB)"))

elif page == "4. Cardinality lab (FM vs HLL)":
    st.title("🧮 Cardinality estimation: Flajolet-Martin vs HyperLogLog")
    st.write("Each configuration is run over several independent streams so the error has a spread.")
    runs = st.slider("Independent runs (seeds)", 1, 10, 5)
    if st.button("Run comparison"):
        rows = []
        prog = st.progress(0.0)
        for i, s in enumerate(range(seed, seed + runs)):
            ids = [e["user_id"] for e in generate_stream(n_events, seed=s)]
            true = len(set(ids))
            for name, sketch in [(f"PCSA m={m}", PCSA(m)) for m in (64, 256, 1024)] + \
                                [(f"HLL p={p}", HyperLogLog(p)) for p in (8, 10, 12)]:
                for u in ids:
                    sketch.add(u)
                rows.append({"config": name, "memory (B)": sketch.memory_bytes,
                             "error %": abs(sketch.estimate() - true) / true * 100,
                             "expected SE %": sketch.standard_error * 100})
            prog.progress((i + 1) / runs)
        df = pd.DataFrame(rows).groupby("config", sort=False).agg(
            memory_B=("memory (B)", "first"), mean_error=("error %", "mean"),
            std_error=("error %", "std"), expected_SE=("expected SE %", "first"))
        st.dataframe(df.round(2), use_container_width=True)
        st.bar_chart(df["mean_error"])
        st.caption("HLL reaches the same error as PCSA with far less memory (6-bit registers vs 32-bit bitmaps).")

elif page == "5. Heavy hitters (Count-Min)":
    st.title("🔥 Heavy hitters with Count-Min Sketch")
    eps = st.select_slider("ε (error as a fraction of stream length)", [0.01, 0.005, 0.001, 0.0005], value=0.001)
    cms = CountMinSketch(epsilon=eps, delta=0.01, top_k=10)
    for u in user_ids:
        cms.add(u)
    exact = Counter(user_ids)
    st.info(f"Sketch: {cms.depth} × {cms.width:,} counters = **{cms.memory_bytes / 1024:.1f} KB** · "
            f"guarantee: overcount ≤ εN = {eps * len(user_ids):.0f} with prob ≥ 99%")
    df = pd.DataFrame([{"user": u, "CMS estimate": c, "exact": exact[u], "overcount": c - exact[u]}
                       for u, c in cms.heavy_hitters()])
    st.dataframe(df, use_container_width=True)
    recall = len({u for u, _ in exact.most_common(10)} & set(df.user)) / 10
    st.metric("Top-10 recall vs exact", f"{recall:.0%}")
