import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from scipy.sparse import hstack
from dashboard.models import Product


#  Prepare product data and features
def build_product_features():
    # Get all active products from your database
    products = Product.objects.filter(is_active=True)
    
    # Convert to pandas DataFrame
    df = pd.DataFrame(list(products.values('id', 'name', 'slug','description', 'category__name', 'price','cost_price', 'main_image','brand')))
    
    # Rename category column for simplicity
    df.rename(columns={'category__name': 'category_name'}, inplace=True)
    
    # Handle missing values
    df['description'] = df['description'].fillna('')
    df['brand'] = df['brand'].fillna('')
    df['category_name'] = df['category_name'].fillna('')
    df['cost_price'] = df['cost_price'].fillna(0).astype(float)


    #  TF-IDF for text (product descriptions)
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['description'])

    #  One-hot encode category + brand
    encoder = OneHotEncoder()
    cat_brand_matrix = encoder.fit_transform(df[['category_name', 'brand']])

    # Normalize price
    scaler = MinMaxScaler()
    price_scaled = scaler.fit_transform(df[['price']])

    # Combine all features together
    final_matrix = hstack([tfidf_matrix, cat_brand_matrix, price_scaled])

    return df, final_matrix



def compute_similarity():
    df, final_matrix = build_product_features()
    similarity = cosine_similarity(final_matrix)
    return df, similarity


def get_recommendations(product_id, top_n=5):
    # Get product data and similarity table
    df, similarity = compute_similarity()

    # Find the row index of the selected product
    try:
        product_idx = df[df['id'] == product_id].index[0]
    except IndexError:
        print(" Product not found!")
        return pd.DataFrame()

    # Get all similarity scores for this product
    scores = similarity[product_idx]

    # Sort products by similarity (highest first)
    similar_products = df.copy()
    similar_products['similarity'] = scores
    similar_products = similar_products.sort_values(by='similarity', ascending=False)

    # Skip itself and take top_n similar ones
    recommendations = similar_products.iloc[1:top_n+1]

    # Include slug, price, main_image so template works
    return recommendations[['id', 'name', 'slug', 'price','cost_price','main_image', 'similarity']]
