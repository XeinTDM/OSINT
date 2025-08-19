import tweepy
from typing import Dict, Any, Optional
from modules import config
from modules.core.base_scanner import BaseScanner
from modules.core.exceptions import ScannerError
from modules.core.errors import APIError, AuthenticationError
from modules.enums import ScannerNames


class SocialMediaScanner(BaseScanner):
    @property
    def name(self) -> str:
        return ScannerNames.TWITTER_PROFILE.value

    async def scan(self, username: str, bearer_token: Optional[str], **kwargs) -> Dict[str, Any]:
        """Asynchronously fetches user information from the Twitter API v2."""
        self.progress.update(self.task_id, description=f"[bold yellow]Scanning Twitter profile: {username}...[/bold yellow]")

        bearer_token = bearer_token or config.Config.TWITTER_BEARER_TOKEN

        if not bearer_token:
            self.progress.update(self.task_id, description=f"[bold red]Twitter Bearer Token not provided. Skipping Twitter scan for {username}.[/bold red]")
            raise AuthenticationError("Twitter Bearer Token not provided.", self.name)

        try:
            client = tweepy.AsyncClient(bearer_token=bearer_token)
            response = await client.get_user(
                username=username,
                user_fields=["public_metrics", "description", "created_at", "location", "profile_image_url", "verified"],
            )

            if response.data:
                user = response.data
                public_metrics = user.public_metrics if hasattr(user, 'public_metrics') else {}
                result = {
                    "found": True,
                    "id": user.id,
                    "name": user.name,
                    "username": user.username,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "description": user.description,
                    "location": user.location,
                    "verified": user.verified,
                    "profile_image_url": user.profile_image_url,
                    "followers": public_metrics.get("followers_count", 0),
                    "following": public_metrics.get("following_count", 0),
                    "tweet_count": public_metrics.get("tweet_count", 0),
                    "listed_count": public_metrics.get("listed_count", 0),
                }
            else:
                error_message = "User not found."
                if response.errors and len(response.errors) > 0:
                    error_message = response.errors[0].get("detail", error_message)
                raise APIError(error_message, self.name)

        except tweepy.errors.TweepyException as e:
            raise APIError(f"An error occurred with the Twitter API: {e}", self.name, e)
        except Exception as e:
            raise ScannerError(f"An unexpected error occurred: {e}", self.name, e)
        finally:
            self.progress.update(self.task_id, advance=1)

        self.progress.update(self.task_id, description=f"[bold green]Twitter profile scan for {username} complete.[/bold green]")
        return result