import discord
import os
from discord.flags import Intents
from dotenv import load_dotenv
import asyncio
from inventoryDetection import handleImageDetection

load_dotenv()
intents = discord.Intents.all()

guild_id = 1127618095687671909
my_guild = discord.Object(id=guild_id)
admin_channel = 1141774925552689153
ROLES_CHANNEL = 1129159066086801578
ROLES_MESSAGE = 1140727328322879608

class MyClient(discord.Client):
    def __init__(self, *, intents: Intents):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=my_guild)
        await self.tree.sync(guild=my_guild)
        self.add_view(BotReportView())

client = MyClient(intents=intents)

@client.event
async def on_ready():
    channel = client.get_channel(ROLES_CHANNEL)
    message = await channel.fetch_message(ROLES_MESSAGE)

    await message.add_reaction("🇺🇸")
    await message.add_reaction("🇧🇷")
    await message.add_reaction("📢")

    print(f"{client.user} is ready and online!")

@client.event
async def on_message(message):
    await handleImageDetection(message, client.user, client.user.avatar)

@client.event
async def on_raw_reaction_add(event: discord.RawReactionActionEvent):
    if event.message_id != ROLES_MESSAGE:
        return
    
    emoji = str(event.emoji)
    if emoji == "🇺🇸":
        await addRole(1129148272309702756, event.user_id)
    if emoji == "🇧🇷":
        await addRole(1129148360591425596, event.user_id)
    if emoji == "📢":
        await addRole(1129148508721647657, event.user_id)


@client.tree.command(name="prepare_report", guild=my_guild)
async def prepare_report(interaction: discord.Interaction):
    embed = discord.Embed(title=f"Contact us", color=0x2C2542, type="rich", description="Interact with the buttons bellow to either make a suggestion or a bug report, the bot will send you a private message after the interaction so you can describe the issue.")
    embed.set_thumbnail(url=client.user.avatar)

    await interaction.response.send_message(embed=embed, view=BotReportView())

class BotReportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.ongoing = []

    def removeId(self, id: int):
        self.ongoing.remove(id)
    
    def addId(self, id: int):
        self.ongoing.append(id)

    @discord.ui.button(label="Make a suggestion", style=discord.ButtonStyle.primary, emoji="🔮", custom_id='persistent_view:suggestion')
    async def suggestion_callback(self, interaction: discord.Interaction, _):
        if (interaction.user.id in self.ongoing): return
        self.addId(interaction.user.id)

        embed = discord.Embed(title=f"Suggestion creation", color=0x2C2542, type="rich", description="Type your suggestion in only one message. If you want to cancel this interaction, click on the Cancel button.\n\nThis interaction will expire after 15 minutes.")
        embed.set_thumbnail(url=client.user.avatar)

        await interaction.user.send(embed=embed, view=BotReportResponseView(trigger=self.removeId))

        def check(message: discord.Message):
            return message.channel.type == discord.ChannelType.private and message.author == interaction.user

        try:
            message = await client.wait_for("message", timeout=60.0*15.0, check=check)
            await interaction.user.send(f"Your suggestion was successfully submitted, and our team will soon review it!")
            
            reportEmbed = discord.Embed(title="Suggestion", color=0x2C2542, type="rich", description=message.content)
            reportEmbed.set_author(name=message.author)
            await client.get_channel(admin_channel).send(embed=reportEmbed)
            self.ongoing.remove(interaction.user.id)
        except asyncio.TimeoutError:
            self.ongoing.remove(interaction.user.id)
            await interaction.user.send("Message timeout.")

    @discord.ui.button(label="Report a bug", style=discord.ButtonStyle.primary, emoji="🐛", custom_id='persistent_view:report')
    async def bug_callback(self, interaction: discord.Interaction, _):
        if (interaction.user.id in self.ongoing): return
        self.addId(interaction.user.id)

        embed = discord.Embed(title=f"Bug report", color=0x2C2542, type="rich", description="Type your report in only one message as the following template:\n\n Page name: Constitution \n Feature name: Tier selection \n How to reproduce: ... \n\n If you want to cancel this interaction, click on the Cancel button.\n\nThis interaction will expire after 15 minutes.")
        embed.set_thumbnail(url=client.user.avatar)

        await interaction.user.send(embed=embed, view=BotReportResponseView(trigger=self.removeId))
        
        def check(message: discord.Message):
            return message.channel.type == discord.ChannelType.private and message.author == interaction.user

        try:
            message = await client.wait_for("message", timeout=60.0*15.0, check=check)
            await interaction.user.send(f"Your bug was successfully reported, and our team will soon resolve it!")

            reportEmbed = discord.Embed(title="Bug report", color=0x2C2542, type="rich", description=message.content)
            reportEmbed.set_author(name=message.author)
            await client.get_channel(admin_channel).send(embed=reportEmbed)
            self.ongoing.remove(interaction.user.id)
        except asyncio.TimeoutError:
            self.ongoing.remove(interaction.user.id)
            await interaction.user.send("Message timeout.")

class BotReportResponseView(discord.ui.View):
    def __init__(self, trigger):
        super().__init__()
        self.trigger = trigger

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_callback(self, interaction: discord.Interaction, _):
        self.trigger(interaction.user.id)
        await interaction.user.send(content="Interaction canceled.")

async def addRole(roleId: int, userId: int):
    role = discord.Object(roleId)
    guild = await client.fetch_guild(guild_id)
    user = await guild.fetch_member(userId)

    return await user.add_roles(role)

client.run(os.getenv('DISCORD_TOKEN'))