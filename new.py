import streamlit as st
import requests
from datetime import datetime, timedelta
import time

# Configure API key through Streamlit secrets
API_KEY = st.secrets["AIzaSyBQ8mjJS289S16LQ3IKAXyeFz_vT2ZGdNw"]

# API endpoints
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Configure app title and description
st.title("🎵 Sprunki Mod Viral Tracker")
st.markdown("Track fan-created content and community engagement for the Sprunki Incredibox Mod")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Search Parameters")
    MAX_SUBSCRIBERS = st.slider("Maximum Channel Subscribers", 1000, 100000, 5000, 1000)
    RESULTS_PER_KEYWORD = st.slider("Results per Keyword", 1, 10, 5)
    DAYS_TO_SEARCH = st.selectbox("Search Window", [7, 14, 21, 30], index=0)
    
    st.markdown("---")
    st.markdown("**Sprunki Keywords:**")
    st.caption("Tracking these fan-created content themes:")

# Curated Sprunki keywords
DEFAULT_KEYWORDS = [
    "Unleash Your Sound: Sprunki – A Love Letter to Incredibox Fans",
    "Sprunki Mod: Where Incredibox Fans Become Creators",
    "Custom Beats, Infinite Feels: Meet the Sprunki Incredibox Mod",
    "Sprunki – Crafted by Fans, Inspired by Incredibox Magic",
    "Beyond the Original: Sprunki's Fan-Made Beatbox Revolution",
    "Sprunki Mod: Remix Your Rhythm with the Incredibox Community",
    "Fan Art Meets Music: Dive into Sprunki's Incredibox Universe",
    "Sprunki: The Ultimate Fan-Crafted Spin on Incredibox",
    "Join the Groove – Sprunki, By the Fans, For the Fans!",
    "Incredibox Mod Tutorial Sprunki",
    "Sprunki Mod Gameplay",
    "Sprunki Beatmaking Community"
]

# Keyword management
with st.expander("🔍 Customize Search Keywords"):
    user_keywords = st.text_area("Add custom search terms (comma-separated):", 
                               help="Combine specific phrases with general tags for best results")
    keywords = DEFAULT_KEYWORDS + [k.strip() for k in user_keywords.split(",") if k.strip()]

def safe_get(data, *keys, default="N/A"):
    """Safely retrieve nested dictionary values with error handling"""
    for key in keys:
        try:
            data = data[key]
        except (KeyError, TypeError, IndexError):
            return default
    return data

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_youtube_data(url, params):
    """Optimized API fetcher with cache and error handling"""
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

if st.button("🚀 Launch Community Scan"):
    if not API_KEY:
        st.error("YouTube API key not configured!")
        st.stop()

    start_date = (datetime.utcnow() - timedelta(days=DAYS_TO_SEARCH)).isoformat("T") + "Z"
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, keyword in enumerate(keywords):
        try:
            # Update progress
            progress = (idx + 1) / len(keywords)
            progress_bar.progress(progress)
            status_text.markdown(f"🔎 Scanning: _{keyword}_")

            # Search parameters
            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": start_date,
                "maxResults": RESULTS_PER_KEYWORD,
                "key": API_KEY,
                "relevanceLanguage": "en",
                "videoCategoryId": "20"  # Gaming category
            }

            # Execute search
            search_data = fetch_youtube_data(YOUTUBE_SEARCH_URL, search_params)
            if not search_data or not search_data.get("items"):
                continue

            # Process results
            video_ids = [item["id"]["videoId"] for item in search_data["items"] if item.get("id")]
            channel_ids = [item["snippet"]["channelId"] for item in search_data["items"] if item.get("snippet")]

            # Batch get video stats
            video_stats = fetch_youtube_data(YOUTUBE_VIDEO_URL, {
                "part": "statistics",
                "id": ",".join(video_ids),
                "key": API_KEY
            }) or {}

            # Batch get channel stats
            channel_stats = fetch_youtube_data(YOUTUBE_CHANNEL_URL, {
                "part": "statistics",
                "id": ",".join(channel_ids),
                "key": API_KEY
            }) or {}

            # Create results
            for item in search_data["items"]:
                video_id = safe_get(item, "id", "videoId")
                channel_id = safe_get(item, "snippet", "channelId")
                
                # Find matching statistics
                video_stat = next((v for v in video_stats.get("items", []) 
                                 if v["id"] == video_id), {})
                channel_stat = next((c for c in channel_stats.get("items", [])
                                   if c["id"] == channel_id), {})

                subs = int(safe_get(channel_stat, "statistics", "subscriberCount", default=0))
                if subs > MAX_SUBSCRIBERS:
                    continue

                results.append({
                    "keyword": keyword,
                    "title": safe_get(item, "snippet", "title"),
                    "url": f"https://youtu.be/{video_id}",
                    "views": int(safe_get(video_stat, "statistics", "viewCount", default=0)),
                    "likes": int(safe_get(video_stat, "statistics", "likeCount", default=0)),
                    "comments": int(safe_get(video_stat, "statistics", "commentCount", default=0)),
                    "channel": safe_get(item, "snippet", "channelTitle"),
                    "subscribers": subs,
                    "published": safe_get(item, "snippet", "publishedAt")[:10]
                })

            time.sleep(0.3)  # Rate limit protection

        except Exception as e:
            st.error(f"Error processing '{keyword}': {str(e)}")
            continue

    # Display results
    progress_bar.empty()
    status_text.empty()
    
    if results:
        st.success(f"🎉 Found {len(results)} Sprunki-related videos!")
        
        # Sort by virality score (views + likes + comments)
        sorted_results = sorted(results, 
                             key=lambda x: x["views"] + x["likes"]*10 + x["comments"]*20, 
                             reverse=True)

        # Display results grid
        cols = st.columns(2)
        for idx, result in enumerate(sorted_results):
            with cols[idx % 2]:
                with st.container(border=True):
                    st.markdown(f"### [{result['title']}]({result['url']})")
                    st.caption(f"**Channel:** {result['channel']} ({result['subscribers']} subs)")
                    
                    # Metrics row
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Views", f"{result['views']:,}")
                    col2.metric("Likes", f"{result['likes']:,}")
                    col3.metric("Comments", f"{result['comments']:,}")
                    
                    st.write(f"**Keyword Match:** `{result['keyword']}`")
                    st.write(f"**Published:** {result['published']}")
                    st.markdown("---")
    else:
        st.warning("No Sprunki-related content found. Try expanding search parameters!")

# Add footer
st.markdown("---")
st.markdown("**Sprunki Community Tracker** v1.1 | Track fan-created content across YouTube")
