import os

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

sns.set_theme(style='whitegrid')
BLUE, LIGHT_BLUE, RED, GREY = '#0D47A1', '#90CAF9', '#C62828', '#B0BEC5'

st.set_page_config(page_title='Olist E-Commerce Dashboard', page_icon='🛒', layout='wide')


# ---------------------------------------------------------------- Load data
@st.cache_data
def load_data():
    path = os.path.join(os.path.dirname(__file__), 'main_data.csv')
    df = pd.read_csv(path)
    for col in ['order_purchase_timestamp', 'order_delivered_customer_date', 'order_estimated_delivery_date']:
        df[col] = pd.to_datetime(df[col])
    df['revenue'] = df['price'] + df['freight_value']
    return df


# ---------------------------------------------------------------- Helper functions
def create_monthly_df(df):
    monthly = (df[df['order_status'] != 'canceled']
               .resample('ME', on='order_purchase_timestamp')
               .agg(order_count=('order_id', 'nunique'), revenue=('revenue', 'sum'))
               .reset_index())
    monthly['month'] = monthly['order_purchase_timestamp'].dt.strftime('%Y-%m')
    return monthly


def create_category_df(df):
    delivered = df[df['order_status'] == 'delivered']
    cat = (delivered.groupby('product_category_name_english')
           .agg(revenue=('revenue', 'sum'), order_count=('order_id', 'nunique'))
           .sort_values('revenue', ascending=False)
           .reset_index())
    cat['share'] = cat['revenue'] / cat['revenue'].sum() * 100
    return cat


def create_delivery_df(df):
    delivery = (df[df['order_status'] == 'delivered']
                .drop_duplicates('order_id')
                .dropna(subset=['order_delivered_customer_date'])
                .copy())
    delivery['is_late'] = delivery['order_delivered_customer_date'] > delivery['order_estimated_delivery_date']
    delivery['delivery_status'] = np.where(delivery['is_late'], 'Terlambat', 'Tepat waktu')
    delivery['delivery_days'] = (delivery['order_delivered_customer_date'] - delivery['order_purchase_timestamp']).dt.days
    return delivery


def create_rfm_df(df):
    delivered = df[df['order_status'] == 'delivered']
    snapshot = delivered['order_purchase_timestamp'].max() + pd.Timedelta(days=1)
    rfm = delivered.groupby('customer_unique_id').agg(
        recency=('order_purchase_timestamp', lambda x: (snapshot - x.max()).days),
        frequency=('order_id', 'nunique'),
        monetary=('revenue', 'sum')).reset_index()
    return rfm


# ---------------------------------------------------------------- Sidebar filter
all_df = load_data()
min_date = all_df['order_purchase_timestamp'].min().date()
max_date = all_df['order_purchase_timestamp'].max().date()

with st.sidebar:
    st.title('🛒 Olist E-Commerce')
    st.caption('Brazilian E-Commerce Public Dataset')
    date_range = st.date_input('Rentang waktu pembelian', value=[min_date, max_date],
                               min_value=min_date, max_value=max_date)
    states = sorted(all_df['customer_state'].dropna().unique())
    selected_states = st.multiselect('Negara bagian pelanggan', states, placeholder='Semua negara bagian')

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    st.warning('Pilih tanggal awal dan akhir pada sidebar.')
    st.stop()

main_df = all_df[(all_df['order_purchase_timestamp'].dt.date >= start_date) &
                 (all_df['order_purchase_timestamp'].dt.date <= end_date)]
if selected_states:
    main_df = main_df[main_df['customer_state'].isin(selected_states)]

if main_df.empty:
    st.warning('Tidak ada data untuk filter yang dipilih.')
    st.stop()

monthly_df = create_monthly_df(main_df)
category_df = create_category_df(main_df)
delivery_df = create_delivery_df(main_df)
rfm_df = create_rfm_df(main_df)

# ---------------------------------------------------------------- Header & KPI
st.title('Dashboard Analisis E-Commerce Olist')
st.caption(f'Periode {start_date:%d %b %Y} – {end_date:%d %b %Y}'
           + (f" · Negara bagian: {', '.join(selected_states)}" if selected_states else ''))

valid_df = main_df[main_df['order_status'] != 'canceled']
total_orders = valid_df['order_id'].nunique()
total_revenue = valid_df['revenue'].sum()
aov = total_revenue / total_orders if total_orders else 0
avg_review = delivery_df['review_score'].mean()
late_rate = delivery_df['is_late'].mean() * 100 if len(delivery_df) else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric('Total pesanan', f'{total_orders:,}')
k2.metric('Total revenue', f'BRL {total_revenue / 1e6:,.2f} jt')
k3.metric('Rata-rata nilai pesanan', f'BRL {aov:,.2f}')
k4.metric('Rata-rata review', f'{avg_review:.2f} ★' if not np.isnan(avg_review) else '-')
k5.metric('Pesanan terlambat', f'{late_rate:.1f}%')

tab1, tab2, tab3, tab4 = st.tabs(['📈 Tren Penjualan', '📦 Kategori Produk',
                                  '🚚 Pengiriman & Review', '👥 Pelanggan (RFM)'])

# ---------------------------------------------------------------- Tab 1: Pertanyaan 1
with tab1:
    st.subheader('Tren jumlah pesanan dan revenue bulanan')
    fig, ax1 = plt.subplots(figsize=(14, 6))
    ax1.bar(monthly_df['month'], monthly_df['revenue'] / 1e3, color=LIGHT_BLUE, label='Revenue (ribu BRL)')
    ax1.set_ylabel('Revenue (ribu BRL)')
    ax1.tick_params(axis='x', rotation=45)
    ax2 = ax1.twinx()
    ax2.plot(monthly_df['month'], monthly_df['order_count'], color=BLUE, marker='o', linewidth=2.5,
             label='Jumlah pesanan')
    ax2.set_ylabel('Jumlah pesanan')
    ax2.grid(False)
    fig.legend(loc='upper left', bbox_to_anchor=(0.07, 0.95))
    st.pyplot(fig)

    if len(monthly_df):
        peak = monthly_df.loc[monthly_df['order_count'].idxmax()]
        c1, c2 = st.columns(2)
        c1.metric('Bulan dengan pesanan terbanyak', peak['month'], f"{int(peak['order_count']):,} pesanan",
                  delta_color='off')

        rev17 = monthly_df[monthly_df['month'].between('2017-01', '2017-08')]['revenue'].sum()
        rev18 = monthly_df[monthly_df['month'].between('2018-01', '2018-08')]['revenue'].sum()
        if rev17 > 0 and rev18 > 0:
            c2.metric('Revenue Jan–Agu 2018 vs Jan–Agu 2017', f'BRL {rev18 / 1e6:,.2f} jt',
                      f'{(rev18 / rev17 - 1) * 100:.1f}% YoY')

# ---------------------------------------------------------------- Tab 2: Pertanyaan 2
with tab2:
    st.subheader('Revenue per kategori produk (pesanan delivered)')
    n = st.slider('Jumlah kategori yang ditampilkan', 5, 15, 10)

    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(20, max(6, n * 0.6)))
    top = category_df.head(n)
    bottom = category_df.tail(n).sort_values('revenue')
    sns.barplot(x=top['revenue'] / 1e3, y=top['product_category_name_english'], hue=top['product_category_name_english'],
                palette=[BLUE] + [LIGHT_BLUE] * (len(top) - 1), legend=False, ax=ax[0])
    ax[0].set_title(f'{n} Kategori dengan Revenue Tertinggi', fontsize=16)
    ax[0].set_xlabel('Revenue (ribu BRL)')
    ax[0].set_ylabel(None)

    sns.barplot(x=bottom['revenue'] / 1e3, y=bottom['product_category_name_english'],
                hue=bottom['product_category_name_english'],
                palette=[RED] + ['#EF9A9A'] * (len(bottom) - 1), legend=False, ax=ax[1])
    ax[1].set_title(f'{n} Kategori dengan Revenue Terendah', fontsize=16)
    ax[1].set_xlabel('Revenue (ribu BRL)')
    ax[1].set_ylabel(None)
    ax[1].invert_xaxis()
    ax[1].yaxis.tick_right()
    plt.tight_layout()
    st.pyplot(fig)

    c1, c2 = st.columns([1, 1])
    with c1:
        cum = category_df['share'].cumsum().reset_index(drop=True)
        n80 = int((cum < 80).sum() + 1)
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(range(1, len(cum) + 1), cum, color=BLUE, linewidth=2.5)
        ax.axhline(80, color='grey', linestyle='--')
        ax.axvline(n80, color=RED, linestyle='--')
        ax.text(n80 + 1, 40, f'{n80} kategori = 80% revenue', color=RED)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        ax.set_xlabel('Jumlah kategori')
        ax.set_ylabel('Revenue kumulatif')
        ax.set_title('Kurva Pareto Revenue')
        st.pyplot(fig)
    with c2:
        st.metric(f'Kontribusi {n} kategori teratas', f"{category_df.head(n)['share'].sum():.1f}%")
        st.dataframe(category_df.head(n).rename(columns={
            'product_category_name_english': 'Kategori', 'revenue': 'Revenue (BRL)',
            'order_count': 'Jumlah pesanan', 'share': 'Kontribusi (%)'}).round(2),
            hide_index=True)

# ---------------------------------------------------------------- Tab 3: Pertanyaan 3
with tab3:
    st.subheader('Dampak keterlambatan pengiriman terhadap review score')
    summary = delivery_df.groupby('delivery_status').agg(
        jumlah=('order_id', 'count'), review=('review_score', 'mean'), hari=('delivery_days', 'mean'))

    c1, c2, c3 = st.columns(3)
    for col, status in zip([c1, c2], ['Tepat waktu', 'Terlambat']):
        if status in summary.index:
            col.metric(f'Rata-rata review – {status}', f"{summary.loc[status, 'review']:.2f} ★",
                       f"rata-rata {summary.loc[status, 'hari']:.0f} hari kirim", delta_color='off')
    if {'Tepat waktu', 'Terlambat'} <= set(summary.index):
        c3.metric('Selisih review', f"{summary.loc['Tepat waktu', 'review'] - summary.loc['Terlambat', 'review']:.2f} poin")

    c1, c2 = st.columns(2)
    with c1:
        dist = pd.crosstab(delivery_df['review_score'], delivery_df['delivery_status'], normalize='columns') * 100
        fig, ax = plt.subplots(figsize=(8, 5))
        dist.plot(kind='bar', ax=ax, rot=0,
                  color=[BLUE if c == 'Tepat waktu' else RED for c in dist.columns])
        ax.set_title('Distribusi review score')
        ax.set_xlabel('Review score')
        ax.set_ylabel('Persentase pesanan (%)')
        ax.legend(title=None)
        st.pyplot(fig)
    with c2:
        state_df = (delivery_df.groupby('customer_state')
                    .agg(late_rate=('is_late', 'mean'), avg_review=('review_score', 'mean'),
                         orders=('order_id', 'count'))
                    .reset_index())
        state_df['late_rate'] *= 100
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(state_df['late_rate'], state_df['avg_review'], s=state_df['orders'] / state_df['orders'].max() * 800 + 20,
                   color=BLUE, alpha=0.6)
        for _, r in state_df.iterrows():
            ax.annotate(r['customer_state'], (r['late_rate'], r['avg_review']), fontsize=8, ha='center', va='center')
        ax.set_xlabel('Pesanan terlambat (%)')
        ax.set_ylabel('Rata-rata review')
        ax.set_title('Keterlambatan vs review per negara bagian\n(ukuran titik = jumlah pesanan)')
        st.pyplot(fig)

    st.subheader('Persentase pesanan terlambat per negara bagian')
    state_sorted = state_df.sort_values('late_rate', ascending=False)
    fig, ax = plt.subplots(figsize=(16, 5))
    sns.barplot(data=state_sorted, x='customer_state', y='late_rate', hue='customer_state', legend=False,
                palette=[RED if i < 5 else GREY for i in range(len(state_sorted))], ax=ax)
    ax.axhline(late_rate, color='black', linestyle='--', label=f'Rata-rata ({late_rate:.1f}%)')
    ax.set_xlabel('Negara bagian')
    ax.set_ylabel('Pesanan terlambat (%)')
    ax.legend()
    st.pyplot(fig)

# ---------------------------------------------------------------- Tab 4: RFM
with tab4:
    st.subheader('Segmentasi pelanggan berdasarkan RFM')
    c1, c2, c3 = st.columns(3)
    c1.metric('Rata-rata recency', f"{rfm_df['recency'].mean():.0f} hari")
    c2.metric('Pelanggan repeat order', f"{(rfm_df['frequency'] > 1).mean() * 100:.1f}%")
    c3.metric('Rata-rata monetary', f"BRL {rfm_df['monetary'].mean():,.2f}")

    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 7))
    for i, (col, title, color) in enumerate([('recency', 'Recency terbaik (hari)', BLUE),
                                             ('frequency', 'Frequency tertinggi', BLUE),
                                             ('monetary', 'Monetary tertinggi (BRL)', BLUE)]):
        asc = col == 'recency'
        data = rfm_df.sort_values(col, ascending=asc).head(5).copy()
        data['customer'] = data['customer_unique_id'].str[:8] + '…'
        sns.barplot(data=data, x='customer', y=col, color=color, ax=ax[i])
        ax[i].set_title(f'5 Pelanggan dengan {title}', fontsize=18)
        ax[i].set_xlabel(None)
        ax[i].set_ylabel(None)
        ax[i].tick_params(axis='x', labelsize=14, rotation=20)
    st.pyplot(fig)

    fig, ax = plt.subplots(figsize=(12, 4))
    sns.histplot(rfm_df['recency'], bins=40, color=LIGHT_BLUE, ax=ax)
    ax.set_title('Distribusi recency pelanggan')
    ax.set_xlabel('Hari sejak pembelian terakhir')
    st.pyplot(fig)

st.caption('Proyek Analisis Data · Dicoding · Dataset: Olist Brazilian E-Commerce')
