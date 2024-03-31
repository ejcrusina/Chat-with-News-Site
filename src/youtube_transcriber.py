import re
from youtube_transcript_api import YouTubeTranscriptApi


def extract_youtube_transcript(youtube_video_url):
    try:
        video_id = re.search("v=([^&]+)", youtube_video_url).group(1)
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        raise e

    transcript = ""
    for i in transcript_text:
        transcript += " " + i["text"]

    return transcript


transcript_text = extract_youtube_transcript(
    "https://www.youtube.com/watch?v=bupx08ZgSFg&list=PLNrNCqqo1fYPjWFugeeSJnlh5qfZsIjC4&index=9"
)
