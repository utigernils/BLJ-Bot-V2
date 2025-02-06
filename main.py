import discord
from discord import app_commands
from discord.ext import commands
from dateutil import parser
import random
import asyncio
import requests

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

PRODUKTE = [
    ["Produkt 1", 10.50],
    ["Produkt 2", 15.00],
    ["Produkt 3", 20.00],
    ["Produkt 4", 5.99],
    ["Produkt 5", 12.49]
]

# Emojis für die Auswahl
EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

def get_weather(city):
    api_key = "XXX"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url).json()
    if response.get("cod") != 200:
        return None
    return response

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Eingeloggt als {bot.user}')

@bot.tree.command(name="erinnere", description="Setze eine Erinnerung in Minuten.")
async def remindme(interaction: discord.Interaction, zeit: int, erinnerung: str):
    await interaction.response.send_message(f'Erinnerung in {zeit} Minuten gesetzt.', ephemeral=True)
    await asyncio.sleep(zeit * 60)
    await interaction.followup.send(f'{interaction.user.mention}, Erinnerung: {erinnerung}')

@bot.tree.command(name="umfrage", description="Erstelle eine Ja/Nein-Umfrage.")
async def poll(interaction: discord.Interaction, frage: str):
    nachricht = await interaction.channel.send(f'Umfrage: {frage}\n👍 für Ja | 👎 für Nein')
    await nachricht.add_reaction("👍")
    await nachricht.add_reaction("👎")
    await interaction.response.send_message("Umfrage erstellt!", ephemeral=True)

@bot.tree.command(name="witz", description="Erhalte einen zufälligen Witz.")
async def joke(interaction: discord.Interaction):
    try:
        antwort = requests.get("https://official-joke-api.appspot.com/jokes/random").json()
        embed = discord.Embed(title="Witz des Tages", description=f'{antwort["setup"]}\n||{antwort["punchline"]}||', color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)
    except:
        await interaction.response.send_message("Konnte keinen Witz laden. Versuche es später erneut.")

@bot.tree.command(name="wetter", description="Zeigt das aktuelle Wetter einer Stadt an.")
async def weather(interaction: discord.Interaction, stadt: str):
    data = get_weather(stadt)
    if data:
        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]
        embed = discord.Embed(title=f"Wetter in {stadt}", description=f'{temp}°C, {description}', color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("Stadt nicht gefunden.")

@bot.tree.command(name="zahl", description="Generiert eine zufällige Zahl zwischen zwei Werten.")
async def randomnum(interaction: discord.Interaction, min: int, max: int):
    zahl = random.randint(min, max)
    await interaction.response.send_message(f'Zufallszahl: {zahl}')

@bot.tree.command(name="muenze", description="Wirft eine Münze.")
async def coinflip(interaction: discord.Interaction):
    ergebnis = random.choice(["Kopf", "Zahl"])
    await interaction.response.send_message(f'Münzwurf: {ergebnis}')

@bot.tree.command(name="fakt", description="Erhalte einen zufälligen Fakt.")
async def randomfact(interaction: discord.Interaction):
    try:
        antwort = requests.get("https://uselessfacts.jsph.pl/random.json?language=en").json()
        embed = discord.Embed(title="Zufallsfakt", description=antwort["text"], color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)
    except:
        await interaction.response.send_message("Konnte keinen Fakt laden. Versuche es später erneut.")

@bot.tree.command(name="loeschen", description="Löscht eine bestimmte Anzahl an Nachrichten.")
async def clear(interaction: discord.Interaction, anzahl: int):
    if interaction.user.guild_permissions.manage_messages:
        await interaction.response.defer(ephemeral=True)  # Defer Interaction
        await interaction.channel.purge(limit=anzahl+1)
        await interaction.followup.send(f'{anzahl} Nachrichten gelöscht.', ephemeral=True)  # Follow-up Nachricht
    else:
        await interaction.response.send_message("Du hast keine Berechtigung, Nachrichten zu löschen.", ephemeral=True)

@bot.tree.command(name="ki", description="Stelle der KI eine Frage.")
async def ask_ai(interaction: discord.Interaction, frage: str):
    api_key = "XXX"
    url = "https://ai.utigernils.ch/api.php"

    headers = {"Content-Type": "application/json"}
    data = {"api_key": api_key, "prompt": frage}

    try:
        await interaction.response.defer()
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        antwort = response.json().get("content", "Keine Antwort erhalten.")
        embed = discord.Embed(title="KI sagt:", description=antwort, color=discord.Color.blue())
        embed.set_footer(text=f"Frage von {interaction.user.display_name}")
        await interaction.followup.send(embed=embed)
    except requests.exceptions.RequestException as e:
        await interaction.followup.send(f"Fehler bei der Anfrage an die KI: {e}")
    except KeyError:
        await interaction.followup.send("Die KI konnte keine Antwort liefern.")



@bot.tree.command(name="sbb", description="Zeigt die nächsten SBB-Verbindungen.")
async def sbb_verbindungen(interaction: discord.Interaction, von: str, bis: str):
    url = f"https://transport.opendata.ch/v1/connections?from={von}&to={bis}&limit=1"
    try:
        response = requests.get(url).json()

        connection = response["connections"][0]

        departure = parser.isoparse(connection["from"]["departure"]).strftime("%H:%M")
        arrival = parser.isoparse(connection["to"]["arrival"]).strftime("%H:%M")
        duration = connection["duration"].replace("d", "")  # Entferne das "d" aus der Dauer
        transfers = connection["transfers"]

        # Liste der Stationen und Zeiten
        stations = []
        sections = connection["sections"]
        for i, section in enumerate(sections):
            if "journey" in section:
                depart_station = section["departure"]["station"]["name"]
                arrive_station = section["arrival"]["station"]["name"]

                departure_time = parser.isoparse(section["departure"]["departure"]).strftime("%H:%M")
                arrival_time = parser.isoparse(section["arrival"]["arrival"]).strftime("%H:%M")

                # Füge die Stationen und Zeiten in einer "Tabellenform" hinzu
                stations.append(f"`{depart_station.ljust(20)}` | `{departure_time}`")
                stations.append(f"`{arrive_station.ljust(20)}` | `{arrival_time}`")

                # Füge "Umsteigen" nur hinzu, wenn es nicht die letzte Sektion ist
                if i < len(sections) - 1:
                    stations.append("**Umsteigen**")

        embed = discord.Embed(
            colour=discord.Colour.red(),
            description=f"SBB-Verbindung von {von} nach {bis}",
            title="SBB Verbindungen"
        )

        embed.set_footer(text="Livedaten von transport.opendata.ch")
        embed.set_thumbnail(url="https://digital.sbb.ch/assets/images/lean/overview/brand.webp")

        embed.add_field(name="Abfahrt", value=departure)
        embed.add_field(name="Ankunft", value=arrival)
        embed.add_field(name="Dauer", value=duration)
        embed.add_field(name="Umstiege", value=transfers, inline=False)

        # Füge die Stationen als eine "Tabelle" hinzu
        stations_text = "\n".join(stations)
        embed.add_field(name="Stationen", value=stations_text, inline=False)

        await interaction.response.send_message(embed=embed)

    except requests.exceptions.RequestException as e:
        await interaction.response.send_message(f'Fehler beim Abrufen der SBB-Verbindungen. {e}')

@bot.tree.command(name="bestellen", description="Bestelle ein Produkt.")
async def bestellen(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛒 Produktliste",
        description="Wähle ein Produkt aus, indem du auf die entsprechende Zahl reagierst.",
        color=discord.Color.blue()
    )

    for i, (produkt, preis) in enumerate(PRODUKTE, start=1):
        embed.add_field(name=f"{i}. {produkt}", value=f"Preis: {preis:.2f} CHF", inline=False)

    embed.set_footer(text="Reagiere mit der entsprechenden Zahl, um zu bestellen.")

    nachricht = await interaction.response.send_message(embed=embed)

    nachricht_obj = await interaction.original_response()

    for emoji in EMOJIS:
        await nachricht_obj.add_reaction(emoji)

@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user.bot:
        return

    if reaction.message.author == bot.user and "🛒 Produktliste" in reaction.message.embeds[0].title:
        try:
            index = EMOJIS.index(reaction.emoji)
        except ValueError:
            return

        produkt, preis = PRODUKTE[index]

        embed = discord.Embed(
            title="✅ Bestellung aufgegeben",
            description=f"{user.mention} hat **{produkt}** für **{preis:.2f} CHF** bestellt.",
            color=discord.Color.green()
        )

        guild = reaction.message.guild
        seller_role = discord.utils.get(guild.roles, name="seller")
        if seller_role:
            for member in seller_role.members:
                try:
                    # Sende die Bestellbestätigung als DM
                    await member.send(embed=embed)
                except discord.Forbidden:
                    print(f"Konnte Nachricht nicht an {member.name} senden (keine DMs erlaubt).")
                except Exception as e:
                    print(f"Fehler beim Senden der DM an {member.name}: {e}")

        await reaction.message.delete()

        channel = reaction.message.channel
        await channel.send(embed=embed)

bot.run("XXX")
