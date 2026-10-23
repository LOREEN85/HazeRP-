import asyncio
import json
import os
import random
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands

# --- KONFIGURACJA FLASKA DLA UPTIMEROBOTA ---
app = Flask('')


@app.route('/')
def home():
  return "Bot ekonomiczny PLN dziala 24/7!"


def run_flask():
  app.run(host='0.0.0.0', port=8080)


def keep_alive():
  t = Thread(target=run_flask)
  t.start()


# --- KONFIGURACJA BOTA DISCORD ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

DATA_FILE = 'economy.json'

# Sklep z walutą w PLN i przypisanymi rolami
SHOP_ITEMS = {
    'prawo jazdy kat. b': {'price': 2500, 'role': 'Prawo jazdy kat. B'},
    'prawo jazdy kat. c': {'price': 3000, 'role': 'Prawo jazdy kat. C'},
    'karta wędkarska': {'price': 500, 'role': 'Karta wędkarska'},
    'pozwolenie na broń': {'price': 2000, 'role': 'Pozwolenie na broń'},
    'colt': {'price': 25000, 'role': 'Colt'},
    'beretta': {'price': 24000, 'role': 'Beretta'},
    'łom': {'price': 250, 'role': 'Łom'},
    'baseball': {'price': 300, 'role': 'Baseball'},
    'nóż': {'price': 260, 'role': 'Nóż'},
}


def load_data():
  if not os.path.exists(DATA_FILE):
    return {}
  with open(DATA_FILE, 'r', encoding='utf-8') as f:
    return json.load(f)


def save_data(data):
  with open(DATA_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


def get_user_data(user_id):
  data = load_data()
  uid = str(user_id)
  if uid not in data:
    data[uid] = {
        'wallet': 0,
        'bank': 0,
        'last_work': '2000-01-01 00:00:00',
        'last_hustle': '2000-01-01 00:00:00',
        'last_crime': '2000-01-01 00:00:00',
    }
    save_data(data)
  return data[uid]


@bot.event
async def on_ready():
  print(f'Zalogowano jako {bot.user.name}! Bot ekonomiczny PLN jest gotowy.')


# --- 1. !work (50-150 PLN, co 5h) ---
@bot.command()
async def work(ctx):
  data = load_data()
  uid = str(ctx.author.id)
  user = get_user_data(uid)

  now = datetime.now()
  last_work = datetime.strptime(user['last_work'], '%Y-%m-%d %H:%M:%S')

  if now - last_work < timedelta(hours=5):
    left = timedelta(hours=5) - (now - last_work)
    hours, remainder = divmod(int(left.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    await ctx.send(
        f'⏳ **{ctx.author.name}**, musisz odpocząć! Następna praca za **{hours}h'
        f' {minutes}m**.'
    )
    return

  zarobek = random.randint(50, 150)
  user['wallet'] += zarobek
  user['last_work'] = now.strftime('%Y-%m-%d %H:%M:%S')
  data[uid] = user
  save_data(data)

  embed = discord.Embed(
      title='💼 Sukces w pracy!',
      description=(
          f'{ctx.author.mention} poszedłeś do uczciwej pracy i zarobiłeś'
          f' **{zarobek} PLN**!'
      ),
      color=discord.Color.green(),
  )
  await ctx.send(embed=embed)


# --- 2. !hustle (40-100 PLN, co 8h) ---
@bot.command()
async def hustle(ctx):
  data = load_data()
  uid = str(ctx.author.id)
  user = get_user_data(uid)

  now = datetime.now()
  last_hustle = datetime.strptime(user['last_hustle'], '%Y-%m-%d %H:%M:%S')

  if now - last_hustle < timedelta(hours=8):
    left = timedelta(hours=8) - (now - last_hustle)
    hours, remainder = divmod(int(left.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    await ctx.send(
        f'⏳ **{ctx.author.name}**, jesteś zbyt zmęczony na hustle. Odpocznij'
        f' jeszcze **{hours}h {minutes}m**.'
    )
    return

  zarobek = random.randint(40, 100)
  user['wallet'] += zarobek
  user['last_hustle'] = now.strftime('%Y-%m-%d %H:%M:%S')
  data[uid] = user
  save_data(data)

  embed = discord.Embed(
      title='🔥 Szybki biznes!',
      description=(
          f'{ctx.author.mention} ogarnąłeś lewy interes i zgarnąłeś'
          f' **{zarobek} PLN**!'
      ),
      color=discord.Color.orange(),
  )
  await ctx.send(embed=embed)

# --- POMOCNICZA FUNKCJA SPRAWDZAJĄCA BAZĘ DANYCH ---
def ensure_user_keys(user_data):
  """Zapewnia synchornizację portfela i banku niezależnie od używanych kluczy w bazie."""
  if "wallet" not in user_data:
    user_data["wallet"] = user_data.get("cash", 0)
  if "bank" not in user_data:
    user_data["bank"] = user_data.get("bank_balance", 0)

  # Synchronizacja w drugą stronę
  user_data["cash"] = user_data["wallet"]
  user_data["bank_balance"] = user_data["bank"]
  return user_data


# --- KOMENDA: !bal / !balance ---
@bot.command(aliases=["balance", "konto", "stan"])
async def bal(ctx, member: discord.Member = None):
  target = member or ctx.author
  data = load_data()
  user = ensure_user_keys(get_user_data(target.id))

  wallet_val = user["wallet"]
  bank_val = user["bank"]
  total_val = wallet_val + bank_val

  embed = discord.Embed(
      title=f"💳 Portfel: {target.display_name}", color=discord.Color.blue()
  )
  if target.avatar:
    embed.set_thumbnail(url=target.avatar.url)

  embed.add_field(
      name="💵 Portfel (gotówka)", value=f"**{wallet_val} PLN**", inline=True
  )
  embed.add_field(
      name="🏦 Bank (konto)", value=f"**{bank_val} PLN**", inline=True
  )
  embed.add_field(
      name="\n📊 Łącznie majątek",
      value=f"**{total_val} PLN**",
      inline=False,
  )

  await ctx.send(embed=embed)


# --- KOMENDA: !dep <kwota> / !dep all ---
@bot.command(aliases=["deposit"])
async def dep(ctx, amount: str = None):
  if amount is None:
    await ctx.send(
        f"❌ {ctx.author.mention}, podaj kwotę do wpłaty, np. `!dep 50` lub"
        " `!dep all`!"
    )
    return

  data = load_data()
  user = ensure_user_keys(get_user_data(ctx.author.id))

  if amount.lower() == "all":
    dep_amount = user["wallet"]
  else:
    try:
      dep_amount = int(amount)
    except ValueError:
      await ctx.send(
          f"❌ {ctx.author.mention}, podaj poprawną liczbę lub `all`!"
      )
      return

  if dep_amount <= 0:
    await ctx.send(
        f"❌ {ctx.author.mention}, kwota wpłaty musi być większa niż 0 PLN!"
    )
    return

  if user["wallet"] < dep_amount:
    await ctx.send(
        f"❌ {ctx.author.mention}, nie masz tylu pieniędzy w portfelu!"
        f" Posiadasz tylko **{user['wallet']} PLN**."
    )
    return

  # Aktualizacja wartości w obu zestawach kluczy
  user["wallet"] -= dep_amount
  user["bank"] += dep_amount
  ensure_user_keys(user)

  save_data(data)

  embed = discord.Embed(
      title="🏦 Wpłata do banku",
      description=(
          f"{ctx.author.mention} wpłaciłeś **{dep_amount} PLN** do bezpiecznego"
          f" banku.\n💳 Portfel: **{user['wallet']} PLN** | 🏦 Bank:"
          f" **{user['bank']} PLN**"
      ),
      color=discord.Color.green(),
  )
  await ctx.send(embed=embed)


# --- KOMENDA: !with <kwota> / !with all ---
@bot.command(aliases=["withdraw"])
async def with_cmd(ctx, amount: str = None):
  if amount is None:
    await ctx.send(
        f"❌ {ctx.author.mention}, podaj kwotę do wypłaty, np. `!with 50` lub"
        " `!with all`!"
    )
    return

  data = load_data()
  user = ensure_user_keys(get_user_data(ctx.author.id))

  if amount.lower() == "all":
    with_amount = user["bank"]
  else:
    try:
      with_amount = int(amount)
    except ValueError:
      await ctx.send(
          f"❌ {ctx.author.mention}, podaj poprawną liczbę lub `all`!"
      )
      return

  if with_amount <= 0:
    await ctx.send(
        f"❌ {ctx.author.mention}, kwota wypłaty musi być większa niż 0 PLN!"
    )
    return

  if user["bank"] < with_amount:
    await ctx.send(
        f"❌ {ctx.author.mention}, nie masz tylu pieniędzy w banku! Posiadasz"
        f" tam tylko **{user['bank']} PLN**."
    )
    return

  # Aktualizacja wartości w obu zestawach kluczy
  user["bank"] -= with_amount
  user["wallet"] += with_amount
  ensure_user_keys(user)

  save_data(data)

  embed = discord.Embed(
      title="🏦 Wypłata z banku",
      description=(
          f"{ctx.author.mention} wypłaciłeś **{with_amount} PLN** ze swojego"
          f" konta bankowego.\n💳 Portfel: **{user['wallet']} PLN** | 🏦 Bank:"
          f" **{user['bank']} PLN**"
      ),
      color=discord.Color.blue(),
  )
  await ctx.send(embed=embed)






# --- 7. !crime (50% szans na zysk/stratę 100-200 PLN, co 24h) ---
@bot.command()
async def crime(ctx):
  data = load_data()
  uid = str(ctx.author.id)
  user = get_user_data(uid)

  now = datetime.now()
  last_crime = datetime.strptime(user['last_crime'], '%Y-%m-%d %H:%M:%S')

  if now - last_crime < timedelta(hours=24):
    left = timedelta(hours=24) - (now - last_crime)
    hours, remainder = divmod(int(left.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    await ctx.send(
        f'🚨 **{ctx.author.name}**, policja jeszcze patroliuje teren! Kolejny'
        f' skok możliwy za **{hours}h {minutes}m**.'
    )
    return

  kwota = random.randint(100, 200)
  sukces = random.random() < 0.5

  user['last_crime'] = now.strftime('%Y-%m-%d %H:%M:%S')

  if sukces:
    user['wallet'] += kwota
    embed = discord.Embed(
        title='🦹 Skok udany!',
        description=(
            f'{ctx.author.mention} udało Ci się obrobić sklep i ukryć przed'
            f' psami. Zyskujesz **{kwota} PLN**!'
        ),
        color=discord.Color.green(),
    )
  else:
    strata = min(user['wallet'], kwota)
    user['wallet'] -= strata
    embed = discord.Embed(
        title='🚓 Wpadka!',
        description=(
            f'{ctx.author.mention} policja przyłapała Cię na gorącym uczynku!'
            f' Zapłaciłeś mandat/straciłeś **{strata} PLN**.'
        ),
        color=discord.Color.red(),
    )

  data[uid] = user
  save_data(data)
  await ctx.send(embed=embed)


# --- 8. !top ---
@bot.command()
async def top(ctx):
  data = load_data()
  if not data:
    await ctx.send('❌ Brak danych o bogactwie graczy!')
    return

  sorted_users = sorted(
      data.items(), key=lambda x: x[1]['wallet'] + x[1]['bank'], reverse=True
  )

  embed = discord.Embed(
      title='🏆 Top 10 Najbogatszych Obywateli',
      description='Oto najbogatsi gracze na serwerze:',
      color=discord.Color.gold(),
  )

  text = ''
  medale = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

  for i, (uid, info) in enumerate(sorted_users[:10], start=1):
    member = ctx.guild.get_member(int(uid))
    name = member.display_name if member else f'Obywatel {uid}'
    total = info['wallet'] + info['bank']
    emoji = medale[i - 1] if i <= 3 else f'`{i}.`'
    text += (
        f'{emoji} **{name}** — **{total} PLN** *(Portfel: {info["wallet"]} PLN |'
        f' Bank: {info["bank"]} PLN)*\n'
    )

  embed.add_field(name='Ranking', value=text, inline=False)
  await ctx.send(embed=embed)


# --- 9. !ruletka ---
@bot.command()
async def ruletka(ctx, kolor: str, stawka: int):
  kolor = kolor.lower()
  if kolor not in ['czerwony', 'czarny', 'zielony']:
    await ctx.send(
        f'❌ {ctx.author.mention}, wybierz poprawny kolor: `czerwony`, `czarny` lub'
        ' `zielony`!'
    )
    return

  user = get_user_data(ctx.author.id)
  if user['wallet'] < stawka or stawka <= 0:
    await ctx.send(
        f'❌ {ctx.author.mention}, nie masz tyle w portfelu lub podano złą'
        ' stawkę!'
    )
    return

  if random.random() < 0.30:
    wygrana = stawka * 2
    user['wallet'] += stawka
    save_data(load_data())
    embed = discord.Embed(
        title='🎰 Ruletka - Wygrana!',
        description=(
            f'🎉 Kula trafiła w Twój kolor! Wygrywasz i zgarniasz'
            f' **{wygrana} PLN**!'
        ),
        color=discord.Color.green(),
    )
  else:
    user['wallet'] -= stawka
    save_data(load_data())
    embed = discord.Embed(
        title='🎰 Ruletka - Przegrana',
        description=(
            f'💀 Kula zatrzymała się w innym miejscu. Tracisz postawione'
            f' **{stawka} PLN**.'
        ),
        color=discord.Color.red(),
    )

  await ctx.send(embed=embed)


# --- 10. !sklep oraz !kup ---
@bot.command()
async def sklep(ctx):
  embed = discord.Embed(
      title='🛒 Sklep Licencji i Przedmiotów',
      description='Wpisz `!kup <nazwa przedmiotu>`, aby dokonać zakupu.',
      color=discord.Color.teal(),
  )

  for item, details in SHOP_ITEMS.items():
    nazwa_wyswietlana = item.capitalize()
    embed.add_field(
        name=f'🔹 {nazwa_wyswietlana}',
        value=f'Cena: **{details["price"]} PLN**\nNadaje rolę: `{details["role"]}`',
        inline=False,
    )

  await ctx.send(embed=embed)


# --- KONFIGURACJA WYPŁAT (!collect) ---
ROLE_PAYOUTS = {
    1562161272831873116: 762,  # Zarzad KWP
    1562161335419015308: 843,  # Zarzad PRM
    1562161420085362888: 756,  # Zarzad PSP
    1562161451307634698: 751,  # Zarzad OSP
    1562161482119118948: 746,  # zarzad GDDKiA
    1562160796916646000: 435,  # KWP
    1562160850331107379: 534,  # PRM
    1562160899823767603: 432,  # PSP
    1562160921311322184: 428,  # OSP
    1562160960230395905: 426,  # GDDKiA
    1562161025334378596: 324,  # FIRMA
}

collect_cooldowns = {}


# --- KONFIGURACJA SKLEPU (!kup) ---
SHOP_ITEMS = {
    "prawo jazdy b": {
        "name": "Prawo Jazdy B",
        "price": 500,
        "role_id": 1563214789512138864,
    },
    "prawo jazdy c": {
        "name": "Prawo Jazdy C",
        "price": 1000,
        "role_id": 1563215060334280837,
    },
    "karta wedkarska": {
        "name": "Karta Wędkarska",
        "price": 200,
        "role_id": 1563215061227667487,
    },
    "pozwolenie na bron": {
        "name": "Pozwolenie na Broń",
        "price": 2500,
        "role_id": 1563215061697175622,
    },
    "colt": {"name": "Colt", "price": 1500, "role_id": 1563215062544421034},
    "beretta": {"name": "Beretta", "price": 1800, "role_id": 1563215063056261140},
    "lom": {"name": "Łom", "price": 300, "role_id": 1563215064482455683},
    "noz": {"name": "Nóż", "price": 150, "role_id": 1563215063635075082},
    "baseball": {
        "name": "Kij Baseballowy",
        "price": 250,
        "role_id": 1563215064884969573,
    },
}


# --- KOMENDA: !collect ---

@bot.command()
async def collect(ctx):
  user_id = ctx.author.id
  now = datetime.now()

  # Sprawdzanie cooldownu 24h
  if user_id in collect_cooldowns:
    next_collect_time = collect_cooldowns[user_id] + timedelta(hours=24)
    if now < next_collect_time:
      remaining = next_collect_time - now
      hours, remainder = divmod(int(remaining.total_seconds()), 3600)
      minutes, _ = divmod(remainder, 60)
      await ctx.send(
          f"❌ {ctx.author.mention}, swoją wypłatę możesz odebrać ponownie za"
          f" **{hours} godz. i {minutes} min.**!"
      )
      return

  # Liczenie łącznej kwoty na podstawie ról użytkownika
  total_payout = 0
  matched_roles = []

  for role in ctx.author.roles:
    if role.id in ROLE_PAYOUTS:
      amount = ROLE_PAYOUTS[role.id]
      total_payout += amount
      matched_roles.append(f"{role.name} (+{amount} PLN)")

  if total_payout == 0:
    await ctx.send(
        f"❌ {ctx.author.mention}, nie posiadasz żadnej roli uprawniającej do"
        " pobrania wypłaty!"
    )
    return

  # Ustawienie cooldownu na 24h od teraz
  collect_cooldowns[user_id] = now

  roles_str = ", ".join(matched_roles)
  await ctx.send(
      f"✅ {ctx.author.mention}, pomyślnie odebrałeś dzienną wypłatę w wysokości"
      f" **{total_payout} PLN**!\n📜 **Uwzględnione role:** {roles_str}"
  )


# --- KOMENDA: !kup ---
@bot.command()
async def kup(ctx, *, item_key: str = None):
  if not item_key:
    await ctx.send(
        "❌ Podaj nazwę przedmiotu, który chcesz kupić, np. `!kup Colt`!"
    )
    return

  item_key_clean = item_key.lower().strip()

  if item_key_clean not in SHOP_ITEMS:
    await ctx.send(
        "❌ Nie znaleziono takiego przedmiotu w sklepie! Wpisz `!sklep`, aby"
        " zobaczyć ofertę."
    )
    return

  item = SHOP_ITEMS[item_key_clean]
  price = item["price"]
  role_id = item["role_id"]
  user = ctx.author

  # Sprawdzenie czy użytkownik już ma tę rolę
  role = ctx.guild.get_role(role_id)
  if role and role in user.roles:
    await ctx.send(f"❌ {user.mention}, posiadasz już **{item['name']}**!")
    return

  # Nadanie roli na serwerze
  if role:
    try:
      await user.add_roles(role)
      await ctx.send(
          f"🛍️ {user.mention}, pomyślnie zakupiono **{item['name']}** za"
          f" **{price} PLN**! Otrzymałeś odpowiednią rolę."
      )
    except discord.Forbidden:
      await ctx.send(
          "❌ Bot nie ma wystarczających uprawnień, aby nadać tę rolę! Upewnij"
          " się, że rola bota jest wyżej w ustawieniach serwera."
      )
  else:
    await ctx.send(
        "❌ Nie znaleziono roli na serwerze. Skontaktuj się z administracją."
    )
# --- KOMENDA: !pay <ilosc> <@osoba/nick> ---
@bot.command()
async def pay(ctx, amount: int = None, member: discord.Member = None):
  if amount is None or member is None:
    await ctx.send(
        f"❌ {ctx.author.mention}, użyj poprawnego formatu: `!pay <ilość>"
        " <@oznaczenie_gracza>` (np. `!pay 500 @Gracz`)!"
    )
    return

  if amount <= 0:
    await ctx.send(
        f"❌ {ctx.author.mention}, kwota przelewu musi być większa niż 0 PLN!"
    )
    return

  if member.id == ctx.author.id:
    await ctx.send(
        f"❌ {ctx.author.mention}, nie możesz przelać pieniędzy samemu sobie!"
    )
    return

  if member.bot:
    await ctx.send(
        f"❌ {ctx.author.mention}, nie możesz przelać pieniędzy botowi!"
    )
    return

  data = load_data()
  sender = get_user_data(ctx.author.id)

  if sender["wallet"] < amount:
    await ctx.send(
        f"❌ {ctx.author.mention}, nie masz wystarczająco pieniędzy w portfelu!"
        f" Posiadasz tylko **{sender['wallet']} PLN**."
    )
    return

  receiver = get_user_data(member.id)

  # Przelew środków między portfelami
  sender["wallet"] -= amount
  receiver["wallet"] += amount
  save_data(data)

  await ctx.send(
      f"💸 {ctx.author.mention} przekazał(a) **{amount} PLN** dla"
      f" {member.mention}!"
  )


# Uruchomienie serwera WWW i bota
keep_alive()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)
