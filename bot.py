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


# --- 3. !collect (co 24h za rolę) ---
@bot.command()
async def collect(ctx):
  wymagana_rola = 'Pracownik'
  rola = discord.utils.get(ctx.guild.roles, name=wymagana_rola)

  if not rola or rola not in ctx.author.roles:
    await ctx.send(
        f'❌ {ctx.author.mention}, nie posiadasz wymaganej roli (`{wymagana_rola}`)'
        ' do odebrania dziennej wypłaty!'
    )
    return

  bonus = 500
  user = get_user_data(ctx.author.id)
  user['wallet'] += bonus
  save_data(load_data())

  embed = discord.Embed(
      title='💰 Dzienna wypłata',
      description=(
          f'{ctx.author.mention}, odebrałeś swoje świadczenie za rolę w'
          f' wysokości **{bonus} PLN**!'
      ),
      color=discord.Color.gold(),
  )
  await ctx.send(embed=embed)


# --- 4. !bal / !balance ---
@bot.command(aliases=['balance'])
async def bal(ctx, member: discord.Member = None):
  target = member or ctx.author
  user = get_user_data(target.id)
  wallet = user['wallet']
  bank = user['bank']
  total = wallet + bank

  embed = discord.Embed(
      title=f'💳 Portfel: {target.display_name}', color=discord.Color.blue()
  )
  embed.set_thumbnail(url=target.display_avatar.url)
  embed.add_field(name='💵 Portfel (gotówka)', value=f'**{wallet} PLN**', inline=True)
  embed.add_field(name='🏦 Bank (konto)', value=f'**{bank} PLN**', inline=True)
  embed.add_field(name='📊 Łącznie majątek', value=f'**{total} PLN**', inline=False)
  await ctx.send(embed=embed)


# --- 5. !withdraw / !with ---
@bot.command(aliases=['with'])
async def withdraw(ctx, amount: str):
  user = get_user_data(ctx.author.id)

  if amount.lower() == 'all':
    amt = user['bank']
  else:
    try:
      amt = int(amount)
    except ValueError:
      await ctx.send(
          f'❌ {ctx.author.mention}, podaj poprawną kwotę do wypłaty!'
      )
      return

  if amt <= 0:
    await ctx.send(f'❌ {ctx.author.mention}, kwota musi być większa od 0!')
    return

  if user['bank'] < amt:
    await ctx.send(
        f'❌ {ctx.author.mention}, nie masz tylu pieniędzy w banku! (Masz:'
        f' {user["bank"]} PLN)'
    )
    return

  user['bank'] -= amt
  user['wallet'] += amt
  save_data(load_data())

  embed = discord.Embed(
      title='💸 Wypłata z banku',
      description=(
          f'{ctx.author.mention} wypłaciłeś **{amt} PLN** z banku do portfela.'
      ),
      color=discord.Color.green(),
  )
  await ctx.send(embed=embed)


# --- 6. !deposit / !dep ---
@bot.command(aliases=['dep'])
async def deposit(ctx, amount: str):
  user = get_user_data(ctx.author.id)

  if amount.lower() == 'all':
    amt = user['wallet']
  else:
    try:
      amt = int(amount)
    except ValueError:
      await ctx.send(
          f'❌ {ctx.author.mention}, podaj poprawną kwotę do wpłaty!'
      )
      return

  if amt <= 0:
    await ctx.send(f'❌ {ctx.author.mention}, kwota musi być większa od 0!')
    return

  if user['wallet'] < amt:
    await ctx.send(
        f'❌ {ctx.author.mention}, nie masz tylu pieniędzy w portfelu! (Masz:'
        f' {user["wallet"]} PLN)'
    )
    return

  user['wallet'] -= amt
  user['bank'] += amt
  save_data(load_data())

  embed = discord.Embed(
      title='🏦 Wpłata do banku',
      description=(
          f'{ctx.author.mention} wpłaciłeś **{amt} PLN** do bezpiecznego'
          ' banku.'
      ),
      color=discord.Color.green(),
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


@bot.command()
async def kup(ctx, *, item_name: str):
  item_name = item_name.lower()
  if item_name not in SHOP_ITEMS:
    await ctx.send(
        f'❌ {ctx.author.mention}, taki przedmiot nie istnieje w sklepie!'
        ' Sprawdź `!sklep`.'
    )
    return

  item = SHOP_ITEMS[item_name]
  price = item['price']
  role_name = item['role']

  user = get_user_data(ctx.author.id)
  if user['wallet'] < price:
    await ctx.send(
        f'❌ {ctx.author.mention}, masz za mało gotówki w portfelu! Brakuje Ci'
        f' **{price - user["wallet"]} PLN**.'
    )
    return

  user['wallet'] -= price
  save_data(load_data())

  role = discord.utils.get(ctx.guild.roles, name=role_name)
  if role:
    try:
      await ctx.author.add_roles(role)
      embed = discord.Embed(
          title='✅ Udany zakup!',
          description=(
              f'{ctx.author.mention}, pomyślnie zakupiłeś **{role_name}** za'
              f' **{price} PLN**. Rola została Ci nadana!'
          ),
          color=discord.Color.green(),
      )
      await ctx.send(embed=embed)
    except discord.Forbidden:
      await ctx.send(
          f'⚠️ {ctx.author.mention}, zakupiłeś przedmiot za {price} PLN, ale bot'
          ' nie ma uprawnień do nadania roli! (Przesuń rolę bota wyżej w'
          ' ustawieniach serwera).'
      )
  else:
    await ctx.send(
        f'⚠️ {ctx.author.mention}, pobrano {price} PLN, ale rola `{role_name}` nie'
        ' istnieje na tym serwerze! Stwórz ją w panelu.'
    )


# Uruchomienie serwera WWW i bota
keep_alive()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)
