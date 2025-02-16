import streamlit as st
import requests
from datetime import datetime, timedelta
from collections import Counter
import re

# YouTube API Key
API_KEY = "AIzaSyBQ8mjJS289S16LQ3IKAXyeFz_vT2ZGdNw"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("YouTube Trending Topics Analyzer")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)
min_views = st.number_input("Minimum Views:", min_value=0, value=10000)
min_subscribers = st.number_input("Minimum Subscribers:", min_value=0, value=5000)
max_videos = st.number_input("Maximum Videos on Channel:", min_value=0, value=100)
results_limit = st.slider("Number of Videos to Analyze:", 100, 5000, 1000)

# Function to extract trending topics and tags
def extract_trending_topics(description):
    # Clean and normalize text
    clean_text = re.sub(r"[^\w\s#]", "", description.lower())
    # Extract hashtags and keywords
    hashtags = re.findall(r"#(\w+)", clean_text)
    keywords = re.findall(r"\b\w{4,}\b", clean_text)
    return hashtags + keywords

# Fetch Data Button
if st.button("Analyze Trending Content"):
    try:
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []
        trending_topics = Counter()
        trending_tags = Counter()

        # Fetch popular videos without keyword search
        search_params = {
            "part": "snippet",
            "type": "video",
            "order": "viewCount",
            "publishedAfter": start_date,
            "maxResults": 50,
            "key": API_KEY,
            "regionCode": "US"
        }

        # Pagination to get more results
        total_collected = 0
        while total_collected < results_limit:
            response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
            data = response.json()
            
            if "items" not in data:
                break
                
            videos = data["items"]
            video_ids = [v["id"]["videoId"] for v in videos if "id" in v]
            channel_ids = [v["snippet"]["channelId"] for v in videos if "snippet" in v]

            # Fetch video statistics
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params={
                "part": "statistics",
                "id": ",".join(video_ids),
                "key": API_KEY
            })
            stats_data = stats_response.json()

            # Fetch channel statistics
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params={
                "part": "statistics,snippet",
                "id": ",".join(channel_ids),
                "key": API_KEY
            })
            channel_data = channel_response.json()

            # Process batch of videos
            for video, stats, channel in zip(videos, stats_data.get("items", []), channel_data.get("items", [])):
                # Extract video details
                title = video["snippet"].get("title", "")
                description = video["snippet"].get("description", "")
                video_url = f"https://youtube.com/watch?v={video['id']['videoId']}"
                
                # Extract statistics
                views = int(stats.get("statistics", {}).get("viewCount", 0))
                subs = int(channel.get("statistics", {}).get("subscriberCount", 0))
                channel_videos = int(channel.get("statistics", {}).get("videoCount", 0))

                # Apply filters
                if (views >= min_views and 
                    subs >= min_subscribers and 
                    channel_videos <= max_videos):
                    
                    all_results.append({
                        "Title": title,
                        "URL": video_url,
                        "Views": views,
                        "Subscribers": subs
                    })

                    # Extract and count topics/tags
                    topics = extract_trending_topics(f"{title} {description}")
                    filtered_topics = [t for t in topics if "sprunki" not in t.lower()]
                    trending_topics.update(filtered_topics)
                    trending_tags.update([t for t in re.findall(r"#(\w+)", description) if "sprunki" not in t.lower()])

            total_collected += len(videos)
            if "nextPageToken" in data:
                search_params["pageToken"] = data["nextPageToken"]
            else:
                break

        # Display results
        if trending_topics:
            st.success(f"Analyzed {total_collected} videos. Found {len(trending_topics)} unique topics!")
            
            # Show trending analysis
            st.subheader("Top Viral Topics")
            cols = st.columns(2)
            with cols[0]:
                st.write("**Most Frequent Keywords:**")
                for topic, count in trending_topics.most_common(20):
                    st.write(f"`{topic}` ({count})")
            
            with cols[1]:
                st.write("**Popular Hashtags:**")
                for tag, count in trending_tags.most_common(20):
                    st.write(f"`#{tag}` ({count})")

            # Raw data
            st.subheader("Raw Data Preview")
            st.dataframe(all_results[:20])
        else:
            st.warning("No trending topics found matching the criteria.")

    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
