import requests
import pandas as pd
from datetime import datetime
import time
import re

def search_reddit_api(query, limit=100, max_posts=1000):
    """Search Reddit using their API with pagination to get exact MiN NEW YORK results"""
    url = "https://www.reddit.com/search.json"
    
    headers = {
        'User-Agent': 'MyRedditScraper/1.0'
    }
    
    all_posts = []
    after = None
    
    exact_query = f'"{query}"'
    
    while len(all_posts) < max_posts:
        params = {
            'q': exact_query,
            'limit': limit,
            'sort': 'relevance',
            'raw_json': 1,
            'restrict_sr': False,
            'type': 'link'
        }
        
        if after:
            params['after'] = after
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            children = data['data']['children']
            if not children:
                break
                
            for post in children:
                post_data = post['data']
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')
                
                if is_min_new_york_specific(title, selftext):
                    all_posts.append({
                        'title': title,
                        'subreddit': post_data.get('subreddit', ''),
                        'author': post_data.get('author', ''),
                        'score': post_data.get('score', 0),
                        'comments': post_data.get('num_comments', 0),
                        'created_utc': datetime.fromtimestamp(post_data.get('created_utc', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                        'url': f"https://reddit.com{post_data.get('permalink', '')}",
                        'domain': post_data.get('domain', ''),
                        'is_self': post_data.get('is_self', False),
                        'over_18': post_data.get('over_18', False),
                        'selftext': selftext[:1000],
                        'link_flair_text': post_data.get('link_flair_text', ''),
                        'post_id': post_data.get('id', ''),
                        'permalink': post_data.get('permalink', '')
                    })
                    print(f" ACCEPTED: {title[:70]}...")
                else:
                    print(f" REJECTED: {title[:70]}...")
            
            after = data['data'].get('after')
            if not after:
                break
                
            time.sleep(1)
            
        except requests.RequestException as e:
            print(f"API Error: {e}")
            break
    
    return all_posts

def is_min_new_york_specific(title, selftext):
    """STRICT validation to ensure it's ONLY about MiN NEW YORK"""
    title_lower = title.lower()
    selftext_lower = selftext.lower()
    
    exact_matches = [
        "min new york",
        "minnewyork",
        "min-ny", 
        "min_ny",
        "min ny",
        "m.i.n. new york",
        "m.i.n. ny"
    ]
    
    reject_patterns = [
        r'\d+[-_]?min',  
        r'minute',      
        r'\d+ mins',    
        r'time',         
        r'hour',         
        r'duration',     
    ]
    
    for pattern in reject_patterns:
        if re.search(pattern, title_lower) or re.search(pattern, selftext_lower):
            return False
    
    for match in exact_matches:
        if match in title_lower or match in selftext_lower:
            return True
    
    return False

def get_post_comments(post_permalink, max_comments=500):
    """Get all comments for a specific post"""
    url = f"https://www.reddit.com{post_permalink}.json"
    
    headers = {
        'User-Agent': 'MyRedditScraper/1.0'
    }
    
    comments_data = []
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if len(data) > 1:
            comments = data[1]['data']['children']
            
            for comment in comments:
                if comment['kind'] == 't1':
                    comment_data = comment['data']
                    comments_data.append({
                        'comment_id': comment_data.get('id', ''),
                        'author': comment_data.get('author', ''),
                        'body': comment_data.get('body', ''),
                        'score': comment_data.get('score', 0),
                        'created_utc': datetime.fromtimestamp(comment_data.get('created_utc', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                        'permalink': f"https://reddit.com{comment_data.get('permalink', '')}",
                        'is_submitter': comment_data.get('is_submitter', False),
                        'parent_id': comment_data.get('parent_id', '')
                    })
                    
                    if len(comments_data) >= max_comments:
                        break
        
        time.sleep(0.5)
        
    except requests.RequestException as e:
        print(f"Error fetching comments: {e}")
    
    return comments_data

def get_detailed_reddit_data():
    """Get comprehensive Reddit data ONLY for exact MiN NEW YORK"""
    query = "MiN NEW YORK"
    print(f" Searching STRICTLY for '{query}' posts...")
    print(" Will reject 30-min, 15-min, etc. unrelated posts\n")
    
    posts = search_reddit_api(query, limit=100, max_posts=1000)
    
    if not posts:
        print("No exact MiN NEW YORK posts found")
        return None, None
    
    print(f"\n Found {len(posts)} specific MiN NEW YORK posts. Fetching comments...")
    
    all_comments = []
    
    for i, post in enumerate(posts):
        print(f" Fetching comments {i+1}/{len(posts)}: {post['title'][:50]}...")
        
        comments = get_post_comments(post['permalink'])
        for comment in comments:
            comment['post_id'] = post['post_id']
            comment['post_title'] = post['title']
            comment['subreddit'] = post['subreddit']
            all_comments.append(comment)
        
        if (i + 1) % 5 == 0:
            print(f" Progress: {i+1}/{len(posts)} posts, {len(all_comments)} comments")
    
    return posts, all_comments

def save_to_excel(posts, comments, filename_prefix="Exact_MiN_NEW_YORK"):
    """Save only exact MiN NEW YORK posts to Excel"""
    if posts:
        posts_df = pd.DataFrame(posts)
        comments_df = pd.DataFrame(comments) if comments else pd.DataFrame()
        
        posts_df = posts_df.sort_values('score', ascending=False)
        
        with pd.ExcelWriter(f"{filename_prefix}_reddit_data.xlsx") as writer:
            posts_df.to_excel(writer, sheet_name='Posts', index=False)
            if not comments_df.empty:
                comments_df.to_excel(writer, sheet_name='Comments', index=False)
        
        print(f"\n Saved to {filename_prefix}_reddit_data.xlsx")
        
        print(f"\n=== EXACT MiN NEW YORK RESULTS ===")
        print(f" Total exact posts: {len(posts)}")
        print(f" Total comments: {len(comments)}")
        print(f" Date range: {posts_df['created_utc'].min()} to {posts_df['created_utc'].max()}")
        print(f"  Subreddits: {posts_df['subreddit'].value_counts().to_dict()}")
        
        print(f"\n Sample posts (exact matches only):")
        for i, post in enumerate(posts_df.head().itertuples()):
            print(f"  {i+1}. {post.title[:80]}...")
    
    else:
        print("No exact MiN NEW YORK data to save")

if __name__ == "__main__":
    posts, comments = get_detailed_reddit_data()
    
    if posts:
        save_to_excel(posts, comments, "Exact_MiN_NEW_YORK")
        
        posts_df = pd.DataFrame(posts)
        print(f"\n Top MiN NEW YORK Posts:")
        top_posts = posts_df.nlargest(5, 'comments')[['title', 'comments', 'score', 'subreddit']]
        print(top_posts.to_string(index=False))
        
    else:
        print(" No exact MiN NEW YORK posts found!")