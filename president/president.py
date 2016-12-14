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
    @president.command( name="nominate", pass_context=True )
    async def _nominate_president(self, ctx):
        """Nominate a president for the server"""

        user = ctx.message.author
        server = ctx.message.server
        settings = self.check_server_settings(server)

        wait = settings["Config"]["Wait Time"]
        if not self.account_check(user):
            await self.bot.say("You need a bank account to pay for your campaign")
        elif not self.enough_points(user, server):
            await self.bot.say("You doing have enough cash to cover the cost of your campaign")
        elif not self.check_cooldowns(settings):
            s = abs(settings["Config"]["Time Remaining"])
            seconds = abs(s - settings["Config"]["Default CD"])
            time_remaining = self.time_formatting(seconds)
            await self.bot.say("A president was just nominated, another campaign cannot be started for {}".format(time_remaining))
        elif settings["Config"]["Election Started"] == "Yes":
            self.candidates_add(user, settings, server)
        elif settings["Config"]["Election Started"] == "No":
            self.candidates_add(user, settings, server)

    @president.command(name="info", pass_context=True)
    async def _info_president(self, ctx):
        """Shows presidential race information"""

        server = ctx.message.server
        settings = self.check_server_settings(server)
        await self.bot.say(settings["Config"])

    # DEBUGGING
    @president.command(name="reset", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _reset_president(self, ctx):
        """Resets president and settings to normal"""
        server = ctx.message.server
        settings = self.check_server_settings(server)
        self.presidentclear(settings)
        await self.bot.say("President has been reset.")

    #--INTERNAL ATTR DEFINITIONS

    def candidates_add(self, uid, settings, server):
        settings["Candidates"].append({"Name": server.get_member(uid).nick, "User ID": uid})
        settings["Config"]["Candidates"] = settings["Config"]["Candidates"] + 1
        dataIO.save_json(self.file_path, self.system)

    def presidentclear(self, settings):
        dataIO.save_json(self.file_path, self.system)

    def account_check(self,uid):
        bank = self.bot.get_cog('Economy').bank
        if bank.account_exists(uid):
            return True
        else:
            return False

    def enough_points(self, uid, server):
        amount = 0
        bank = self.bot.get_cog('Economy').bank
        mobj = server.get_member(uid)
        if self.account_check(mobj):
            if bank.can_spend(mobj, amount):
                return True
            else:
                return False
        else:
            return False

    def time_formatting(self, seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            msg = "```{} hours, {} minutes and {} seconds remaining```".format(h, m, s)
        elif h == 0 and m > 0:
            msg = "{} minutes, {} seconds remaining".format(m, s)
        elif m == 0 and h == 0 and s > 0:
            msg = "{} seconds remaining".format(s)
        return msg

    def check_cooldowns(self, settings):
        if settings["Config"]["Cooldown"] is False:
            return True
        elif abs(settings["Config"]["Time Remaining"] - int(time.perf_counter())) >= settings["Config"]["Default CD"]:
            return True
        elif settings["Config"]["Time Remaining"] == 0:
            return True
        else:
            return False


    def check_server_settings(self, server):
        if server.id not in self.system["Servers"]:
            self.system["Servers"][server.id] = {"President": {},
                                                 "Candidates": [],
                                                 "Config": {"Election Started": "No",
                                                            "Cooldown": False, "Time Remaining": 0, "Default CD": 0,
                                                            "Candidates": 0, "Wait Time": 120},
                                                 }
            dataIO.save_json(self.file_path, self.system)
            print("Creating default heist settings for Server: {}".format(server.name))
            path = self.system["Servers"][server.id]
            return path
        else:
            path = self.system["Servers"][server.id]
            return path

#--EXTERNAL ATTR DEFINITIONS


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
