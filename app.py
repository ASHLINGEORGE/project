from flask import Flask, render_template, jsonify, send_from_directory
import pandas as pd
from collections import defaultdict, Counter
import plotly.express as px
import json
from wordcloud import WordCloud
import os
import re

app = Flask(__name__)

COUNTRY_COORDS = {
    'AU': [-25.2744, 133.7751], 'BE': [50.8503, 4.3517], 'BR': [-14.2350, -51.9253],
    'CA': [56.1304, -106.3468], 'CH': [46.8182, 8.2275], 'CN': [35.8617, 104.1954],
    'CZ': [49.8175, 15.4730], 'DE': [51.1657, 10.4515], 'ES': [40.4637, -3.7492],
    'FR': [46.6034, 1.8883], 'GB': [55.3781, -3.4360], 'IT': [41.8719, 12.5674],
    'NL': [52.3676, 4.9041], 'SE': [60.1282, 18.6435], 'US': [37.0902, -95.7129]
}

COUNTRY_REMAP = {
    'EU': 'FR', 'WW': 'US', 'N. AMERICA': 'US', 'S. AMERICA': 'BR', 'ASIA': 'CN'
}

stopwords = set([
    'the', 'a', 'an', 'from', 'to', 'with', 'and', 'of', 'for', 'in', 'on',
    'by', 'is', 'this', 'that', 'at', 'offer', 'gr', 'g', 'mg'
])

@app.route('/')
def dashboard():
    return render_template('map.html')

@app.route('/data')
def ship_data():
    df = pd.read_csv('data/cleaned_dataset.csv')
    country_tx = defaultdict(int)

    for _, row in df.iterrows():
        origin = str(row['ships_from']).strip().upper()
        tx_count = int(row['successful_transactions']) if not pd.isna(row['successful_transactions']) else 0
        origin_mapped = COUNTRY_REMAP.get(origin, origin)
        if origin_mapped in COUNTRY_COORDS:
            country_tx[origin_mapped] += tx_count

    tx_list = [
        {"country": c, "coords": COUNTRY_COORDS[c], "tx": t} for c, t in country_tx.items()
    ]
    return jsonify({"transactions": tx_list})

@app.route('/vendor-ratings')
def vendor_ratings():
    df = pd.read_csv('data/cleaned_dataset.csv')
    rating_df = df.groupby('vendor_name')['rating'].mean().reset_index().sort_values(by='rating', ascending=False)
    fig = px.bar(rating_df, x='vendor_name', y='rating', title='Average Vendor Ratings')
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/generate-wordcloud')
def generate_wordcloud():
    df = pd.read_csv('data/cleaned_dataset.csv')
    text = ' '.join(df['product_title'].dropna()).lower()
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    path = 'static/wordcloud.png'
    wordcloud.to_file(path)
    return jsonify({'wordcloud_image': path})

@app.route('/title_words')
def title_words():
    df = pd.read_csv('data/cleaned_dataset.csv')
    df = df[df['successful_transactions'].fillna(0).astype(int) > 0]  # ✅ filter only successful ones
    titles = df['product_title'].dropna().astype(str).str.lower()
    words = []

    for title in titles:
        tokens = re.findall(r'\b[a-zA-Z]{3,}\b', title)
        filtered = [w for w in tokens if w not in stopwords]
        words.extend(filtered)

    freq = Counter(words).most_common(50)
    return jsonify(freq)

@app.route('/static/<path:filename>')
def serve_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)

if __name__ == '__main__':
    app.run(debug=True)
