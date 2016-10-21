#  President.py was created by MrSuicide
#  This will create a system.JSON file and a data folder
#  This will modify values your government.py
import os
import asyncio
import random
import time
import discord
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
    @president.command(name="nominate", pass_context=True, mentions=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _nominate_president(self, ctx, nominatedUser: str):
        """Nominate a president for the server"""

        user = ctx.message.author
        server = ctx.message.server
        settings = self.check_server_settings(server)

        #Get nominated member by either mention or name
        nominatedMember = self.get_nominated_member(server, nominatedUser, ctx.message.mentions)

        if nominatedMember is not None:
            if settings["Config"]["Election Started"] == "No":
                self.bot.say("Starting Election!")
                self.presidentclear(settings)
                settings["Config"]["Election Started"] = "Yes"

                self.candidates_add(nominatedMember.id, nominatedMember.nick, settings)
                self.bot.say("{0} nominated {1}".format(user, nominatedMember.nick))

                #THIS IS WHERE THE MAGIC HAPPENS
                wait = settings["Config"]["Wait Time"]
                wait_time = int(wait)
                half_time = int(wait_time)
                split_time = int(half_time / 2)

                await self.bot.say("{0} hour(s) until election is over".format( wait ))
                await asyncio.sleep(wait_time)
                await self.bot.say("{0} hour(s) until election is over".format( waitTime))
                await asyncio.sleep(half_time)
                await self.bot.say("{0} hour(s) until election is over".format( half_time))
            else:
                if has_duplicate_nominee(settings, nominatedMember.id) is not True:
                    self.candidates_add(nominatedMember.id, nominatedMember.nick, settings)
                    self.bot.say("{0} nominated {1}".format(user, nominatedMember.nick))
                else:
                    self.bot.say("{0} is already nominated!".format(nominatedMember.nick))
        else:
            await self.bot.say("Could not find user: {0}".format(nominatedUser))


                # DEBUGGING
    @president.command(name="reset", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _reset_president(self, ctx):
        """Resets president and settings to normal"""
        server = ctx.message.server
        settings = self.check_server_settings(server)
        self.presidentclear(settings)
        await self.bot.say("President has been reset.")

    #DEBUG SHOWS INFO ABOUT CONFIG
    #Delete me after final
    @president.command(name="info", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _info_president(self, ctx):
        """Shows President Config"""

        server = ctx.message.server
        settings = self.check_server_settings(server)
        await self.bot.say(settings)


    #--INTERNAL ATTR DEFINITIONS
    def get_nominated_member(self, server, nominatedUser, mentions):
    	numOfMentions = len(mentions)
    	if numOfMentions > 0:
    		return server.get_member(mentions[0].id)
		else:
			return server.get_member_named(nominatedUser)

    def has_duplicate_nominee(self, settings, memberName):
        for member in settings["Candidates"]:
            if member is memberName:
                return True

    def presidentclear(self, settings):
    	del settings["Candidates"]
    	settings["President"] = "None"
    	settings["Candidates"] = {}
    	settings["Config"]["Election Started"] = "No"
    	settings["Config"]["Time Remaining"] = 0
    	settings["Config"]["NumOfCandidates"] = 0
    	settings["Config"]["Cooldown"] = False
    	dataIO.save_json(self.file_path, self.system)

    def candidates_add(self, uid, name, settings):
        settings["Candidates"][uid] = {"Name": name, "User ID": uid}
        settings["Config"]["NumOfCandidates"] = settings["Config"]["NumOfCandidates"] + 1
        dataIO.save_json(self.file_path, self.system)

    def check_server_settings(self, server):
        if server.id not in self.system["Servers"]:
            self.system["Servers"][server.id] = {"President": "None",
                                                 "Candidates": {},
                                                 "Config": {"Election Started": "No",
                                                            "Cooldown": False, "Time Remaining": 0, "Default CD": 0,
                                                            "NumOfCandidates": 0, "Wait Time": 120},
                                                 }
            dataIO.save_json(self.file_path, self.system)
            print("Creating default president settings for Server: {}".format(server.name))
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
