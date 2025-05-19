import os
from datetime import timedelta
import discord
from discord import app_commands, Embed, Color
from discord.ext import commands
from discord.ui import View, Button
from dotenv import load_dotenv
import json
from discord import Interaction  # ✅ これが正しい
from discord import app_commands, Interaction, Embed, Color, CategoryChannel, Role,PermissionOverwrite


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_IDS = [int(g) for g in os.getenv("GUILD_ID").split(",")]

WARN_FILE = "warnings.json"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    print(f"Bot起動: {bot.user} (ID: {bot.user.id})")
    for guild_id in GUILD_IDS:
        guild = bot.get_guild(guild_id)
        if guild:
            try:
                await tree.sync(guild=discord.Object(id=guild_id))
                print(f"スラッシュコマンド同期成功: {guild.name} ({guild.id})")
            except Exception as e:
                print(f"同期失敗: {guild.name} ({guild.id}) - {e}")

# --- /verify コマンド ---
@tree.command(name="verify", description="認証パネルを設置します", guilds=[discord.Object(id=g) for g in GUILD_IDS])
@app_commands.describe(role="認証時に付与するロール")
async def verify(interaction: discord.Interaction, role: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("エラー: 管理者権限が必要です。", ephemeral=True)
        return

    bot_member = interaction.guild.get_member(bot.user.id)
    if role.position >= bot_member.top_role.position:
        await interaction.response.send_message("エラー: ボットの権限より上のロールは付与できません。", ephemeral=True)
        return

    embed = Embed(title="認証", description="✅ 認証ボタンを押して認証を完了してください。", color=Color.blue())
    view = View(timeout=None)
    button = Button(label="✅ 認証", style=discord.ButtonStyle.green)

    async def button_callback(btn_interaction: discord.Interaction):
        if role in btn_interaction.user.roles:
            await btn_interaction.response.send_message("既に認証済みです。", ephemeral=True)
            return
        await btn_interaction.user.add_roles(role)
        await btn_interaction.response.send_message(f"{role.mention} を付与しました。認証完了です。", ephemeral=True)

    button.callback = button_callback
    view.add_item(button)

    await interaction.response.send_message(embed=embed, view=view)

# --- /kick コマンド ---
@tree.command(name="kick", description="ユーザーをキックします", guilds=[discord.Object(id=g) for g in GUILD_IDS])
@app_commands.describe(user="キックするユーザー", reason="理由（省略可）")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "なし"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("権限がありません。", ephemeral=True)
        return
    try:
        await user.kick(reason=reason)
        embed = Embed(title="キック実行", description=f"{user.mention} をキックしました。", color=Color.orange())
        embed.add_field(name="理由", value=reason)
        embed.set_footer(text=f"実行者: {interaction.user}")
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"エラー: {e}", ephemeral=True)

# --- /ban コマンド ---
@tree.command(name="ban", description="ユーザーをBANします", guilds=[discord.Object(id=g) for g in GUILD_IDS])
@app_commands.describe(user="BANするユーザー", reason="理由（省略可）")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "なし"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("権限がありません。", ephemeral=True)
        return
    try:
        await user.ban(reason=reason)
        embed = Embed(title="BAN実行", description=f"{user.mention} をBANしました。", color=Color.red())
        embed.add_field(name="理由", value=reason)
        embed.set_footer(text=f"実行者: {interaction.user}")
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"エラー: {e}", ephemeral=True)

# --- /timeout コマンド ---
@tree.command(name="timeout", description="ユーザーをタイムアウトします", guilds=[discord.Object(id=g) for g in GUILD_IDS])
@app_commands.describe(user="対象ユーザー", duration="秒数", reason="理由（省略可）")
async def timeout(interaction: discord.Interaction, user: discord.Member, duration: int, reason: str = "なし"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("権限がありません。", ephemeral=True)
        return
    try:
        until = discord.utils.utcnow() + timedelta(seconds=duration)
        await user.timeout(until=until, reason=reason)
        embed = Embed(title="タイムアウト実行", description=f"{user.mention} を {duration} 秒間タイムアウトしました。", color=Color.orange())
        embed.add_field(name="理由", value=reason)
        embed.set_footer(text=f"実行者: {interaction.user}")
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"エラー: {e}", ephemeral=True)

# --- /untimeout コマンド ---
@tree.command(name="untimeout", description="ユーザーのタイムアウトを解除します", guilds=[discord.Object(id=g) for g in GUILD_IDS])
@app_commands.describe(user="対象ユーザー", reason="理由（省略可）")
async def untimeout(interaction: discord.Interaction, user: discord.Member, reason: str = "解除"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("権限がありません。", ephemeral=True)
        return
    try:
        await user.timeout(None, reason=reason)
        embed = Embed(title="タイムアウト解除", description=f"{user.mention} のタイムアウトを解除しました。", color=Color.green())
        embed.add_field(name="理由", value=reason)
        embed.set_footer(text=f"実行者: {interaction.user}")
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"エラー: {e}", ephemeral=True)

# --- /clear コマンド ---
@tree.command(name="clear", description="最大100件のメッセージを一括削除します", guilds=[discord.Object(id=g) for g in GUILD_IDS])
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction):
    if not interaction.channel.permissions_for(interaction.user).manage_messages:
        await interaction.response.send_message("メッセージ管理権限がありません。", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=100)
    await interaction.followup.send(f"{len(deleted)} 件のメッセージを削除しました。", ephemeral=True)

@clear.error
async def clear_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("このコマンドを使うには「メッセージ管理」権限が必要です。", ephemeral=True)
    else:
        await interaction.response.send_message("エラーが発生しました。", ephemeral=True)

# --- /icon コマンド ---
@tree.command(name="icon", description="指定したメンバーのアイコンを表示します", guilds=[discord.Object(id=g) for g in GUILD_IDS])
@app_commands.describe(member="メンバー")
async def icon(interaction: discord.Interaction, member: discord.Member):
    embed = Embed(description=f"{member.mention} のアイコン", color=Color.blue())
    embed.set_image(url=member.display_avatar.url)
    embed.add_field(name="ダウンロードリンク", value=f"[こちらをクリック]({member.display_avatar.url})")
    embed.set_footer(text="Zer0")
    await interaction.response.send_message(embed=embed)

@tree.command(name="warn", description="ユーザーに警告を与えます", guilds=[discord.Object(id=g) for g in GUILD_IDS])

@app_commands.describe(user="警告を与えるユーザー", reason="警告の理由")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str = "ルール違反"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ 警告を与える権限がありません。", ephemeral=True)
        return

    if user.bot:
        await interaction.response.send_message("❌ ボットには警告を与えられません。", ephemeral=True)
        return

    if os.path.exists(WARN_FILE):
        with open(WARN_FILE, "r", encoding="utf-8") as f:
            warnings = json.load(f)
    else:
        warnings = {}

    user_id = str(user.id)
    if user_id not in warnings:
        warnings[user_id] = []

    warnings[user_id].append({
        "reason": reason,
        "moderator": str(interaction.user),
        "timestamp": interaction.created_at.isoformat()
    })

    with open(WARN_FILE, "w", encoding="utf-8") as f:
        json.dump(warnings, f, indent=4, ensure_ascii=False)

    embed = discord.Embed(
        title="⚠️ 警告実行",
        description=f"{user.mention} に警告を与えました。",
        color=discord.Color.gold()
    )
    embed.add_field(name="理由", value=reason, inline=False)
    embed.set_footer(text=f"実行者: {interaction.user}")
    await interaction.response.send_message(embed=embed)

@tree.command(name="warnings", description="指定ユーザーの警告履歴を表示します", guilds=[discord.Object(id=g) for g in GUILD_IDS])
@app_commands.describe(user="警告履歴を確認したいユーザー")
async def warnings(interaction: discord.Interaction, user: discord.Member):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ 警告履歴を確認する権限がありません。", ephemeral=True)
        return

    if not os.path.exists(WARN_FILE):
        await interaction.response.send_message(f"{user.mention} は警告を受けていません。", ephemeral=True)
        return

    with open(WARN_FILE, "r", encoding="utf-8") as f:
        warnings = json.load(f)

    user_id = str(user.id)
    if user_id not in warnings or len(warnings[user_id]) == 0:
        await interaction.response.send_message(f"{user.mention} は警告を受けていません。", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"⚠️ {user.display_name} の警告履歴",
        color=discord.Color.orange()
    )

    for i, warn in enumerate(warnings[user_id], start=1):
        reason = warn["reason"]
        moderator = warn["moderator"]
        timestamp = warn["timestamp"]
        embed.add_field(
            name=f"{i}回目の警告",
            value=f"**理由**: {reason}\n**実行者**: {moderator}\n**日時**: {timestamp}",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

@tree.command(name="antiraid", description="荒らし対策の設定を切り替えます", guilds=[discord.Object(id=g) for g in GUILD_IDS])
@app_commands.describe(
    feature="設定したい荒らし対策の種類",
    state="on または off を指定してください"
)
@app_commands.choices(feature=[
    app_commands.Choice(name="auto_kick_new_members", value="auto_kick_new_members"),
    app_commands.Choice(name="spam_filter", value="spam_filter"),
    app_commands.Choice(name="bad_word_filter", value="bad_word_filter"),
])
async def antiraid(interaction: discord.Interaction, feature: app_commands.Choice[str], state: str):
    if interaction.guild.id != GUILD_ID:
        await interaction.response.send_message("❌ このコマンドはこのサーバー専用です。", ephemeral=True)
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 管理者権限が必要です。", ephemeral=True)
        return

    state = state.lower()
    if state not in ("on", "off"):
        await interaction.response.send_message("❌ 状態は 'on' か 'off' を指定してください。", ephemeral=True)
        return

    anti_raid_settings.setdefault(GUILD_ID, {})
    anti_raid_settings[GUILD_ID][feature.value] = (state == "on")

    await interaction.response.send_message(f"✅ `{feature.value}` を **{state.upper()}** に設定しました。")

@bot.event
async def on_member_join(member: discord.Member):
    if anti_raid_settings.get(member.guild.id, {}).get("auto_kick_new_members", False):
        try:
            await member.send("荒らし対策のため新規参加者の自動キックを行いました。")
        except Exception:
            pass
        await member.kick(reason="Auto kick by anti-raid system")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    guild_id = message.guild.id if message.guild else None
    if guild_id != GUILD_ID:
        return

    settings = anti_raid_settings.get(guild_id, {})

    # 禁止ワード監視
    if settings.get("bad_word_filter", False):
        for bad_word in BAD_WORDS:
            if bad_word in message.content.lower():
                try:
                    await message.delete()
                except Exception:
                    pass
                await message.channel.send(f"{message.author.mention} 禁止ワードの使用は禁止されています。", delete_after=5)
                return

    # スパム監視（簡易版）
    if settings.get("spam_filter", False):
        user_id = message.author.id
        channel_id = message.channel.id
        key = (guild_id, user_id, channel_id)

        logs = message_logs.get(key, [])
        # 10秒以内のメッセージのみ保持
        logs = [msg_time for msg_time in logs if (discord.utils.utcnow() - msg_time).total_seconds() < 10]
        logs.append(discord.utils.utcnow())
        message_logs[key] = logs

        if len(logs) > SPAM_THRESHOLD:
            try:
                await message.channel.send(f"{message.author.mention} スパム行為は禁止されています。", delete_after=5)
                await message.delete()
            except Exception:
                pass

class TicketSelectView(View):
    def __init__(self, category_id, limit, staff_role_id, content_options):
        super().__init__(timeout=None)
        self.category_id = category_id
        self.limit = limit
        self.staff_role_id = staff_role_id
        self.content_options = content_options

        select = Select(placeholder="内容を選択してください", options=[
            discord.SelectOption(label=option.strip(), value=option.strip()) for option in content_options
        ])
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        user = interaction.user
        category = interaction.guild.get_channel(self.category_id)

        user_tickets = [ch for ch in category.text_channels if ch.name.startswith(f"🎫｜{user.name}")]
        if len(user_tickets) >= self.limit:
            await interaction.response.send_message("エラー: チケット作成の制限に達しました。既存のチケットを削除して再度作成してください。", ephemeral=True)
            return

        if len(category.channels) >= 50:
            await interaction.response.send_message("エラー: カテゴリにチャンネルが多すぎます。管理者にお知らせください。", ephemeral=True)
            return

        channel_name = f"🎫｜{user.name}"
        overwrites = {
            interaction.guild.default_role: PermissionOverwrite(view_channel=False),
            user: PermissionOverwrite(view_channel=True, send_messages=True),
        }

        staff_role = interaction.guild.get_role(self.staff_role_id)
        if staff_role:
            overwrites[staff_role] = PermissionOverwrite(view_channel=True, send_messages=True)
    
        channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)
        await interaction.response.send_message(f"チケットが作成されました: {channel.mention}", ephemeral=True)
        selected_content = interaction.data['values'][0]

        embed = Embed(
            title=f"{user.display_name}のチケット",
            description=f"内容: {selected_content}\n要件を書いてスタッフの対応をお待ちください。",
            color=Color.green()
        )
        staff_mention = f"{staff_role.mention}" if staff_role else "スタッフ未指定"
        user_mention = user.mention
        await channel.send(f"{staff_mention} | {user_mention} チケットが作成されました。")
        view = TicketDeleteView(channel)
        await channel.send(embed=embed, view=view)

class TicketDeleteView(View):
    def __init__(self, channel):
        super().__init__(timeout=None)
        self.channel = channel

    @discord.ui.button(label="削除", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: Button):
        await self.channel.delete(reason="チケット削除ボタンが押されました")

class TicketIssueButtonView(View):
    def __init__(self, category_id, limit, staff_role_id, content_options):
        super().__init__(timeout=None)
        self.category_id = category_id
        self.limit = limit
        self.staff_role_id = staff_role_id
        self.content_options = content_options

    @discord.ui.button(label="🎫発行", style=discord.ButtonStyle.primary)
    async def issue_button(self, interaction: discord.Interaction, button: Button):
        view = TicketSelectView(self.category_id, self.limit, self.staff_role_id, self.content_options)
        await interaction.response.send_message("内容を選択してください:", view=view, ephemeral=True)

@tree.command(name="ticket", description="チケット作成フォームを開きます", guilds=[discord.Object(id=g) for g in GUILD_IDS])
@app_commands.describe(
    title="Embedのタイトル",
    description="チケットの説明文",
    category="チャンネルを作成するカテゴリ",
    limit="ユーザーが作成できるチャンネルの上限",
    staff="作成したチャンネルにアクセスできるスタッフロール",
    content="チケットの内容（例: '代行,購入,質問'）"
)
async def ticket_command(
    interaction: Interaction, 
    title: str, 
    description: str, 
    category: CategoryChannel, 
    limit: int, 
    staff: Role,
    content: str
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("エラー: このコマンドを使用するには管理者権限が必要です。", ephemeral=True)
        return

    content_options = content.replace("&", ",").split(",")

    embed = Embed(title=title, description=description, color=Color.blue())
    view = TicketIssueButtonView(category.id, limit, staff.id, content_options)
    
    try:
        message = await interaction.channel.send(embed=embed, view=view)
    except Exception as e:
        await interaction.response.send_message(f"エラー: メッセージを送信できませんでした。{str(e)}", ephemeral=True)
        return

    await interaction.response.send_message("チケット作成フォームが正常に作成されました。", ephemeral=True)


bot.run(TOKEN)
