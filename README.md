# discord-timers

A simple extension for discord.py which provides basic timer support.

## Installing

```bash
pip install discord-timers -U
```

## Example

```python
import datetime

from discord.ext import commands, timers


bot = commands.Bot(command_prefix="!")
bot.timer_manager = timers.TimerManager(bot)


@bot.command(name="remind")
async def remind(ctx, time, *, text):
    """Remind to do something on a date.
    
    The date must be in ``Y/M/D`` format."""
    date = datetime.datetime(*map(int, time.split("/")))
    
    bot.timer_manager.create_timer("reminder", date, args=(ctx.channel.id, ctx.author.id, text))
    # or without the manager
    timers.Timer(bot, "reminder", date, args=(ctx.channel.id, ctx.author.id, text)).start()

@bot.event
async def on_reminder(channel_id, author_id, text):
    channel = bot.get_channel(channel_id)
    
    await channel.send("Hey, <@{0}>, remember to: {1}".format(author_id, text))


bot.run("token")
```