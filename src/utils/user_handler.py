from __future__ import annotations

import os
from typing import Optional, Union, List
from uuid import UUID

from dotenv import load_dotenv
from src.models.user import (
    UserModel, ShowcaseModel, CommentModel, VisionBoardModel,
    ShowCaseLikeModel, ShowCaseBookmarkModel, CommentUpvoteModel,
    VisionBoardTaskModel, FollowerModel
)
from supabase import AsyncClient, create_async_client

load_dotenv()


class UserHandler:
    supabase: AsyncClient

    async def init(self):
        self.supabase = await create_async_client(
            os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
        )

    # User Management Methods
    async def fetch_user(
        self,
        *,
        user_id: Union[UUID, str, None] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Optional[UserModel]:
        if user_id:
            return await self._fetch_user_by_id(user_id)

        if email and password:
            return await self._fetch_user_by_email(email, password)

    async def create_user(self, *, user: UserModel):
        payload = user.model_dump(mode="json")
        response = await self.supabase.table("users").insert(payload).execute()
        return self._parse(response.data)

    async def update_user(
        self, *, user_id: Union[UUID, str], update_payload: UserModel
    ) -> Optional[UserModel]:
        payload = update_payload.model_dump(mode="json")
        _id = payload.pop("id", user_id)
        assert _id == user_id
        response = await (
            self.supabase.table("users").update(payload).eq("id", _id).execute()
        )
        return self._parse(response.data)

    # Follower Management Methods
    async def get_followers(self, *, user_id: Union[UUID, str]) -> List[UserModel]:
        response = await (
            self.supabase.table("FollowerModel")
            .select("user_id")
            .eq("following_id", str(user_id))
            .execute()
        )
        return [UserModel(**user) for user in response.data]

    async def get_following(self, *, user_id: Union[UUID, str]) -> List[UserModel]:
        response = await (
            self.supabase.table("FollowerModel")
            .select("following_id")
            .eq("user_id", str(user_id))
            .execute()
        )
        return [UserModel(**user) for user in response.data]

    async def follow(self, following_id: Union[UUID, str], *, user_id: Union[UUID, str]):
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        if isinstance(following_id, str):
            following_id = UUID(following_id)
        data = FollowerModel(user_id=user_id, following_id=following_id)
        payload = data.model_dump(mode="json")
        await self.supabase.table("FollowerModel").insert(payload).execute()

    async def unfollow(self, following_id: Union[UUID, str], *, user_id: Union[UUID, str]):
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        if isinstance(following_id, str):
            following_id = UUID(following_id)
        await (
            self.supabase.table("FollowerModel")
            .delete()
            .eq("user_id", str(user_id))
            .eq("following_id", str(following_id))
            .execute()
        )

    # Message Methods
    async def get_message_users(self, *, user_id: Union[UUID, str]) -> List[UserModel]:
        response = await (
            self.supabase.table("messages")
            .select("DISTINCT sender_id, receiver_id")
            .or_(f"sender_id.eq.{user_id},receiver_id.eq.{user_id}")
            .execute()
        )
        return [UserModel(**user) for user in response.data]

    async def create_message(self, *, sender_id: Union[UUID, str], receiver_id: Union[UUID, str], message: str):
        payload = {
            "sender_id": str(sender_id),
            "receiver_id": str(receiver_id),
            "message": message
        }
        await self.supabase.table("messages").insert(payload).execute()

    async def get_messages(self, *, user_id: Union[UUID, str], other_user_id: Union[UUID, str], limit: int) -> List[dict]:
        response = await (
            self.supabase.table("messages")
            .select("*")
            .or_(f"sender_id.eq.{user_id},receiver_id.eq.{user_id}")
            .or_(f"sender_id.eq.{other_user_id},receiver_id.eq.{other_user_id}")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data

    # Showcase Methods
    async def get_showcases(self, *, user_id: Union[UUID, str]) -> List[ShowcaseModel]:
        response = await (
            self.supabase.table("showcases")
            .select("*")
            .eq("owner_id", str(user_id))
            .execute()
        )
        return [ShowcaseModel(**showcase) for showcase in response.data]

    async def create_showcase(self, *, showcase: ShowcaseModel, user_id: Union[UUID, str]):
        payload = showcase.model_dump(mode="json")
        payload["owner_id"] = str(user_id)
        await self.supabase.table("showcases").insert(payload).execute()

    async def get_showcase(self, *, showcase_id: Union[UUID, str]) -> Optional[ShowcaseModel]:
        response = await (
            self.supabase.table("showcases")
            .select("*")
            .eq("id", str(showcase_id))
            .execute()
        )
        return self._parse(response.data, model=ShowcaseModel)

    async def update_showcase(self, *, showcase_id: Union[UUID, str], showcase: ShowcaseModel, user_id: Union[UUID, str]):
        payload = showcase.model_dump(mode="json")
        await (
            self.supabase.table("showcases")
            .update(payload)
            .eq("id", str(showcase_id))
            .eq("owner_id", str(user_id))
            .execute()
        )

    async def delete_showcase(self, *, showcase_id: Union[UUID, str], user_id: Union[UUID, str]):
        await (
            self.supabase.table("showcases")
            .delete()
            .eq("id", str(showcase_id))
            .eq("owner_id", str(user_id))
            .execute()
        )

    # Showcase Interaction Methods
    async def like_showcase(self, *, showcase_id: Union[UUID, str], user_id: Union[UUID, str]):
        data = ShowCaseLikeModel(user_id=user_id, showcase_id=showcase_id)
        payload = data.model_dump(mode="json")
        await self.supabase.table("ShowCaseLikeModel").insert(payload).execute()

    async def unlike_showcase(self, *, showcase_id: Union[UUID, str], user_id: Union[UUID, str]):
        await (
            self.supabase.table("ShowCaseLikeModel")
            .delete()
            .eq("user_id", str(user_id))
            .eq("showcase_id", str(showcase_id))
            .execute()
        )

    async def create_comment(self, *, showcase_id: Union[UUID, str], comment: CommentModel, user_id: Union[UUID, str]):
        payload = comment.model_dump(mode="json")
        payload["author_id"] = str(user_id)
        payload["showcase_id"] = str(showcase_id)
        await self.supabase.table("comments").insert(payload).execute()

    async def upvote_comment(self, *, comment_id: Union[UUID, str], user_id: Union[UUID, str]):
        data = CommentUpvoteModel(user_id=user_id, comment_id=comment_id)
        payload = data.model_dump(mode="json")
        await self.supabase.table("CommentUpvoteModel").insert(payload).execute()

    async def remove_comment_upvote(self, *, comment_id: Union[UUID, str], user_id: Union[UUID, str]):
        await (
            self.supabase.table("CommentUpvoteModel")
            .delete()
            .eq("user_id", str(user_id))
            .eq("comment_id", str(comment_id))
            .execute()
        )

    async def bookmark_showcase(self, *, showcase_id: Union[UUID, str], user_id: Union[UUID, str]):
        data = ShowCaseBookmarkModel(user_id=user_id, showcase_id=showcase_id)
        payload = data.model_dump(mode="json")
        await self.supabase.table("ShowCaseBookmarkModel").insert(payload).execute()

    async def unbookmark_showcase(self, *, showcase_id: Union[UUID, str], user_id: Union[UUID, str]):
        await (
            self.supabase.table("ShowCaseBookmarkModel")
            .delete()
            .eq("user_id", str(user_id))
            .eq("showcase_id", str(showcase_id))
            .execute()
        )

    # Vision Board Methods
    async def get_visionboards(self, *, user_id: Union[UUID, str]) -> List[VisionBoardModel]:
        response = await (
            self.supabase.table("visionboards")
            .select("*")
            .eq("owner_id", str(user_id))
            .execute()
        )
        return [VisionBoardModel(**visionboard) for visionboard in response.data]

    async def create_visionboard(self, *, visionboard: VisionBoardModel, user_id: Union[UUID, str]):
        payload = visionboard.model_dump(mode="json")
        payload["owner_id"] = str(user_id)
        await self.supabase.table("visionboards").insert(payload).execute()

    async def update_visionboard(self, *, visionboard_id: Union[UUID, str], visionboard: VisionBoardModel, user_id: Union[UUID, str]):
        payload = visionboard.model_dump(mode="json")
        await (
            self.supabase.table("visionboards")
            .update(payload)
            .eq("id", str(visionboard_id))
            .eq("owner_id", str(user_id))
            .execute()
        )

    async def delete_visionboard(self, *, visionboard_id: Union[UUID, str], user_id: Union[UUID, str]):
        await (
            self.supabase.table("visionboards")
            .delete()
            .eq("id", str(visionboard_id))
            .eq("owner_id", str(user_id))
            .execute()
        )

    async def assign_visionboard_task(self, *, visionboard_id: Union[UUID, str], user_id: Union[UUID, str], task: VisionBoardTaskModel, assigner_id: Union[UUID, str]):
        payload = task.model_dump(mode="json")
        payload["visionboard_id"] = str(visionboard_id)
        payload["user_id"] = str(user_id)
        payload["assigner_id"] = str(assigner_id)
        await self.supabase.table("VisionBoardTaskModel").insert(payload).execute()

    async def create_visionboard_draft(self, *, visionboard_id: Union[UUID, str], user_id: Union[UUID, str]):
        await (
            self.supabase.table("visionboards")
            .update({"status": "draft"})
            .eq("id", str(visionboard_id))
            .eq("owner_id", str(user_id))
            .execute()
        )

    # Browse Methods
    async def get_nearby_artists(self, *, user_id: Union[UUID, str]) -> List[UserModel]:
        # TODO: Implement location-based search
        response = await (
            self.supabase.table("users")
            .select("*")
            .neq("id", str(user_id))
            .execute()
        )
        return [UserModel(**user) for user in response.data]

    async def get_top_rated_artists(self) -> List[UserModel]:
        response = await (
            self.supabase.table("users")
            .select("*")
            .order("rating", desc=True)
            .limit(10)
            .execute()
        )
        return [UserModel(**user) for user in response.data]

    async def get_artist_showcases(self, *, artist_id: Union[UUID, str]) -> List[ShowcaseModel]:
        response = await (
            self.supabase.table("showcases")
            .select("*")
            .eq("owner_id", str(artist_id))
            .execute()
        )
        return [ShowcaseModel(**showcase) for showcase in response.data]

    # Helper Methods
    async def _fetch_user_by_email(
        self, email: str, password: str
    ) -> Optional[UserModel]:
        response = await (
            self.supabase.table("users")
            .select("*")
            .eq("email", email)
            .eq("password", password)
            .execute()
        )
        print(response)
        return self._parse(response.data)

    async def _fetch_user_by_id(self, user_id):
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        response = await (
            self.supabase.table("users").select("*").eq("id", user_id).execute()
        )
        return self._parse(response.data)

    def _parse(self, response: list, count: int = 1, model: type = UserModel):
        if len(response) == 0:
            return None
        assert len(response) == count
        return model(**response[0])

    async def get_users_by_genre(self, genre_name: str) -> list[UserModel]:
        response = await (
            self.supabase.table("users")
            .select("*")
            .contains("genres", f'["{genre_name}"]')
            .execute()
        )
        return [UserModel(**user) for user in response.data]