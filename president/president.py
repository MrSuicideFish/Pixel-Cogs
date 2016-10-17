#  Bankheist.py was created by Redjumpman for Redbot
#  This will create a system.JSON file and a data folder
#  This will modify values your bank.json from economy.py
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

#On script initiaion we do this first
    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/president/system.json"
        self.system = dataIO.load_json(self.file_path)

#COMMANDS START HERE

    #--define the president command
    @commands.group(pass_context=True, no_pm=True)
    async def president(self, ctx):
        """General heist related commands"""

        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    #--Create the 'nominate' command
    #we write pass_context so that discord will send us info about the server that we can use
    @president.command( name="nominate", pass_context=True )
    async def _nominate_president(self):
        user = ctx.message.author
        server = ctx.message.server
        settings = self.check_server_settings(server)

        #output a message from the bot
        await self.bot.say("I can do stuff!")


    #DEBUGGING
    @president.command(name="reset", pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def _reset_president(self,ctx):
        server = ctx.message.server
        settings = self.check_server_settings(server)
        self.
        await self.bot.say("President has been reset.")

#COMMANDS END HERE

#COG DEFINITIONS, DO NOT CHANGE ME
def setup(bot):
    bot.add_cog(president(bot))

def (self, settings):
    dataIO.save_json(self.file_path, self.system)