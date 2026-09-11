import os
import base64
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv
from Factline import logger


load_dotenv()

class Upload:

    def __init__(self, config):
        self.config = config

        self.scopes = [
            "https://www.googleapis.com/auth/youtube"
        ]

        self.youtube = None

    def _authenticate(self):
        creds = None

        token_b64 = os.getenv("GOOGLE_OAUTH_TOKEN")

        # Try to load existing OAuth token
        if token_b64:
            try:
                creds = pickle.loads(
                    base64.b64decode(token_b64)
                )

                # Refresh expired credentials
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())

            except Exception as e:
                logger.warning(
                    "Failed to decode or refresh GOOGLE_OAUTH_TOKEN: %s",
                    e
                )
                creds = None

        # Authenticate using browser if credentials are missing/invalid
        if not creds or not creds.valid or not token_b64:
            logger.info("Launching browser for Google OAuth...")

            flow = InstalledAppFlow.from_client_secrets_file(
                "creds.json",
                self.scopes
            )

            creds = flow.run_local_server(port=0)

            # Convert credentials to base64
            token_b64 = base64.b64encode(
                pickle.dumps(creds)
            ).decode("utf-8")

            # Save token to .env
            env_file = ".env"

            if os.path.exists(env_file):
                with open(env_file, "r") as f:
                    env_content = f.read()
            else:
                env_content = ""

            if "GOOGLE_OAUTH_TOKEN=" not in env_content:
                with open(env_file, "a") as f:
                    f.write(
                        f"\nGOOGLE_OAUTH_TOKEN={token_b64}\n"
                    )

            logger.info("Saved Google OAuth token to .env")

        return creds

    def _initialize_youtube(self):
        try:
            creds = self._authenticate()

            self.youtube = build(
                "youtube",
                "v3",
                credentials=creds
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to initialize YouTube API: %s",
                e
            )
            return False

    def _upload_video(
        self,
        file_path,
        title,
        description,
        tags=None,
        category_id="22",
        privacy_status="private"
    ):
        try:
            request_body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags or [],
                    "categoryId": category_id,
                },
                "status": {
                    "privacyStatus": privacy_status
                }
            }

            media_file = MediaFileUpload(
                file_path,
                chunksize=-1,
                resumable=True,
                mimetype="video/*"
            )

            request = self.youtube.videos().insert(
                part="snippet,status",
                body=request_body,
                media_body=media_file
            )

            response = None

            while response is None:
                status, response = request.next_chunk()

                if status:
                    logger.info(
                        "Upload progress: %d%%",
                        int(status.progress() * 100)
                    )

            video_id = response.get("id")

            logger.info(
                "Upload complete! Video ID: %s",
                video_id
            )

            return video_id

        except HttpError as e:
            logger.error(
                "YouTube API error during upload: %s",
                e
            )
            return None

        except Exception as e:
            logger.error(
                "Upload failed: %s",
                e
            )
            return None

    def _add_to_playlist(self, video_id, language):
        if not video_id:
            logger.warning(
                "Skipping playlist addition — no video ID."
            )
            return None

        try:
            english_playlist = os.getenv("ENGLISH")
            hindi_playlist = os.getenv("HINDI")

            playlist_id = (
                english_playlist
                if language.lower() == "english"
                else hindi_playlist
            )

            if not playlist_id:
                logger.warning(
                    "No playlist ID found for language: %s",
                    language
                )
                return None

            request = self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            )

            response = request.execute()

            logger.info(
                "Added video to %s playlist.",
                language
            )

            return response

        except HttpError as e:
            logger.error(
                "Failed to add video to playlist: %s",
                e
            )
            return None

        except Exception as e:
            logger.error(
                "Playlist addition error: %s",
                e
            )
            return None

    def upload(self, data, video_file, language):
        """
        Upload a video to YouTube and add it to the
        appropriate language playlist.

        Parameters
        ----------
        data : dict
            Video metadata containing:
            - video_title
            - description
            - tags

        video_file : str
            Path to the generated video.

        language : str
            Video language, e.g. "English" or "Hindi".

        Returns
        -------
        str or None
            YouTube video ID if successful.
        """

        # Check video exists
        if not os.path.exists(video_file):
            logger.error(
                "Video file not found: %s",
                video_file
            )
            return None

        # Initialize YouTube API
        if not self._initialize_youtube():
            return None

        # Extract metadata
        title = data.get(
            "video_title",
            "Untitled"
        )

        description = data.get(
            "description",
            ""
        )

        tags = data.get(
            "tags",
            []
        )

        # Upload video
        video_id = self._upload_video(
            file_path=video_file,
            title=title,
            description=description,
            tags=tags,
            category_id="25",
            privacy_status="private"
        )

        if not video_id:
            return None

        # Add uploaded video to playlist
        self._add_to_playlist(
            video_id,
            language
        )

        return video_id
