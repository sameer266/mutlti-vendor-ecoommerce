import math
import re
from collections import Counter
from dashboard.models import Product


# --- Utility: Simple text vectorization using word frequency ---
def text_to_vector(text):
    """Convert text into a word frequency Counter."""
    words = re.findall(r'\w+', (text or '').lower())
    return Counter(words)


# --- Utility: Cosine similarity (no NumPy) ---
def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two text vectors."""
    if not vec1 or not vec2:
        return 0.0

    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum(vec1[x] * vec2[x] for x in intersection)

    sum1 = sum(v ** 2 for v in vec1.values())
    sum2 = sum(v ** 2 for v in vec2.values())
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if denominator == 0:
        return 0.0
    return numerator / denominator


# --- Build simplified product features ---
def build_product_features():
    """Extract and prepare product features from the database."""
    products = Product.objects.filter(is_active=True).values(
        'id', 'name', 'slug', 'description', 'category__name', 
        'price', 'cost_price', 'main_image', 'brand'
    )

    product_features = []

    for p in products:
        desc = (p.get('description') or '').lower()
        brand = (p.get('brand') or '').lower()
        category = (p.get('category__name') or '').lower()
        name = (p.get('name') or '').lower()

        # Combine text fields for similarity
        text_data = f"{name} {desc} {brand} {category}"
        vector = text_to_vector(text_data)

        product_features.append({
            'id': p['id'],
            'name': p['name'],
            'slug': p['slug'],
            'price': float(p.get('price') or 0),
            'cost_price': float(p.get('cost_price') or 0),
            'main_image': p.get('main_image'),
            'vector': vector
        })

    return product_features


# --- Compute similarity manually (no NumPy) ---
def compute_similarity():
    """Compute pairwise similarity for all active products."""
    products = build_product_features()
    n = len(products)

    # Initialize empty matrix
    similarity_matrix = [[0.0 for _ in range(n)] for _ in range(n)]

    # Compute similarity only once for each pair
    for i in range(n):
        for j in range(i + 1, n):
            sim = cosine_similarity(products[i]['vector'], products[j]['vector'])
            similarity_matrix[i][j] = sim
            similarity_matrix[j][i] = sim

    return products, similarity_matrix


# --- Get top N similar products ---
def get_recommendations(product_id, top_n=5):
    """Return top N similar products based on text similarity."""
    products, similarity_matrix = compute_similarity()

    # Find index of the selected product
    product_idx = next((i for i, p in enumerate(products) if p['id'] == product_id), None)
    if product_idx is None:
        print("⚠️ Product not found!")
        return []

    # Get all similarity scores for this product
    scores = similarity_matrix[product_idx]

    scored_products = []
    for i, score in enumerate(scores):
        if i != product_idx:  # skip itself
            scored_products.append({
                'id': products[i]['id'],
                'name': products[i]['name'],
                'slug': products[i]['slug'],
                'price': products[i]['price'],
                'cost_price': products[i]['cost_price'],
                'main_image': products[i]['main_image'],
                'similarity': round(score, 4)
            })

    # Sort by similarity (highest first)
    scored_products.sort(key=lambda x: x['similarity'], reverse=True)

    # Return top N recommendations
    return scored_products[:top_n]






# import pandas as pd
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
# from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
# from scipy.sparse import hstack
# from dashboard.models import Product


# #  Prepare product data and features
# def build_product_features():
#     # Get all active products from your database
#     products = Product.objects.filter(is_active=True)
    
#     # Convert to pandas DataFrame
#     df = pd.DataFrame(list(products.values('id', 'name', 'slug','description', 'category__name', 'price','cost_price', 'main_image','brand')))
    
#     # Rename category column for simplicity
#     df.rename(columns={'category__name': 'category_name'}, inplace=True)
    
#     # Handle missing values
#     df['description'] = df['description'].fillna('')
#     df['brand'] = df['brand'].fillna('')
#     df['category_name'] = df['category_name'].fillna('')
#     df['cost_price'] = df['cost_price'].fillna(0).astype(float)


#     #  TF-IDF for text (product descriptions)
#     tfidf = TfidfVectorizer(stop_words='english')
#     tfidf_matrix = tfidf.fit_transform(df['description'])

#     #  One-hot encode category + brand
#     encoder = OneHotEncoder()
#     cat_brand_matrix = encoder.fit_transform(df[['category_name', 'brand']])

#     # Normalize price
#     scaler = MinMaxScaler()
#     price_scaled = scaler.fit_transform(df[['price']])

#     # Combine all features together
#     final_matrix = hstack([tfidf_matrix, cat_brand_matrix, price_scaled])

#     return df, final_matrix



# def compute_similarity():
#     df, final_matrix = build_product_features()
#     similarity = cosine_similarity(final_matrix)
#     return df, similarity


# def get_recommendations(product_id, top_n=5):
#     # Get product data and similarity table
#     df, similarity = compute_similarity()

#     # Find the row index of the selected product
#     try:
#         product_idx = df[df['id'] == product_id].index[0]
#     except IndexError:
#         print(" Product not found!")
#         return pd.DataFrame()

#     # Get all similarity scores for this product
#     scores = similarity[product_idx]

#     # Sort products by similarity (highest first)
#     similar_products = df.copy()
#     similar_products['similarity'] = scores
#     similar_products = similar_products.sort_values(by='similarity', ascending=False)

#     # Skip itself and take top_n similar ones
#     recommendations = similar_products.iloc[1:top_n+1]

#     # Include slug, price, main_image so template works
#     return recommendations[['id', 'name', 'slug', 'price','cost_price','main_image', 'similarity']]
