from datetime import datetime, timedelta
import json
import os
import random
from threading import Thread
import discord
from discord.ext import commands
from flask import Flask

# --- SERWER HTTP DLA RENDERA (WEB SERVICE) ---
app = Flask('')


@app.route('/')
def home():
  return 'Bot HazeRP działa 24/7!'


def run_web():
  port = int(os.environ.get('PORT', 8080))
  app.run(host='0.0.0.0', port=port)


def keep_alive():
  t = Thread(target=run_web)
  t.start()


# --- INICJALIZACJA BOTA ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
DATA_FILE = 'economy.json'


# --- SYSTEM BAZY DANYCH (JSON) ---
def load_data():
  if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
      json.dump({}, f)
  try:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
      return json.load(f)
  except Exception:
    return {}


def save_data(data):
  with open(DATA_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)


def get_user_data(data, user_id):
  user_id_str = str(user_id)
  if user_id_str not in data:
    data[user_id_str] = {'wallet': 0, 'bank': 0}

  if 'wallet' not in data[user_id_str]:
    data[user_id_str]['wallet'] = data[user_id_str].get('cash', 0)
  if 'bank' not in data[user_id_str]:
    data[user_id_str]['bank'] = data[user_id_str].get('bank_balance', 0)

  return data[user_id_str]


# --- KONFIGURACJA EKONOMII HAZE RP ---

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

SHOP_ITEMS = {
    'prawo jazdy b': {
        'name': 'Prawo Jazdy B',
        'price': 2500,
        'role_id': 1563214789512138864,
    },
    'prawo jazdy c': {
        'name': 'Prawo Jazdy C',
        'price': 3000,
        'role_id': 1563215060334280837,
    },
    'karta wedkarska': {
        'name': 'Karta Wędkarska',
        'price': 700,
        'role_id': 1563215061227667487,
    },
    'karta wędkarska': {
        'name': 'Karta Wędkarska',
        'price': 700,
        'role_id': 1563215061227667487,
    },
    'pozwolenie na bron': {
        'name': 'Pozwolenie na Broń',
        'price': 2800,
        'role_id': 1563215061697175622,
    },
    'pozwolenie na broń': {
        'name': 'Pozwolenie na Broń',
        'price': 2800,
        'role_id': 1563215061697175622,
    },
    'colt': {'name': 'Colt', 'price': 25000, 'role_id': 1563215062544421034},
    'beretta': {
        'name': 'Beretta',
        'price': 24000,
        'role_id': 1563215063056261140,
    },
    'lom': {'name': 'Łom', 'price': 250, 'role_id': 1563215064482455683},
    'łom': {'name': 'Łom', 'price': 250, 'role_id': 1563215064482455683},
    'noz': {'name': 'Nóż', 'price': 200, 'role_id': 1563215063635075082},
    'nóż': {'name': 'Nóż', 'price': 200, 'role_id': 1563215063635075082},
    'baseball': {
        'name': 'Kij Baseballowy',
        'price': 400,
        'role_id': 1563215064884969573,
    },
    'kij baseballowy': {
        'name': 'Kij Baseballowy',
        'price': 400,
        'role_id': 1563215064884969573,
    },
}

ALLOWED_CASH_ROLES = {
    1562153601382490234,
    1562152425471742023,
    1562153152491552819,
}

collect_cooldowns = {}
work_cooldowns = {}
hustle_cooldowns = {}
crime_cooldowns = {}


@bot.event
async def on_ready():
  print(f'✅ Bot {bot.user.name} wystartował pomyślnie!')


# --- KOMENDA: !bal ---
@bot.command(aliases=['balance', 'konto', 'stan'])
async def bal(ctx, member: discord.Member = None):
  target = member or ctx.author
  data = load_data()
  user = get_user_data(data, target.id)

  wallet_val = user['wallet']
  bank_val = user['bank']
  total_val = wallet_val + bank_val

  embed = discord.Embed(
      title=f'💳 Stan konta: {target.display_name}',
      color=discord.Color.gold(),
      timestamp=datetime.now(),
  )
  if target.avatar:
    embed.set_thumbnail(url=target.avatar.url)

  embed.add_field(
      name='💵 Portfel (Gotówka)', value=f'```\n{wallet_val:,} PLN\n```', inline=True
  )
  embed.add_field(
      name='🏦 Bank (Konto)', value=f'```\n{bank_val:,} PLN\n```', inline=True
  )
  embed.add_field(
      name='📊 Łączny majątek', value=f'**{total_val:,} PLN**', inline=False
  )
  embed.set_footer(
      text='Haze RolePlay • System Ekonomii',
      icon_url=ctx.guild.icon.url if ctx.guild.icon else None,
  )

  await ctx.send(embed=embed)


# --- KOMENDA: !top ---
@bot.command(aliases=['leaderboard', ' richest'])
async def top(ctx):
  data = load_data()
  if not data:
    await ctx.send('❌ Brak danych w bazie ekonomii!')
    return

  # Sortowanie użytkowników według łącznego majątku (portfel + bank)
  user_balances = []
  for user_id_str, vals in data.items():
    wallet = vals.get('wallet', vals.get('cash', 0))
    bank = vals.get('bank', vals.get('bank_balance', 0))
    total = wallet + bank
    user_balances.append((int(user_id_str), total, wallet, bank))

  user_balances.sort(key=lambda x: x[1], reverse=True)

  embed = discord.Embed(
      title='🏆 Top 10 Najbogatszych – HazeRP',
      color=discord.Color.gold(),
      timestamp=datetime.now(),
  )

  description = ''
  for index, (uid, total, wallet, bank) in enumerate(user_balances[:10], start=1):
    member = ctx.guild.get_member(uid)
    name = member.display_name if member else f'Użytkownik {uid}'
    medal = (
        '🥇'
        if index == 1
        else '🥈'
        if index == 2
        else '🥉'
        if index == 3
        else f'`#{index}`'
    )
    description += (
        f'{medal} **{name}**\n   💰 Majątek: **{total:,} PLN** (Portfel:'
        f' `{wallet:,}`, Bank: `{bank:,}`)\n\n'
    )

  embed.description = (
      description
      if description
      else 'Brak graczy w rankingach.'
  )
  embed.set_footer(text='Haze RolePlay • Ranking Bogaczy')
  await ctx.send(embed=embed)


# --- KOMENDA: !dep ---
@bot.command(aliases=['deposit'])
async def dep(ctx, amount: str = None):
  if amount is None:
    embed = discord.Embed(
        title='❌ Błąd składni',
        description='Podaj kwotę do wpłaty, np. `!dep 50` lub `!dep all`!',
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    return

  data = load_data()
  user = get_user_data(data, ctx.author.id)

  if amount.lower() == 'all':
    dep_amount = user['wallet']
  else:
    try:
      dep_amount = int(amount)
    except ValueError:
      embed = discord.Embed(
          title='❌ Błąd kwoty',
          description='Podaj poprawną liczbę lub słowo `all`!',
          color=discord.Color.red(),
      )
      await ctx.send(embed=embed)
      return

  if dep_amount <= 0:
    embed = discord.Embed(
        title='❌ Błąd kwoty',
        description='Kwota wpłaty musi być większa niż 0 PLN!',
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    return

  if user['wallet'] < dep_amount:
    embed = discord.Embed(
        title='💸 Brak funduszy',
        description=(
            f'Nie masz tylu pieniędzy w portfelu!\nPosiadasz tylko'
            f' **{user["wallet"]:,} PLN**.'
        ),
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    return

  user['wallet'] -= dep_amount
  user['bank'] += dep_amount
  save_data(data)

  embed = discord.Embed(
      title='🏦 Wpłata do Banku',
      description=(
          f'Wpłacono **{dep_amount:,} PLN** do bezpiecznego banku.\n\n💳'
          f' Portfel: **{user["wallet"]:,} PLN**\n🏦 Bank: **{user["bank"]:,}'
          ' PLN**'
      ),
      color=discord.Color.green(),
  )
  await ctx.send(embed=embed)


# --- KOMENDA: !with / !withdraw (Wypłata z banku) ---
@bot.command(name='with', aliases=['withdraw'])
async def with_cmd(ctx, amount: str = None):
  if amount is None:
    embed = discord.Embed(
        title='❌ Błąd składni',
        description='Podaj kwotę do wypłaty, np. `!with 50` lub `!with all`!',
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    return

  data = load_data()
  user = get_user_data(data, ctx.author.id)

  # Sprawdzenie słowa 'all'
  if amount.lower() == 'all':
    with_amount = user['bank']
  else:
    try:
      with_amount = int(amount)
    except ValueError:
      embed = discord.Embed(
          title='❌ Błąd kwoty',
          description='Podaj poprawną liczbę lub słowo `all`!',
          color=discord.Color.red(),
      )
      await ctx.send(embed=embed)
      return

  if with_amount <= 0:
    embed = discord.Embed(
        title='❌ Błąd kwoty',
        description='Kwota wypłaty musi być większa niż 0 PLN!',
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    return

  if user['bank'] < with_amount:
    embed = discord.Embed(
        title='💸 Brak funduszy w banku',
        description=(
            f'Nie masz tylu pieniędzy w banku!\nPosiadasz tam tylko'
            f' **{user["bank"]:,} PLN**.'
        ),
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    return

  # Wykonanie wypłaty i zapis w bazie
  user['bank'] -= with_amount
  user['wallet'] += with_amount
  save_data(data)

  embed = discord.Embed(
      title='🏦 Wypłata z Banku',
      description=(
          f'Wypłacono **{with_amount:,} PLN** z konta bankowego.\n\n💳'
          f' Portfel: **{user["wallet"]:,} PLN**\n🏦 Bank: **{user["bank"]:,}'
          ' PLN**'
      ),
      color=discord.Color.blue(),
  )
  await ctx.send(embed=embed)
  
# --- KOMENDA: !collect ---
@bot.command()
async def collect(ctx):
  user_id = ctx.author.id
  now = datetime.now()

  if user_id in collect_cooldowns:
    next_collect_time = collect_cooldowns[user_id] + timedelta(hours=24)
    if now < next_collect_time:
      remaining = next_collect_time - now
      hours, remainder = divmod(int(remaining.total_seconds()), 3600)
      minutes, _ = divmod(remainder, 60)

      embed = discord.Embed(
          title='⏳ Czas oczekiwania',
          description=(
              f'Wypłatę możesz odebrać ponownie za **{hours} godz. i'
              f' {minutes} min.**!'
          ),
          color=discord.Color.red(),
      )
      await ctx.send(embed=embed)
      return

  total_payout = 0
  matched_roles = []

  for role in ctx.author.roles:
    if role.id in ROLE_PAYOUTS:
      amount = ROLE_PAYOUTS[role.id]
      total_payout += amount
      matched_roles.append(f'• **{role.name}**: +{amount:,} PLN')

  if total_payout == 0:
    embed = discord.Embed(
        title='❌ Brak uprawnień',
        description=(
            'Nie posiadasz żadnej roli uprawniającej do pobrania wypłaty!'
        ),
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    return

  data = load_data()
  user_data = get_user_data(data, user_id)
  user_data['wallet'] += total_payout
  save_data(data)

  collect_cooldowns[user_id] = now
  roles_str = '\n'.join(matched_roles)

  embed = discord.Embed(
      title='💰 Dzienna Wypłata',
      description=(
          f'Pomyślnie odebrano dzienną wypłatę w wysokości **{total_payout:,}'
          ' PLN**!\n\n📜 **Otrzymane wynagrodzenie:**\n'
          + roles_str
      ),
      color=discord.Color.green(),
  )
  embed.set_footer(text='Pieniądze zostały przelane bezpośrednio do portfela.')
  await ctx.send(embed=embed)


# --- KOMENDA: !work ---
@bot.command()
async def work(ctx):
  user_id = ctx.author.id
  now = datetime.now()

  if user_id in work_cooldowns:
    next_work_time = work_cooldowns[user_id] + timedelta(hours=5)
    if now < next_work_time:
      remaining = next_work_time - now
      hours, remainder = divmod(int(remaining.total_seconds()), 3600)
      minutes, _ = divmod(remainder, 60)
      embed = discord.Embed(
          title='⏳ Czas na odpoczynek',
          description=(
              f'Jesteś zmęczony pracą! Możesz popracować ponownie za **{hours}'
              f' godz. i {minutes} min.**'
          ),
          color=discord.Color.red(),
      )
      await ctx.send(embed=embed)
      return

  earnings = random.randint(100, 300)

  data = load_data()
  user = get_user_data(data, user_id)
  user['wallet'] += earnings
  save_data(data)

  work_cooldowns[user_id] = now

  embed = discord.Embed(
      title='🛠️ Praca',
      description=(
          f'{ctx.author.mention}, uczciwie przepracowałeś swoją zmianę i'
          f' zarobiłeś **{earnings:,} PLN**!'
      ),
      color=discord.Color.green(),
  )
  await ctx.send(embed=embed)


# --- KOMENDA: !hustle ---
@bot.command()
async def hustle(ctx):
  user_id = ctx.author.id
  now = datetime.now()

  if user_id in hustle_cooldowns:
    next_hustle_time = hustle_cooldowns[user_id] + timedelta(hours=8)
    if now < next_hustle_time:
      remaining = next_hustle_time - now
      hours, remainder = divmod(int(remaining.total_seconds()), 3600)
      minutes, _ = divmod(remainder, 60)
      embed = discord.Embed(
          title='⏳ Szybki opór',
          description=(
              f'Kolejna fucha będzie dostępna za **{hours} godz. i'
              f' {minutes} min.**'
          ),
          color=discord.Color.red(),
      )
      await ctx.send(embed=embed)
      return

  earnings = random.randint(50, 500)

  data = load_data()
  user = get_user_data(data, user_id)
  user['wallet'] += earnings
  save_data(data)

  hustle_cooldowns[user_id] = now

  embed = discord.Embed(
      title='💼 Szybka Fucha',
      description=(
          f'{ctx.author.mention}, ogarnąłeś szybki interes i na Twoim koncie'
          f' ląduje **{earnings:,} PLN**!'
      ),
      color=discord.Color.dark_theme(),
  )
  await ctx.send(embed=embed)


# --- KOMENDA: !crime ---
@bot.command()
async def crime(ctx):
  user_id = ctx.author.id
  now = datetime.now()

  if user_id in crime_cooldowns:
    next_crime_time = crime_cooldowns[user_id] + timedelta(hours=12)
    if now < next_crime_time:
      remaining = next_crime_time - now
      hours, remainder = divmod(int(remaining.total_seconds()), 3600)
      minutes, _ = divmod(remainder, 60)
      embed = discord.Embed(
          title='🚨 Niebezpiecznie na ulicy',
          description=(
              'Policja patroluje teren! Kolejną akcję możesz wykonać za'
              f' **{hours} godz. i {minutes} min.**'
          ),
          color=discord.Color.red(),
      )
      await ctx.send(embed=embed)
      return

  data = load_data()
  user = get_user_data(data, user_id)

  success = random.choices([True, False], weights=[70, 30])[0]

  if success:
    earnings = random.randint(200, 1000)
    user['wallet'] += earnings
    embed = discord.Embed(
        title='🥷 Udana Akcja Przestępcza',
        description=(
            f'{ctx.author.mention}, zgubiłeś pościg i zgarnąłeś **{earnings:,}'
            ' PLN**!'
        ),
        color=discord.Color.dark_red(),
    )
  else:
    fine = random.randint(100, 300)
    user['wallet'] = max(0, user['wallet'] - fine)
    embed = discord.Embed(
        title='🚔 Wpadka z Policją!',
        description=(
            f'{ctx.author.mention}, zostałeś złapany! Zapłaciłeś mandat w'
            f' wysokości **{fine:,} PLN**.'
        ),
        color=discord.Color.red(),
    )

  save_data(data)
  crime_cooldowns[user_id] = now
  await ctx.send(embed=embed)


# --- KOMENDA: !sklep ---
@bot.command(aliases=['shop', 'sklepik'])
async def sklep(ctx):
  embed = discord.Embed(
      title='🛍️ Oferta Sklepu HazeRP',
      description=(
          'Aby kupić wybrany przedmiot, użyj komendy: `!kup <nazwa>`\n'
          'Przykład: `!kup Colt` lub `!kup Prawo Jazdy B`\n'
          '─────────────────────────────'
      ),
      color=discord.Color.gold(),
  )

  # Unikalne wyświetlanie tylko głównych nazw przedmiotów
  unique_items = [
      'prawo jazdy b',
      'prawo jazdy c',
      'karta wedkarska',
      'pozwolenie na bron',
      'colt',
      'beretta',
      'lom',
      'noz',
      'baseball',
  ]
  for key in unique_items:
    item = SHOP_ITEMS[key]
    embed.add_field(
        name=f"🔹 {item['name']}",
        value=f"Cena: **{item['price']:,} PLN**",
        inline=True,
    )

  embed.set_footer(
      text='Pieniądze na zakup są pobierane bezpośrednio z Twojego portfela.'
  )
  await ctx.send(embed=embed)


# --- KOMENDA: !kup ---
@bot.command()
async def kup(ctx, *, item_name: str = None):
  if not item_name:
    embed = discord.Embed(
        title='❌ Błąd składni',
        description=(
            'Podaj nazwę przedmiotu, który chcesz kupić!\n'
            'Zobacz pełną listę pod komendą `!sklep`.'
        ),
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    return

  item_key = item_name.lower().strip()

  if item_key not in SHOP_ITEMS:
    embed = discord.Embed(
        title='❌ Nie znaleziono przedmiotu',
        description=(
            'Taki przedmiot nie istnieje w sklepie! Wpisz `!sklep`, aby'
            ' zobaczyć ofertę.'
        ),
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    return

  item = SHOP_ITEMS[item_key]
  price = item['price']
  role_id = item['role_id']

  data = load_data()
  user = get_user_data(data, ctx.author.id)

  if user['wallet'] < price:
    embed = discord.Embed(
        title='💸 Brak funduszy',
        description=(
            f'Masz za mało gotówki w portfelu!\nBrakująca kwota:'
            f' **{price - user["wallet"]:,} PLN**.'
        ),
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    return

  role = ctx.guild.get_role(role_id)
  if role and role in ctx.author.roles:
    embed = discord.Embed(
        title='⚠️ Przedmiot posiadany',
        description=f"Posiadasz już przedmiot/licencję: **{item['name']}**!",
        color=discord.Color.orange(),
    )
    await ctx.send(embed=embed)
    return

  user['wallet'] -= price
  save_data(data)

  if role:
    try:
      await ctx.author.add_roles(role)
      embed = discord.Embed(
          title='🛍️ Zakup udany!',
          description=(
              f"Zakupiono **{item['name']}** za **{price:,} PLN**!\nOtrzymano"
              f' rolę: {role.mention}'
          ),
          color=discord.Color.green(),
      )
      await ctx.send(embed=embed)
    except discord.Forbidden:
      embed = discord.Embed(
          title='⚠️ Problem z uprawnieniami',
          description=(
              'Pieniądze zostały pobrane, ale bot nie ma uprawnień do nadania'
              ' roli!'
          ),
          color=discord.Color.orange(),
      )
      await ctx.send(embed=embed)
  else:
    embed = discord.Embed(
        title='⚠️ Błąd konfiguracyjny',
        description=(
            'Pieniądze zostały pobrane, ale nie znaleziono roli na serwerze.'
        ),
        color=discord.Color.orange(),
    )
    await ctx.send(embed=embed)


# --- KOMENDA: !pay (elastyczna kolejność argumentów) ---
@bot.command()
async def pay(ctx, arg1: str = None, arg2: str = None):
  # Obsługa obu wariantów: !pay @Gracz 500 oraz !pay 500 @Gracz
  member = None
  amount = None

  if ctx.message.mentions:
    member = ctx.message.mentions[0]
    # Szukamy, który argument to kwota
    for arg in [arg1, arg2]:
      if arg and not arg.startswith('<@'):
        try:
          amount = int(arg)
        except ValueError:
          pass

  if not member or not amount:
    embed = discord.Embed(
        title='❌ Błąd składni',
        description=(
            'Użyj formatu: `!pay @Odbiorca <kwota>`\nPrzykład: `!pay @Gracz 500`'
        ),
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    return

  if amount <= 0:
    embed = discord.Embed(
        title='❌ Błąd kwoty',
        description='Kwota przelewu musi być większa niż 0 PLN!',
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    return

  if member.id == ctx.author.id or member.bot:
    embed = discord.Embed(
        title='❌ Błąd odbiorcy',
        description='Nie możesz przelać pieniędzy sobie ani botowi!',
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    return

  data = load_data()
  sender = get_user_data(data, ctx.author.id)

  if sender['wallet'] < amount:
    embed = discord.Embed(
        title='💸 Brak funduszy',
        description=(
            f'Nie masz wystarczająco pieniędzy w portfelu!\nPosiadasz tylko'
            f' **{sender["wallet"]:,} PLN**.'
        ),
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    return

  receiver = get_user_data(data, member.id)

  sender['wallet'] -= amount
  receiver['wallet'] += amount
  save_data(data)

  embed = discord.Embed(
      title='💸 Przelew prywatny',
      description=(
          f'{ctx.author.mention} przekazał(a) **{amount:,} PLN** dla'
          f' {member.mention}!'
      ),
      color=discord.Color.blue(),
  )
  await ctx.send(embed=embed)


# --- KOMENDA: !cash ---
@bot.command()
async def cash(ctx, amount: int = None):
  user_role_ids = {role.id for role in ctx.author.roles}
  if not user_role_ids.intersection(ALLOWED_CASH_ROLES):
    embed = discord.Embed(
        title='❌ Brak uprawnień',
        description='Nie posiadasz uprawnień do użycia tej komendy!',
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    return

  if amount is None or amount <= 0:
    embed = discord.Embed(
        title='❌ Błąd kwoty',
        description='Podaj poprawną kwotę do dodania, np. `!cash 10000`!',
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    return

  data = load_data()
  user = get_user_data(data, ctx.author.id)

  user['wallet'] += amount
  save_data(data)

  embed = discord.Embed(
      title='👑 Doładowanie Administracyjne',
      description=(
          f'Dodano **{amount:,} PLN** do Twojego portfela!\nAktualny stan'
          f' portfela: **{user["wallet"]:,} PLN**'
      ),
      color=discord.Color.purple(),
  )
  await ctx.send(embed=embed)


# --- START BOTA ---
TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN:
  keep_alive()
  bot.run(TOKEN)
else:
  print('❌ Brak tokena DISCORD_TOKEN w środowisku!')
