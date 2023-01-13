"""
MIT License
Copyright (c) 2020 WebKide [d.id @323578534763298816]
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import discord, asyncio, random, textwrap, traceback

from discord.ext import commands
from enum import Enum

_dict = {
    'afraid': '((ﾟ□ﾟ;))',
    'ahh': '“ヽ(´▽｀)ノ”',
    'bday': 'ღゝ◡╹)ノ♡ ✯ℋᵃᵖᵖʸ ℬⁱʳᵗʰᵈᵃʸ✯',
    'bunbun': '(ヽ/)\n(°⌄°)\n(___)ﾉ',
    'coffee': '✧.◟(^ヮ^)◞.”旦~',
    'doggo': 'ʷᵒᶠᶠ ▽･ｪ･▽ﾉ”',
    'doki': '(⸝⸝°ᗣ°⸝⸝)ᒄᵒᵏⁱ',
    'doncare': '┐( ˘˘)┌',
    'excited': '(˵¯͒⌄¯͒˵)',
    'fight': '(ง •̀•́)ง',
    'fury': '!(ﾉ｀◎´)ﾉᶠᶠˢミ',
    'go': '(ノ°ο°)ノ ᵍᵒ',
    'gurl': '⌒°(ᴖ◡ᴖ)°⌒',
    'handshake': '( ＾◡＾)っ',
    'happy': '₍₍◝(°꒳°)◜₎₎',
    'holyshit': '┏(｀ﾟдﾟ)┛ʰᵒˡʸ ˢʰⁱᵗ',
    'hugglies': '(ɔˆ ³(ˆ⌣ˆc)',
    'joy': 'o(〃’▽’〃)o',
    'kickass': 'ヽ( ･∀･)ﾉ┌┛Σ(ノ `Д´)ノ',
    'kisses': '✩•̩̩͙"˚(_/c”ˆ⊰⊱ˆɔ‿)*˚"•̩̩͙✩',
    'lewd': '╰U╯ ԅ(≖‿≖ԅ)',
    'lewdisgewd': '( • Y • )ԅ(≖‿≖ԅ)',
    'linebreak': "·°'-.,¸¸.·°'-,..,.-'°-,_,.-'°·",
    'love': '(ღˇ◡ˇ)~ Lᵒᵛᵉ ʸᵒᵘ♡',
    'lurk': '__( ⚆  ⚆ )__',
    'magik': '(∩｀-´)⊃━☆ﾟ.*･｡ﾟ',
    'mate': 'ᵐᵃᵗᵉ“ヽ(´▽｀)ノ”',
    'meh': '┐( ˘ㅅ˘)┌',
    'music': '◖|⌣ ‿ ⌣|◗˳♪⁎˚♫˳',
    'mwack': '(｀3´)ᵐʷᵃᶜᵏ(`ε ´ )',
    'never': '( ᗒᗣᗕ)!ⁿᵉᵛᵉʳ',
    'nosebleed': '⁽͑˙˚̀༎˚́˙⁾̉ ',
    'outahere': 'ε=ε=ε=ε=┏(;￣▽￣)┛',
    'panic': 'ヾ(ﾟ∀ﾟ○)ﾂ三ヾ(●ﾟ∀ﾟ)ﾉ',
    'rain': '、ヽ｀、ヽ｀个o(･･｡)｀ヽ、｀ヽ、',
    'runaway': '..･ヾ(。￣□￣)ﾂ',
    'scared': '˛ ˛ (⊙﹏⊙ ) ̉ ̉',
    'sleep': '(＿ ＿)Ｚᴢｚ',
    'smooch': '(づ￣ 3￣)づˢᵐᵒᵒᶜʰ',
    'sorry': '｡(^▽^)ゞˢᵒʳʳʸ',
    'sparks': '(ﾉ^ヮ^)ﾉ:・ﾟ✧',
    'stfu': 'sʜᴜᴛ ╭(°ㅂ°)╮ ╰(°ㅂ°)╯ ᵘᵖ',
    'strong': 'ˢᵗʳᵒⁿᵍ ᕙ(⇀‸↼‶)ᕗ',
    'waves': '~(‾▿‾)~',
    'what': 'ʷʰᵃᵗ..(・ヘ・?)',
    'whocares': 'ʅ(‾◡◝)ʃ',
    'wyou': '(ｼ;ﾟДﾟ)ｼ!!',
    'noway': '(눈_눈)',
    'disappointed': '(；⌣̀_⌣́)',
    'yaright': '(¬_¬ )',
    'sure': '(￢_￢)',
    'apologies': '(*_ _)人',
    'hiding': '|･д･)ﾉ',
    'asleep': '(￣ρ￣)..zzZ',
    'annoyed': '＼＼\\٩(๑`^´๑)۶//／／',
    'bff': '( ・∀・)爻(・ω・ )',
    'eww': '(¬_¬`)ԅ(￣ε￣ԅ)',
    'cheers': '(ღ￣▽￣)旦 且(´∀`✿)',
    'angel': 'ଘ(੭ˊ꒳​ˋ)੭✧',
    'drowning': '‿︵‿︵‿︵‿ヽ(°□° )ノ︵‿︵‿︵‿︵',
    'drool': '(￣﹃￣)',
    'brr': '(っ•﹏•)っ',
    'hifive': 'ヾ(・ω・)人(・ω・)ノ',
    'fear': '..・ヾ(。＞＜)シ',
    'puke': '_:(´ཀ` ):_',
    'anger': '(ﾉಥ益ಥ)ﾉ',
    'furious': '٩(╬ʘ益ʘ╬)۶',
    'therethere': '(ｏ・_・)ノ”(ノ_<、)',
    'proud': '<(￣︶￣)>',
    'joy': '☆*:.｡.o(≧▽≦)o.｡.:*☆',
    'chase': 'ε=ε=(○｀益´)ﾉｼ Σ(っﾟДﾟ)っ',
    'pissed': '٩(´◣д◢`੭)',
    'why': 'ლ(ಠ益ಠ)ლ',
    'bowing': '●౹౽',
    'cat': '(=ↀᆺↀ=)✧',
    'kitty': '(ꃋิꎴꃋิ)',
    'dafuq': '◝₍ᴑ̑ДO͝₎◞',
    'owell': '╰(◉ᾥ◉)╯',
    'hey': '(•̀⌓•́)シ',
    'nihongo': '顔文字'
}

dev_list = [323578534763298816]

d = '“Scissors cut paper, paper covers rock, rock crushes lizard, ' \
    'lizard poisons Spock, Spock smashes scissors, scissors decapitate lizard, ' \
    'lizard eats paper, paper disproves Spock, Spock vaporizes rock and, ' \
    'as it’s always been, rock crushes scissors.”\n    ~Sheldon Cooper,\n\n' \
    'The Big Bang Theory S02E08 — “The Lizard-Spock Expansion”\n\n'


class RPSLS(Enum):
    rock = "\N{RAISED FIST} **Rock!**"
    paper = "\N{PAGE FACING UP} **Paper!**"  # \N{RAISED HAND WITH FINGERS SPLAYED}
    scissors = "\N{BLACK SCISSORS} **Scissors!**"
    lizard = "\N{LIZARD} **Lizard!**"
    spock = "\N{RAISED HAND WITH PART BETWEEN MIDDLE AND RING FINGERS} **Spock!**"


class RPSLSParser:
    def __init__(self, argument):
        argument = argument.lower()
        if argument == "rock":
            self.choice = RPSLS.rock
        elif argument == "paper":
            self.choice = RPSLS.paper
        elif argument == "scissors":
            self.choice = RPSLS.scissors
        elif argument == "lizard":
            self.choice = RPSLS.lizard
        elif argument == "spock":
            self.choice = RPSLS.spock
        else:
            return


class TextGames(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ fun TextGames to challenge the bot """
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.mod_color = discord.Colour(0x7289da)  # Blurple
        self.user_color = discord.Colour(0xed791d)  # Orange
        self.sessions = set()
        self.d = '```css\n“Scissors cut paper, paper covers rock, rock crushes lizard, ' \
              'lizard poisons Spock, Spock smashes scissors, scissors decapitate lizard, ' \
              'lizard eats paper, paper disproves Spock, Spock vaporizes rock and, ' \
              'as it’s always been, rock crushes scissors.”``` ~Sheldon Cooper,\n' \
              'The Big Bang Theory S02E08 — “The Lizard-Spock Expansion”'


    # +------------------------------------------------------------+
    # |         Rock paper, scissors, lizard, Spock                |
    # +------------------------------------------------------------+
    @commands.command(description=d, aliases=['rpsls', 'rps'], no_pm=True)
    async def settle(self, ctx, your_choice: RPSLSParser = None):
        """ Play: rock paper scissors lizard spock
        
        Usage:
        {prefix}settle rock
        
        Note: game variation inspired in TheBigBangTheory
        """
        await ctx.channel.trigger_typing()
        author = ctx.message.author.display_name
        mod_bot = self.bot.user.display_name
        errored = f"{self.d}\n\n**Usage:**\n{ctx.prefix}{ctx.invoked_with} [rock, paper, scissors, lizard, or spock]"

        if your_choice is None:    return await ctx.send(errored, delete_after=69)

        elif your_choice is not None:
            try:
                player_choice = your_choice.choice
                available = RPSLS.rock, RPSLS.paper, RPSLS.scissors, RPSLS.lizard, RPSLS.spock
                bot_choice = random.choice(available)
                cond = {
                    (RPSLS.rock, RPSLS.paper): False,
                    (RPSLS.rock, RPSLS.scissors): True,
                    (RPSLS.rock, RPSLS.lizard): True,
                    (RPSLS.rock, RPSLS.spock): False,
                    (RPSLS.paper, RPSLS.rock): True,
                    (RPSLS.paper, RPSLS.scissors): False,
                    (RPSLS.paper, RPSLS.lizard): False,
                    (RPSLS.paper, RPSLS.spock): True,
                    (RPSLS.scissors, RPSLS.rock): False,
                    (RPSLS.scissors, RPSLS.paper): True,
                    (RPSLS.scissors, RPSLS.lizard): True,
                    (RPSLS.scissors, RPSLS.spock): False,
                    (RPSLS.lizard, RPSLS.rock): False,
                    (RPSLS.lizard, RPSLS.paper): True,
                    (RPSLS.lizard, RPSLS.scissors): False,
                    (RPSLS.lizard, RPSLS.spock): True,
                    (RPSLS.spock, RPSLS.rock): True,
                    (RPSLS.spock, RPSLS.paper): False,
                    (RPSLS.spock, RPSLS.scissors): True,
                    (RPSLS.spock, RPSLS.lizard): False
                }
                e = discord.Embed()
                e.add_field(name=f'{mod_bot} chose:', value=f'{bot_choice.value}', inline=True)
                e.add_field(name=f'{author} chose:', value=f'{player_choice.value}', inline=True)

                if bot_choice == player_choice:    outcome = None

                else:    outcome = cond[(player_choice, bot_choice)]

                if outcome is True:
                    e.color = (discord.Colour(0xed791d))
                    e.set_footer(text="\N{SMALL ORANGE DIAMOND} You win!")
                    await ctx.channel.send(embed=e)

                elif outcome is False:
                    e.color = (discord.Colour(0xe000ff))
                    e.set_footer(text="\N{NO ENTRY SIGN} You lose...")
                    await ctx.channel.send(embed=e)

                else:
                    e.color = (discord.Colour(0x7289da))
                    e.set_footer(text="\N{JAPANESE SYMBOL FOR BEGINNER} We're square")
                    await ctx.channel.send(embed=e)

            except AttributeError:    return await ctx.send(errored, delete_after=69)

    # +------------------------------------------------------------+
    # |                   Choose from list                         |
    # +------------------------------------------------------------+
    @commands.command(description='Choose from a list of items', no_pm=True)
    async def choose(self, ctx, *, options: str = None):
        """ Pick an item from a list
        
        Usage:
        {prefix}choose <item1>, <item2> or [item3]
        
        Note: accepted separators are , | or
        """
        msg = f'Write at least two options separated by a comma: ' \
              f'```css\n{ctx.prefix}{ctx.invoked_with} eat, sleep, read or ' \
              f'walk```'.replace('<@726650866169282600>', f'@{self.bot.user.name}')

        if options is None:    return await ctx.send(msg, delete_after=23)

        if options is not None:
            valid_separators = [',', '|', ' or ']

            if any(x in options for x in valid_separators):
                skd = options.replace(',', ', ').replace(' or ', ', ').replace('|', ', ') \
                    .replace('.', ', ').replace('  ', ' ')
                picked = random.choice(skd.split(', '))
                x = f'```ruby\nOptions:\n{skd}```\N{SMALL ORANGE DIAMOND} I choose: **`{picked}`**'

                try:
                    e = discord.Embed(color=0xed791d)
                    e.description = x.replace(' , ', ', ')
                    await ctx.send(embed=e)

                except discord.Forbidden:  # FORBIDDEN (status code: 403): Missing Permissions
                    result = f'I choose **{picked}** for you.'
                    return await ctx.send(result)

            else:    return await ctx.send(msg, delete_after=23)

        else:    return await ctx.send(msg, delete_after=23)

    # +------------------------------------------------------------+
    # |     Very basic cmd to flip names or coins                  |
    # +------------------------------------------------------------+
    @commands.command(description='Settle a dispute via coin toss', aliases=['toss', 'tossacoin'], no_pm=True)
    async def flip(self, ctx, *, something: str = None):
        """Flips a coin... or some text.
        Defaults to coin toss.
        
        Usage:
        {prefix}flip [text]
        {prefix}tossacoin
        """
        h = 'https://media.discordapp.net/attachments/541059392951418880/556977776771596333/1926_heads.png'
        t = 'https://media.discordapp.net/attachments/541059392951418880/556977839166193674/1926_tails.png'
        e = 'https://media.discordapp.net/attachments/541059392951418880/556978114354348052/1926_edge.png'
        c = '1926 Golden Dollar coin'
        if something is not None:
            char = "abcdefghijklmnopqrstuvwxyz"
            tran = "ɐqɔpǝɟƃɥᴉɾʞʅɯuodbɹsʇnʌʍxʎz"
            table = str.maketrans(char, tran)
            name = something.translate(table)
            char = char.upper()
            tran = "∀ꓭƆᗡƎℲ⅁HIſꓘ⅂WNOԀQᴚSꓕՈΛMX⅄Z"  # ⊥∩āɐ̱
            table = str.maketrans(char, tran)
            name = name.translate(table)

            em = discord.Embed(color=self.user_color)
            em.add_field(name=f'{ctx.message.author.display_name}', value=f'(╯°□°）╯︵ **{name[:1980][::-1]}**')

            try:    await ctx.send(embed=em)
            
            except discord.HTTPException:    await ctx.send(name[:1980][::-1])

        else:
            tossing = await ctx.send('Tosing the coin up in the air . . .')
            await ctx.channel.trigger_typing()
            flips = random.randint(3, 101)
            toss = f'After being tossed up,\nthe coin flipped\n{flips} times in the air\nand landed showing: '
            flop = f'*What are the odds?*\nAfter spinning {flips} times\nthe coin managed to\nland on its edge!'

            heads = discord.Embed(color=0xa84300, description=toss + '**Heads**')
            heads.set_thumbnail(url=h)
            heads.set_author(name='Coin Flip: Heads')
            heads.set_footer(text=c, icon_url=h)
            # heads.add_field(name='\N{SMALL ORANGE DIAMOND} Heads', value=c)

            tails = discord.Embed(color=0x1f8b4c, description=toss + '**Tails**')
            tails.set_thumbnail(url=t)
            tails.set_author(name='Coin Flip: Tails')
            tails.set_footer(text=c, icon_url=t)
            # tails.add_field(name='\N{SMALL ORANGE DIAMOND} Tails', value=c)

            edge = discord.Embed(color=0x23272a, description=flop)  # odds are 11/1
            edge.set_thumbnail(url=e)
            edge.set_author(name='Oops...', icon_url=e)
            edge.set_footer(text='...try again', icon_url=e)
            # edge.add_field(name='\N{BLACK SMALL SQUARE} Edge', value='...try again')

            result = random.choice([heads, tails, heads, tails, heads, tails, heads, tails, heads, tails, edge])

            await asyncio.sleep(8)

            try:    await tossing.edit(embed=result)

            except discord.HTTPException:    await ctx.send(random.choice(['Heads', 'Tails']))  # odds are 50/50

    # +------------------------------------------------------------+
    # |                     Guess                                  |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True)
    async def guess(self, ctx, number: int = None):
        """ Write number between 1 and 11
        
        Usage:
        {prefix}guess 7
        """
        answer = random.randint(1, 11)
        guessed_wrong = [
            'Not even close, the right number was:',
            'Better luck next time, the number was:',
            'How could you have known that the number was:',
            'Hmm, well, the right number was:',
            'Not getting any better, the number was:',
            'Right number was:'
        ]
        wrong = f'```{random.choice(guessed_wrong)} {answer}```'
        guessed_right = [
            'You guessed correctly!',
            'Everyone knew you could do it!',
            'You got the right answer!',
            'History will remember you...'
        ]
        right = f'```{random.choice(guessed_right)}```'
        u = ctx.message.author.display_name
        e = discord.Embed(color=self.user_color)

        if number is None:
            return await ctx.send('please write any number between 1 and 11', delete_after=23)

        if number is not None:
            if number < answer or number > answer:
                q_mark = '\N{OCTAGONAL SIGN}'
                e.add_field(name=f'{q_mark} {u} chose: `{number}`',
                            value=wrong, inline=True)
                try:    await ctx.send(embed=e)
                except discord.HTTPException:    await ctx.send(wrong)

            if number == answer:
                q_mark = '\N{SPORTS MEDAL}'
                e.add_field(name=f'{q_mark} {u} chose: `{answer}`',
                            value=right, inline=True)
                try:    await ctx.send(embed=e)
                except discord.HTTPException:    await ctx.send(right)

            else:    pass

    # +------------------------------------------------------------+
    # |                   KAOMOJI (∩｀-´)⊃━☆ﾟ.*･｡ﾟ                  |
    # +------------------------------------------------------------+
    @commands.command(description='Send cute kaomojis', no_pm=True)
    async def kaomoji(self, ctx, _name: str = None):
        '''Kawaii Kaomoji komandu desu! Sugoi!!'''
        if _name in _dict.keys():
            return await ctx.send(f'{ctx.message.author.mention}\n{_dict[_name]}')

        p = f'`{ctx.prefix}kaomoji`'
        await ctx.send(f'{p} **afraid**, {p} **ahh**, {p} **bday**, {p} **bunbun**, {p} **coffee**, {p} **doggo**, '\
                    f'{p} **doki**, {p} **doncare**, {p} **excited**, {p} **fight**, {p} **fury**, {p} **go**, '\
                    f'{p} **gurl**, {p} **handshake**, {p} **happy**, {p} **holyshit**, {p} **hugglies**, {p} **joy**, '\
                    f'{p} **kickass**, {p} **kisses**, {p} **lewd**, {p} **lewdisgewd**, {p} **linebreak**, {p} **love**, '\
                    f'{p} **lurk**, {p} **magik**, {p} **mate**, {p} **meh**, {p} **music**, {p} **mwack**, {p} **never**, '\
                    f'{p} **nosebleed**, {p} **outahere**, {p} **panic**, {p} **rain**, {p} **runaway**, {p} **scared**, '\
                    f'{p} **sleep**, {p} **smooch**, {p} **sorry**, {p} **sparks**, {p} **stfu**, {p} **strong**, '\
                    f'{p} **waves**, {p} **what**, {p} **wyou**', delete_after=23)


async def setup(bot):
    await bot.add_cog(TextGames(bot))
