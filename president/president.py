import discord
import datetime
import os
import asyncio
import re
from discord.ext import commands
from __main__ import send_cmd_help, user_allowed
from cogs.utils import checks
from cogs.utils.dataIO import dataIO
from cogs.utils.chat_formatting import box, pagify, escape_mass_mentions
from random import choice
from copy import deepcopy
from cogs.utils.settings import Settings

__author__ = "Twentysix"

settings = Settings()

class presidentError(Exception):
    pass

class Unauthorized(presidentError):
    pass

class NotFound(presidentError):
    pass

class AlreadyExists(presidentError):
    pass

class InvalidSettings(presidentError):
    pass

class president:
    """Custom presidents"""

    def __init__(self, bot):
        self.bot = bot
        self.presidents = []
        self.load_presidents()
        self.stats_task = bot.loop.create_task(self.save_stats())

    @commands.group(pass_context=True)
    async def president(self, ctx):
        """president creation commands"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @president.command(pass_context=True)
    @checks.admin_or_permissions(administrator=True)
    async def create(self, ctx, president_name : str, *, presidented_by : str):
        """Creates a president"""
        try:
            self.create_president(president_name, presidented_by, ctx)
        except AlreadyExists:
            await self.bot.say("A president with that name already exists.")
        else:
            self.save_presidents()
            await self.bot.say("president created. Entering interactive "
                               "add mode...".format(ctx.prefix))
            president = self.get_president_by_name(president_name)
            wait = await self.interactive_add_mode(president, ctx)
            self.save_presidents()

    @president.command(pass_context=True)
    @checks.admin_or_permissions(administrator=True)
    async def delete(self, ctx, president_name : str):
        """Deletes a president"""
        try:
            self.delete_president(president_name, ctx)
        except Unauthorized:
            await self.bot.say("You're not authorized to delete that president.")
        except NotFound:
            await self.bot.say("That president doesn't exist.")
        else:
            await self.bot.say("president deleted.")

    @president.command(pass_context=True)
    @checks.admin_or_permissions(administrator=True)
    async def add(self, ctx, president_name : str, *, response : str=None):
        """Adds a response to a president
        Leaving the response argument empty will enable interactive mode
        Owner only:
        Adding a response as 'file: filename.jpg' will send that file as
        response if present in data/president/files"""
        author = ctx.message.author
        president = self.get_president_by_name(president_name)

        if president is None:
            await self.bot.say("That president doesn't exist.")
            return
        if not president.can_edit(author):
            await self.bot.say("You're not allowed to edit that president.")
            return

        if response is not None:
            president.responses.append(response)
            await self.bot.say("Response added.")
        else: # Interactive mode
            await self.interactive_add_mode(president, ctx)
        self.save_presidents()

    @president.command(pass_context=True)
    @checks.admin_or_permissions(administrator=True)
    async def remove(self, ctx, president_name : str):
        """Lets you choose a response to remove"""
        author = ctx.message.author
        president = self.get_president_by_name(president_name)

        if president is None:
            await self.bot.say("That president doesn't exist.")
            return
        if president.responses == []:
            await self.bot.say("That president has no responses to delete.")
            return
        if not president.can_edit(author):
            await self.bot.say("You're not allowed to do that.")
            return

        msg = None
        current_list = None
        past_messages = []
        quit_msg = "\nType 'exit' to quit removal mode."

        while self.get_n_president_responses(president) is not None:
            r_list = self.get_n_president_responses(president, truncate=100)
            if current_list is None:
                current_list = await self.bot.say(r_list + quit_msg)
            else:
                if r_list != current_list.content:
                    await self.bot.edit_message(current_list, r_list + quit_msg)
            msg = await self.bot.wait_for_message(author=author, timeout=15)
            if msg is None:
                await self.bot.say("Nothing else to remove I guess.")
                break
            elif msg.content.lower().strip() == "exit":
                past_messages.append(msg)
                await self.bot.say("Removal mode quit.")
                break
            try:
                i = int(msg.content)
                del president.responses[i]
            except:
                pass
            past_messages.append(msg)

        if not president.responses:
            await self.bot.say("No more responses to delete.")

        past_messages.append(current_list)
        await self.attempt_cleanup(past_messages)

    async def attempt_cleanup(self, messages):
        try:
            if len(messages) > 1:
                await self.bot.delete_messages(messages)
            else:
                await self.bot.delete_message(messages[0])
        except:
            pass

    @president.command(pass_context=True)
    async def info(self, ctx, president_name : str):
        """Shows a president's info"""
        president = self.get_president_by_name(president_name)
        if president:
            msg = "Name: {}\n".format(president.name)
            owner_name = discord.utils.get(self.bot.get_all_members(), id=president.owner)
            owner_name = owner_name if owner_name is not None else "not found"
            msg += "Owner: {} ({})\n".format(owner_name, president.owner)
            president_type = "all responses" if president.type == "all" else "random response"
            msg += "Type: {}\n".format(president_type)
            influence = "server" if president.server is not None else "global"
            msg += "Influence: {}\n".format(influence)
            cs = "yes" if president.case_sensitive else "no"
            msg += "Case Sensitive: {}\n".format(cs)
            regex = "yes" if president.regex else "no"
            msg += "Regex: {}\n".format(regex)
            msg += "Cooldown: {} seconds\n".format(president.cooldown)
            msg += "presidented By: \"{}\"\n".format(president.presidented_by.replace("`", "\\`"))
            msg += "Payload: {} responses\n".format(len(president.responses))
            msg += "presidented: {} times\n".format(president.presidented)
            await self.bot.say(box(msg, lang="xl"))
        else:
            await self.bot.say("There is no president with that name.")

    @president.command(pass_context=True)
    async def show(self, ctx, president_name : str):
        """Shows all responses of a president"""
        president = self.get_president_by_name(president_name)
        if president:
            payload = self.elaborate_payload(president.responses, truncate=9999)
            if payload:
                payload = "\n\n".join(payload)
                if len(payload) > 2000:
                    for page in pagify(payload, delims=[" "]):
                        await self.bot.whisper(page)
                else:
                    await self.bot.say(payload)
            else:
                await self.bot.say("That president has no responses.")
        else:
            await self.bot.say("That president doesn't exist.")

    @president.command(name="list", pass_context=True)
    async def _list(self, ctx, president_type="local"):
        """Lists local / global presidents
        Defaults to local"""
        server = ctx.message.server
        results = []
        if president_type == "local":
            for president in self.presidents:
                if president.server == server.id:
                    results.append(president)
        elif president_type == "global":
            for president in self.presidents:
                if president.server is None:
                    results.append(president)
        else:
            await self.bot.say("Invalid type.")
            return
        if results:
            results = ", ".join([r.name for r in results])
            await self.bot.say("```\n{}\n```".format(results))
        else:
            await self.bot.say("I couldn't find any president of that type.")


    @president.command(name="set", pass_context=True)
    @checks.admin_or_permissions(administrator=True)
    async def _set(self, ctx, president_name : str, setting : str, *,
                   value : str=None):
        """Edits the settings of each president
        Settings:
        cooldown <seconds>
        phrase <word(s) that presidents it>
        response <all or random>
        casesensitive
        regex
        Owner only:
        influence <global or local>
        Response set to 'all' outputs all responses
        Response set to 'random' outputs one at random"""
        try:
            self.change_president_settings(ctx, president_name, setting, value)
        except NotFound:
            await self.bot.say("That president doesn't exist.")
        except Unauthorized:
            await self.bot.say("You're not authorized to edit that presidents' "
                               "settings.")
        except InvalidSettings:
            await self.bot.say("Invalid settings.")
        except:
            await self.bot.say("Invalid settings.")
        else:
            self.save_presidents()
            await self.bot.say("president successfully modified.")

    @president.command(pass_context=True)
    async def search(self, ctx, *, search_terms : str):
        """Returns presidents matching the search terms"""
        result = self.search_presidents(search_terms.lower())
        if result:
            result = ", ".join(sorted([t.name for t in result]))
            await self.bot.say("presidents found:\n\n{}".format(result))
        else:
            await self.bot.say("No presidents matching your search.")

    def get_president_by_name(self, name):
        for president in self.presidents:
            if president.name.lower() == name.lower():
                return president
        return None

    def search_presidents(self, search_terms):
        results = []
        for president in self.presidents:
            if search_terms in president.name.lower():
                results.append(president)
                continue
            for payload in president.responses:
                if search_terms in payload.lower():
                    results.append(president)
                    break
            else:
                if search_terms in president.presidented_by.lower():
                    results.append(president)
        return results

    def create_president(self, name, presidented_by, ctx):
        president = self.get_president_by_name(name)
        if not president:
            author = ctx.message.author
            president = presidentObj(name=name,
                                 presidented_by=presidented_by,
                                 owner=author.id,
                                 server=author.server.id
                                )
            self.presidents.append(president)
        else:
            raise AlreadyExists()

    def delete_president(self, name, ctx):
        president = self.get_president_by_name(name)
        if president:
            if not president.can_edit(ctx.message.author):
                raise Unauthorized()
            self.presidents.remove(president)
            self.save_presidents()
        else:
            raise NotFound()

    def elaborate_payload(self, payload, truncate=50, escape=True):
        shortened = []
        for p in payload:
            if escape:
                p = (p.replace("`", "\\`")
                      .replace("*", "\\*")
                      .replace("_", "\\_")
                      .replace("~", "\\~"))
                p = escape_mass_mentions(p)
            if len(p) < truncate:
                shortened.append(p)
            else:
                shortened.append(p[:truncate] + "...")
        return shortened

    def change_president_settings(self, ctx, president_name, setting, value):
        author = ctx.message.author
        server = author.server
        president = self.get_president_by_name(president_name)
        setting = setting.lower()
        if president is None:
            raise NotFound()
        if not president.can_edit(author):
            raise Unauthorized
        if setting == "response":
            value = value.lower()
            if value in ("all", "random"):
                president.type = value
            else:
                raise InvalidSettings()
        elif setting == "cooldown":
            value = int(value)
            if not value < 1:
                president.cooldown = value
            else:
                raise InvalidSettings()
        elif setting == "influence":
            value = value.lower()
            if author.id != settings.owner:
                raise Unauthorized()
            if value in ("local", "global"):
                if value == "local":
                    president.server = server.id
                else:
                    president.server = None
            else:
                raise InvalidSettings()
        elif setting == "phrase":
            assert value is not None
            value = str(value)
            if len(value) > 0:
                president.presidented_by = value
            else:
                raise InvalidSettings()
        elif setting == "casesensitive":
            president.case_sensitive = not president.case_sensitive
        elif setting == "regex":
            president.regex = not president.regex
        else:
            raise InvalidSettings()

    async def interactive_add_mode(self, president, ctx):
        author = ctx.message.author
        msg = ""
        await self.bot.say("Everything you type will be added as response "
                               "to the president. Type 'exit' to quit.")
        while msg is not None:
            msg = await self.bot.wait_for_message(author=author, timeout=60)
            if msg is None:
                await self.bot.say("No more responses then. "
                                   "Your changes have been saved.")
                break
            if msg.content.lower().strip() == "exit":
                await self.bot.say("Your changes have been saved.")
                break
            president.responses.append(msg.content)

    def get_n_president_responses(self, president, *, truncate=2000):
        msg = ""
        responses = president.responses
        i = 0
        for r in responses:
            if len(r) > truncate:
                r = r[:truncate] + "..."
            r = r.replace("`", "\\`").replace("*", "\\*").replace("_", "\\_")
            msg += "{}. {}\n".format(i, r)
            i += 1
        if msg != "":
            return box(msg, lang="py")
        else:
            return None

    def is_command(self, msg):
        for p in self.bot.command_prefix:
            if msg.startswith(p):
                return True
        return False

    def elaborate_response(self, president, r):
        if president.owner != settings.owner:
            return "text", r
        if not r.startswith("file:"):
            return "text", r
        else:
            path = r.replace("file:", "").strip()
        path = os.path.join("data", "president", "files", path)
        print(path)
        if os.path.isfile(path):
            return "file", path
        else:
            return "text", r

    async def on_message(self, message):
        channel = message.channel
        author = message.author

        if message.server is None:
            return

        if author == self.bot.user:
            return

        if not user_allowed(message):
            return

        if self.is_command(message.content):
            return

        for president in self.presidents:
            if not president.check(message):
                continue
            payload = president.payload()
            for p in payload:
                resp_type, resp = self.elaborate_response(president, p)
                if resp_type == "text":
                    await self.bot.send_message(channel, resp)
                elif resp_type == "file":
                    await self.bot.send_file(channel, resp)

    async def save_stats(self):
        """Saves presidents every 10 minutes to preserve stats"""
        await self.bot.wait_until_ready()
        try:
            await asyncio.sleep(60)
            while True:
                self.save_presidents()
                await asyncio.sleep(60 * 10)
        except asyncio.CancelledError:
            pass

    def load_presidents(self):
        presidents = dataIO.load_json("data/president/presidents.json")
        for president in presidents:
            self.presidents.append(presidentObj(**president))

    def save_presidents(self):
        presidents = [t.export() for t in self.presidents]
        dataIO.save_json("data/president/presidents.json", presidents)

    def __unload(self):
        self.stats_task.cancel()
        self.save_presidents()

class presidentObj:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.owner = kwargs.get("owner")
        self.presidented_by = kwargs.get("presidented_by")
        self.responses = kwargs.get("responses", [])
        self.server = kwargs.get("server") # if it's None, the president will be implicitly global
        self.type = kwargs.get("type", "all") # Type of payload. Types: all, random
        self.case_sensitive = kwargs.get("case_sensitive", False)
        self.regex = kwargs.get("regex", False)
        self.cooldown = kwargs.get("cooldown", 1) # Seconds
        self.presidented = kwargs.get("presidented", 0) # Counter
        self.last_presidented = datetime.datetime(1970, 2, 6) # Initialized

    def export(self):
        data = deepcopy(self.__dict__)
        del data["last_presidented"]
        return data

    def check(self, msg):
        content = msg.content
        presidented_by = self.presidented_by
        if (self.server == msg.server.id or self.server is None) is False:
            return False
        if not self.case_sensitive:
            presidented_by = presidented_by.lower()
            content = content.lower()
        if not self.regex:
            if presidented_by not in content:
                return False
        else:
            found = re.search(presidented_by, content)
            if not found:
                return False
        timestamp = datetime.datetime.now()
        passed = (timestamp - self.last_presidented).seconds
        if passed > self.cooldown:
            self.last_presidented = timestamp
            return True
        else:
            return False

    def payload(self):
        if self.responses:
            self.presidented += 1
        if self.type == "all":
            return self.responses
        elif self.type == "random":
            if self.responses:
                return [choice(self.responses)]
            else:
                return []
        else:
            raise RuntimeError("Invalid president type.")

    def can_edit(self, user):
        server = user.server
        admin_role = settings.get_server_admin(server)
        is_owner = user.id == settings.owner
        is_admin = discord.utils.get(user.roles, name=admin_role) is not None
        is_president_owner = user.id == self.owner
        president_is_global = self.server is None
        if president_is_global:
            if is_president_owner or is_owner:
                return True
            else:
                return False
        else:
            if is_admin or is_president_owner:
                return True
            else:
                return False

def check_folders():
    paths = ("data/president", "data/president/files")
    for path in paths:
        if not os.path.exists(path):
            print("Creating {} folder...".format(path))
            os.makedirs(path)

def check_files():
    f = "data/president/presidents.json"
    if not dataIO.is_valid_json(f):
        print("Creating empty presidents.json...")
        dataIO.save_json(f, [])

def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(president(bot))