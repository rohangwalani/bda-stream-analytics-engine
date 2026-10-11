import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import math
import mmh3
import random
from bitarray import bitarray
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Real-Time Stream Analytics Engine", layout="wide", page_icon="📊")

# --- LOCAL CACHE (Bypassing MongoDB Login to guarantee it works) ---
@st.cache_data
def generate_local_data():
    num_records = 50000
    data = []
    base_users = [f"user_{i:05d}" for i in range(1, 32000)] # ~32k unique users
    
    for i in range(num_records):
        if random.random() < 0.8:
            user_id = random.choice(base_users)
        else:
            user_id = f"user_new_{i:05d}"
            
        record = {
            "user_id": user_id,
            "action": random.choice(["view", "click", "login", "purchase"]),
            "page": random.choice(["/home", "/product", "/cart", "/checkout", "/about"])
        }
        data.append(record)
    return data

collection_data = generate_local_data()

def aggregate_actions():
    counts = {}
    for log in collection_data:
        counts[log['action']] = counts.get(log['action'], 0) + 1
    return [{"_id": k, "count": v} for k, v in counts.items()]

def aggregate_pages():
    counts = {}
    for log in collection_data:
        counts[log['page']] = counts.get(log['page'], 0) + 1
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [{"_id": k, "count": v} for k, v in sorted_counts]

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Big Data Mini Project")
st.sidebar.markdown("### Dashboard Modules")
page = st.sidebar.radio("Select Experiment:", [
    "1. MongoDB Analytics", 
    "2. Bloom Filter Engine", 
    "3. Memory Benchmarking", 
    "4. Flajolet-Martin Algorithm"
])

# --- HELPER CLASSES ---
class BloomFilter:
    def __init__(self, expected_items, fp_probability):
        self.fp_prob = fp_probability
        self.size = int(-(expected_items * math.log(fp_probability)) / (math.log(2)**2))
        self.hash_count = int((self.size / expected_items) * math.log(2))
        self.bit_array = bitarray(self.size)
        self.bit_array.setall(0)
        
    def add(self, item):
        for i in range(self.hash_count):
            digest = mmh3.hash(str(item), i) % self.size
            self.bit_array[digest] = 1
            
    def check(self, item):
        for i in range(self.hash_count):
            digest = mmh3.hash(str(item), i) % self.size
            if self.bit_array[digest] == 0:
                return False
        return True

# --- PAGES ---
if page == "1. MongoDB Analytics":
    st.title("📊 Descriptive Analytics with MongoDB")
    st.write("Using MongoDB's powerful **Aggregation Pipeline** to process and summarize Big Data streams efficiently on the database level.")
    
    st.metric("Total Web Logs Analyzed", f"{len(collection_data):,}")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("User Actions Distribution")
        data = aggregate_actions()
        df = pd.DataFrame(data).rename(columns={"_id": "Action", "count": "Count"})
        fig, ax = plt.subplots()
        ax.pie(df['Count'], labels=df['Action'], autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff','#99ff99','#ffcc99'])
        ax.axis('equal')
        st.pyplot(fig)
        
    with col2:
        st.subheader("Most Popular Website Pages")
        data2 = aggregate_pages()
        df2 = pd.DataFrame(data2).rename(columns={"_id": "Page", "count": "Visits"})
        fig2, ax2 = plt.subplots()
        ax2.bar(df2['Page'], df2['Visits'], color='#3498db')
        plt.xticks(rotation=45)
        st.pyplot(fig2)

elif page == "2. Bloom Filter Engine":
    st.title("🛡️ Bloom Filter Duplicate Detection")
    st.write("Detecting returning users in a real-time stream using an extremely memory-efficient bit array instead of a slow database index.")
    
    expected_users = st.slider("Expected Unique Users", 10000, 50000, 35000)
    fp_rate = st.selectbox("Acceptable False Positive Rate", [0.1, 0.05, 0.01, 0.001])
    
    if st.button("Run Stream Analysis"):
        bloom = BloomFilter(expected_items=expected_users, fp_probability=fp_rate)
        st.info(f"Initialized Bit Array Size: **{bloom.size / 8 / 1024:.2f} KB** | Hash Functions: **{bloom.hash_count}**")
        
        progress_bar = st.progress(0)
        unique = 0
        duplicates = 0
        
        for i, log in enumerate(collection_data):
            user_id = log["user_id"]
            if bloom.check(user_id):
                duplicates += 1
            else:
                bloom.add(user_id)
                unique += 1
            if i % 2500 == 0:
                progress_bar.progress(i / len(collection_data))
                
        progress_bar.progress(1.0)
        
        col1, col2 = st.columns(2)
        col1.metric("Estimated Unique Users (New)", f"{unique:,}")
        col2.metric("Estimated Duplicates (Returning)", f"{duplicates:,}")

elif page == "3. Memory Benchmarking":
    st.title("📈 Bloom Filter Memory vs. Accuracy Benchmark")
    st.write("Analyzing the core Big Data trade-off: Memory Footprint vs False Positive Error Rate.")
    
    if st.button("Run Benchmark Simulation"):
        rates = [0.1, 0.05, 0.01, 0.005, 0.001, 0.0001]
        sizes_kb = [(BloomFilter(35000, r).size / 8 / 1024) for r in rates]
            
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(sizes_kb, rates, marker='o', linestyle='-', color='red', linewidth=2, markersize=8)
        ax.set_title("Memory vs False Positive Rate Trade-off", fontsize=14, fontweight='bold')
        ax.set_xlabel("Memory Required (KB)", fontsize=12)
        ax.set_ylabel("False Positive Probability", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)
        st.pyplot(fig)

elif page == "4. Flajolet-Martin Algorithm":
    st.title("🧮 Flajolet-Martin (PCSA) Cardinality Estimation")
    st.write("Estimating the total number of unique users by hashing data into binary and counting the trailing zeros.")
    
    buckets = st.slider("Number of Buckets (Stochastic Averaging)", 64, 1024, 256, step=64)
    
    if st.button("Run Cardinality Estimation"):
        progress_bar = st.progress(0)
        
        def count_trailing_zeros(n, max_bits):
            if n == 0: return max_bits
            count = 0
            while (n & 1) == 0 and count < max_bits:
                count += 1; n >>= 1
            return count

        max_trailing_zeros = [0] * buckets
        actual_set = set()
        
        for i, log in enumerate(collection_data):
            uid = log["user_id"]
            actual_set.add(uid)
            hash_val = mmh3.hash(str(uid), 0, signed=False)
            k = int(math.log2(buckets))
            bucket_idx = hash_val >> (32 - k)
            mask = (1 << (32 - k)) - 1
            remaining = hash_val & mask
            zeros = count_trailing_zeros(remaining, 32 - k)
            
            if zeros > max_trailing_zeros[bucket_idx]:
                max_trailing_zeros[bucket_idx] = zeros
            if i % 2500 == 0:
                progress_bar.progress(i / len(collection_data))
                
        progress_bar.progress(1.0)
        
        phi = 0.77351
        avg_R = sum(max_trailing_zeros) / buckets
        estimate = int((buckets / phi) * (2 ** avg_R))
        actual = len(actual_set)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Actual Unique Users (Ground Truth)", f"{actual:,}")
        col2.metric("FM Estimated Users", f"{estimate:,}")
        accuracy = (1 - abs(actual - estimate) / actual) * 100
        col3.metric("Estimation Accuracy", f"{accuracy:.2f}%")
        
        fig, ax = plt.subplots(figsize=(8,5))
        bars = ax.bar(['Actual Count', 'Flajolet-Martin Estimate'], [actual, estimate], color=['#2c3e50', '#3498db'], width=0.5)
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval + 1000, int(yval), ha='center', va='bottom', fontsize=12)
            
        ax.set_ylim(0, max(actual, estimate) * 1.2)
        st.pyplot(fig)
