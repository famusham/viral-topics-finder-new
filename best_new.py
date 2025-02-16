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
st.title("YouTube Viral Topics Tool")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)
min_views = st.number_input("Minimum Views:", min_value=0, value=1000)
min_subscribers = st.number_input("Minimum Subscribers:", min_value=0, value=1000)
max_videos = st.number_input("Maximum Videos on Channel:", min_value=0, value=50)

# List of broader keywords related to Sprunki and Incredibox
keywords = [
    "sprunki", "incredibox sprunki", "sprunki mods", "best sprunki",
    "sprunki gameplay", "sprunki tutorial", "sprunki review", "sprunki demo",
    "sprunki music", "sprunki beats", "sprunki modding", "sprunki custom",
    "sprunki update", "sprunki new version", "sprunki tips", "sprunki tricks",
    "sprunki how to", "sprunki guide", "sprunki walkthrough", "sprunki latest",
    "sprunki download", "sprunki install", "sprunki setup", "sprunki features",
    "sprunki comparison", "sprunki vs incredibox", "sprunki community",
    "sprunki fan made", "sprunki creations", "sprunki remix", "sprunki challenge"
]

# Function to extract trending topics and tags
def extract_trending_topics(description):
    # Extract hashtags and common phrases
    hashtags = re.findall(r"#(\w+)", description)
    words = re.findall(r"\b\w{4,}\b", description.lower())
    return hashtags + words

# Fetch Data Button
if st.button("Fetch Data"):
    try:
        # Calculate date range
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []
        trending_topics = Counter()
        trending_tags = Counter()

        # Iterate over the list of keywords
        for keyword in keywords:
            st.write(f"Searching for keyword: {keyword}")

            # Define search parameters
            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": start_date,
                "maxResults": 10,  # Increase to get more results
                "key": API_KEY,
            }

            # Fetch video data
            response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
            data = response.json()

            # Check if "items" key exists
            if "items" not in data or not data["items"]:
                st.warning(f"No videos found for keyword: {keyword}")
                continue

            videos = data["items"]
            video_ids = [video["id"]["videoId"] for video in videos if "id" in video and "videoId" in video["id"]]
            channel_ids = [video["snippet"]["channelId"] for video in videos if "snippet" in video and "channelId" in video["snippet"]]

            if not video_ids or not channel_ids:
                st.warning(f"Skipping keyword: {keyword} due to missing video/channel data.")
                continue

            # Fetch video statistics
            stats_params = {"part": "statistics", "id": ",".join(video_ids), "key": API_KEY}
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()

            if "items" not in stats_data or not stats_data["items"]:
                st.warning(f"Failed to fetch video statistics for keyword: {keyword}")
                continue

            # Fetch channel statistics
            channel_params = {"part": "statistics,snippet", "id": ",".join(channel_ids), "key": API_KEY}
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()

            if "items" not in channel_data or not channel_data["items"]:
                st.warning(f"Failed to fetch channel statistics for keyword: {keyword}")
                continue

            stats = stats_data["items"]
            channels = channel_data["items"]

            # Collect results
            for video, stat, channel in zip(videos, stats, channels):
                title = video["snippet"].get("title", "N/A")
                description = video["snippet"].get("description", "")[:200]
                video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                views = int(stat["statistics"].get("viewCount", 0))
                subs = int(channel["statistics"].get("subscriberCount", 0))
                channel_video_count = int(channel["statistics"].get("videoCount", 0))

                # Apply filters
                if (views >= min_views and subs >= min_subscribers and channel_video_count <= max_videos):
                    all_results.append({
                        "Title": title,
                        "Description": description,
                        "URL": video_url,
                        "Views": views,
                        "Subscribers": subs,
                        "Channel Videos": channel_video_count
                    })

                    # Extract trending topics and tags
                    topics = extract_trending_topics(description)
                    trending_topics.update(topics)
                    trending_tags.update(re.findall(r"#(\w+)", description))

        # Display results
        if all_results:
            st.success(f"Found {len(all_results)} results across all keywords!")
            st.write("### Filtered Results:")
            for result in all_results:
                st.markdown(
                    f"**Title:** {result['Title']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**URL:** [Watch Video]({result['URL']})  \n"
                    f"**Views:** {result['Views']}  \n"
                    f"**Subscribers:** {result['Subscribers']}  \n"
                    f"**Channel Videos:** {result['Channel Videos']}"
                )
                st.write("---")

            # Display trending topics and tags
            st.write("### Trending Topics and Tags:")
            st.write("**Top 10 Trending Topics:**")
            for topic, count in trending_topics.most_common(10):
                st.write(f"- {topic} (Count: {count})")

            st.write("**Top 10 Trending Tags:**")
            for tag, count in trending_tags.most_common(10):
                st.write(f"- #{tag} (Count: {count})")

        else:
            st.warning("No results found based on the applied filters.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
