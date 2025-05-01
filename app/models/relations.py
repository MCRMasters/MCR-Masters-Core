from sqlmodel import Relationship

from app.models.room import Room
from app.models.room_user import RoomUser
from app.models.user import User
from app.models.user_character import UserCharacter

User.room_user = Relationship(sa_relationship=RoomUser, back_populates="user")
Room.room_users = Relationship(sa_relationship=RoomUser, back_populates="room")
RoomUser.user = Relationship(sa_relationship=User, back_populates="room_user")
RoomUser.room = Relationship(sa_relationship=Room, back_populates="room_users")

User.character = Relationship(
    sa_relationship_kwargs={"foreign_keys": [User.character_code]}
)

User.owned_characters = Relationship(link_model=UserCharacter)

RoomUser.character = Relationship(
    sa_relationship_kwargs={"foreign_keys": [RoomUser.character_code]}
)
