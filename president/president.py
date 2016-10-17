import discord
from discord.ext import commands

class president:
    """My custom cog that does stuff!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def mycom(self):
        """This does stuff!"""

        #Your code will go here
        await self.bot.say("I can do stuff!")

def setup(bot):
    check_folders()
    check_files()
    n = president(bot)
    bot.add_cog(n)