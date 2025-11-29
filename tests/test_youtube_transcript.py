"""
Test file for youtube-transcript-api
Based on: https://github.com/jdepoix/youtube-transcript-api
"""
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter, TextFormatter, WebVTTFormatter, SRTFormatter
import json


def test_basic_transcript_fetch():
    """Test basic transcript fetching."""
    print("=" * 80)
    print("Test 1: Basic Transcript Fetch")
    print("=" * 80)
    
    ytt_api = YouTubeTranscriptApi()
    
    # Example video ID (replace with a real video ID for testing)
    # For a video with URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
    # The video ID is: dQw4w9WgXcQ
    video_id = "OY8o5e331iM"  # Replace with your test video ID
    
    try:
        transcript = ytt_api.fetch(video_id)
        print(f"Successfully fetched transcript for video: {video_id}")
        print(f"Number of transcript entries: {len(transcript)}")
        print(f"First entry: {transcript[0] if transcript else 'No entries'}")
        return transcript
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None


def test_transcript_with_languages():
    """Test fetching transcript with specific languages."""
    print("\n" + "=" * 80)
    print("Test 2: Transcript with Specific Languages")
    print("=" * 80)
    
    ytt_api = YouTubeTranscriptApi()
    video_id = "dQw4w9WgXcQ"  # Replace with your test video ID
    
    try:
        # Try to fetch English transcript first, fallback to available languages
        transcript = ytt_api.fetch(video_id, languages=['en', 'de'])
        print(f"Successfully fetched transcript in preferred language")
        print(f"Number of transcript entries: {len(transcript)}")
        return transcript
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None


def test_list_available_transcripts():
    """Test listing all available transcripts for a video."""
    print("\n" + "=" * 80)
    print("Test 3: List Available Transcripts")
    print("=" * 80)
    
    ytt_api = YouTubeTranscriptApi()
    video_id = "dQw4w9WgXcQ"  # Replace with your test video ID
    
    try:
        transcript_list = ytt_api.list_transcripts(video_id)
        print(f"Available transcripts for video: {video_id}")
        for transcript in transcript_list:
            print(f"  - Language: {transcript.language}, Code: {transcript.language_code}")
            print(f"    Is generated: {transcript.is_generated}, Is translatable: {transcript.is_translatable}")
        return transcript_list
    except Exception as e:
        print(f"Error listing transcripts: {e}")
        return None


def test_transcript_formatters(transcript):
    """Test different transcript formatters."""
    print("\n" + "=" * 80)
    print("Test 4: Transcript Formatters")
    print("=" * 80)
    
    if not transcript:
        print("No transcript available for formatting")
        return
    
    # JSON Formatter
    json_formatter = JSONFormatter()
    json_output = json_formatter.format_transcript(transcript, indent=2)
    print("JSON Formatter (first 500 chars):")
    print(json_output[:500])
    
    # Text Formatter
    text_formatter = TextFormatter()
    text_output = text_formatter.format_transcript(transcript)
    print("\nText Formatter (first 500 chars):")
    print(text_output[:500])
    
    # WebVTT Formatter
    webvtt_formatter = WebVTTFormatter()
    webvtt_output = webvtt_formatter.format_transcript(transcript)
    print("\nWebVTT Formatter (first 500 chars):")
    print(webvtt_output[:500])
    
    # SRT Formatter
    srt_formatter = SRTFormatter()
    srt_output = srt_formatter.format_transcript(transcript)
    print("\nSRT Formatter (first 500 chars):")
    print(srt_output[:500])


def test_translated_transcript():
    """Test fetching translated transcript."""
    print("\n" + "=" * 80)
    print("Test 5: Translated Transcript")
    print("=" * 80)
    
    ytt_api = YouTubeTranscriptApi()
    video_id = "dQw4w9WgXcQ"  # Replace with your test video ID
    
    try:
        transcript_list = ytt_api.list_transcripts(video_id)
        
        # Find a transcript that can be translated
        for transcript in transcript_list:
            if transcript.is_translatable:
                print(f"Translating from {transcript.language} to German...")
                translated = transcript.translate('de')
                print(f"Translated transcript has {len(translated)} entries")
                print(f"First entry: {translated[0] if translated else 'No entries'}")
                return translated
        
        print("No translatable transcripts found")
        return None
    except Exception as e:
        print(f"Error translating transcript: {e}")
        return None


def test_save_transcript_to_file(transcript, filename="test_transcript.json"):
    """Test saving transcript to a file."""
    print("\n" + "=" * 80)
    print("Test 6: Save Transcript to File")
    print("=" * 80)
    
    if not transcript:
        print("No transcript available to save")
        return
    
    try:
        json_formatter = JSONFormatter()
        json_output = json_formatter.format_transcript(transcript, indent=2)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(json_output)
        
        print(f"Successfully saved transcript to {filename}")
    except Exception as e:
        print(f"Error saving transcript: {e}")


def main():
    """Run all tests."""
    print("YouTube Transcript API Test Suite")
    print("=" * 80)
    print("Note: Replace video_id with a real YouTube video ID for testing")
    print("=" * 80)
    
    # Test 1: Basic fetch
    transcript = test_basic_transcript_fetch()
    
    # Test 2: With languages
    test_transcript_with_languages()
    
    # Test 3: List available transcripts
    test_list_available_transcripts()
    
    # Test 4: Formatters (if we have a transcript)
    if transcript:
        test_transcript_formatters(transcript)
    
    # Test 5: Translated transcript
    test_translated_transcript()
    
    # Test 6: Save to file
    if transcript:
        test_save_transcript_to_file(transcript)
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()

