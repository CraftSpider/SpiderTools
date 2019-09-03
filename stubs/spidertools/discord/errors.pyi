"""
    Talos errors stub file
"""

from typing import Union, Any
import discord
import discord.ext.commands as commands

class NotRegistered(commands.CommandError):

    user: Union[discord.User, discord.Member]

    def __init__(self, message: Union[discord.Member, discord.User], *args: Any) -> None: ...

class CustomCommandError(commands.CommandError):
    pass

class StopEventLoop(Exception):

    message: str

    def __init__(self, message: str = ...) -> None: ...
