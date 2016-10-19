#  President.py was created by MrSuicide
#  This will create a system.JSON file and a data folder
#  This will modify values your government.py
import os
import asyncio
import random
import time
from operator import itemgetter
from discord.ext import commands
from .utils.dataIO import dataIO
from random import randint
from .utils import checks
from __main__ import send_cmd_help
try:   # Check if Tabulate is installed
    from tabulate import tabulate
    tabulateAvailable = True
except:
    tabulateAvailable = False


class president:
    """Run for Prez of your discord server"""

    # On script initiaion we do this first
    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/president/system.json"
        self.system = dataIO.load_json(self.file_path)

        # COMMANDS START HERE

    #--define the president command
    @commands.group(pass_context=True, no_pm=True)
    async def president(self, ctx):
        """General president related commands"""

        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    #--Create the 'nominate' command
    # we write pass_context so that discord will send us info about the server
    # that we can use
    @president.command(name="nominate", pass_context=True)
    async def _nominate_president(self, ctx):
        user = ctx.message.author
        server = ctx.message.server
        settings = self.check_server_settings(server)
        # output a message from the bot
        await self.bot.say("I can do stuff!")

    # DEBUGGING
    @president.command(name="reset", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _reset_president(self, ctx):
        server = ctx.message.server
        settings = self.check_server_settings(server)
        self.presidentclear(settings)
        await self.bot.say("President has been reset.")

    def presidentclear(self, settings):
        dataIO.save_json(self.file_path, self.system)

    def check_server_settings(self, server):
        if server.id not in self.system["Servers"]:
            self.system["Servers"][server.id] = {"President": {},
                                                 "Config": {"Election Started": "No",
                                                            "Cooldown": False, "Time Remaining": 0, "Default CD": 0,
                                                            "Bankheist Running": "No", "Players": 0,
                                                            "Wait Time": 120},
                                                 }
            dataIO.save_json(self.file_path, self.system)
            print("Creating default heist settings for Server: {}".format(server.name))
            path = self.system["Servers"][server.id]
            return path
        else:
            path = self.system["Servers"][server.id]
            return path

    def check_folders():
        if not os.path.exists("data/president"):
            print("Creating president folder...")
            os.makedirs("data/president")

    def check_files():
        default = {"Servers": {}}
        f = "data/president/system.json"
        if not dataIO.is_valid_json(f):
            print("Making president .json...")
            dataIO.save_json(f, default)

    def setup(bot):
        check_folders()
        check_files()
        n = president(bot)
        bot.add_cog(n)
