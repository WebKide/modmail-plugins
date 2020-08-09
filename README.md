<div align="center">
<h1>「modmail-plugins」</h1>
<p><b><i>plugins to expand Modmail2020's functionality 🍆💦🍑</i></b></p>
</div>


<div align="center">
<img src="http://forthebadge.com/images/badges/made-with-crayons.svg?style=for-the-badge" alt="made with crayons"><br>
<img src="https://img.shields.io/badge/python-v3.7-12a4ff?style=for-the-badge&logo=python&logoColor=12a4ff">
<img src="https://img.shields.io/badge/library-discord%2Epy-ffbb10?style=for-the-badge">

<p>🛠️ if you experience a problem with any <b>modmail-plugin</b> in this repo, please open an issue or submit a pull-request</p>
<br><br>
</div>

> 🔸 by default the prefix is `?` followed by a command: `?calc` but if you changed the prefix, then replace `{p}` with your custom prefix: `{p}calc` becomes `b!calc` if your new prefix is `b!`


- - - -

## .:: ✔ Calculator ::. ##
🔸 <b>Installation</b>: `{p}plugin add WebKide/modmail-plugins/calculator@master`

- [x] `{p}calc` — powerful calculator command, supports addition, substraction, multiplication, division, PEMDAS...
#### Usage and examples ####
|    **operation**  	 	|    **usage example**  	 	|    **result output**    |
|:-----------------------:	|:-----------------------:	|:----------------------:	|
|  addition  |  `{p}calc 2+5`  |    7.0    |
|  substraction  |  `{p}calc 8 - 5.7`  |    2.3    |
|  multiplication  |  `{p}calc 7 x 5`  |    35.0    |
|  division  |  `{p}calc 9/4`  |    2.25    |
|  PEMDAS  |  `{p}calc 6 /2 x (1+ 2) `  |    9.0    |
|  long operation  |  `{p}calc 1,000+40 +1,000+30+ 1,000+20+1,000+10`  |    4100.0    |
|  round()  |  `{p}calc round(9 - 3 / (1/3)+1)`  |    1    |
|  exponent  |  `{p}calc (7^3)+(5x7)+6/6`  |    379.0    |
|  π  |  `{p}calc 23 * 2 * PI`  |    144.51    |
|  E  |  `{p}calc E ^ 2 * 50.13`  |    370.41    |
|  trig  | `{p}calc sin(30)*cos(45)*tan(-264)`  |    -0.06    |
|  trig  | `{p}calc sec(102.5)*csc(432)*cot(-23.45)`  |    -0.0    |


> as you can see, this calculator is very <i>flexible</i> and <b>powerful</b>

- - - -
<br>

## .:: ✔ Misc* ::. ##
🔸 <b>Installation</b>: `{p}plugin add WebKide/modmail-plugins/misc@master`

- [x] <b>`role`</b> - group commands to add/remove role to user
- [x] <b>`g`</b> - Send a msg to another channel
- [x] <b>`hackban`</b> - Ban someone using ID
- [ ] <b>`logo`</b> - Change Bot's avatar img
- [ ] <b>`name`</b> - Change Bot's name
- [x] <b>`purge`</b> - Delete a number of messages
- [x] <b>`sauce`</b> - Show source code for any command
- [x] <b>`say`</b> - Bot sends message
- [x] <b>`sayd`</b> - Sends message and deletes original
- - - -
<br>

## .:: ✔ on_message ::. ##
🔸 <b>Installation</b>: `{p}plugin add webkide/modmail-plugins/on_message@master`

- [x] bot responds to matching `[str]` in messages starting with "I am"
- - - -
<br>

## .:: Starboard2 ::. ##
- [ ] have to fix so it uses db correctly
- - - -
<br>

## .:: ✔ Translate ::. ##
🔸 <b>Installation</b>: `{p}plugin add WebKide/modmail-plugins/translate`

- [x] `{p}tr langs` — list of supported/available languages
- [x] `{p}tr <Language> <message>` — translate text from one language to another
- [x] `{p}tt <message>` — translate text from any language to English inside ticket threads
- [x] `{p}tat` — toggle (on/off) auto translate to English inside ticket threads
- [x] `{p}att` — auto translate text from any language to English inside ticket threads
- [ ] `{p}tr {default_english}` — defaults translation to English if no target language is provided
- - - -
<br>

## .:: ✔ Oracle ::. ##
🔸 <b>Installation</b>: `{p}plugin add WebKide/modmail-plugins/oracle@master`

- [x] `{p}8ball <question?>`
- [x] `{p}iching <question?>`
- [x] `{p}tarot reading`
- - - -
<br>

## .:: ✔ Timezone ::. ##
🔸 <b>Installation</b>: `{p}plugin add WebKide/modmail-plugins/timezone@master`

- [x] `{p}tz :flag_gb:` — get timezone using a flag
- [x] `{p}tz EST` — get timezone using abbreviation
- [x] `{p}tz Mexico` — get timezone usinc country
- - - -
<br>

## .:: TextGames ::. ##
🔸 <b>Installation</b>: `{p}plugin add WebKide/modmail-plugins/textgames@master`

- [x] `choose` — Choose an item from a list.
- [x] `flip` — Flips a coin... or some text.
- [x] `guess` — Guess a number between 1 and 11
- [x] `settle` — Play: rock paper scissors lizard spock
- [ ] `score` — database to record wins, losses, and draws per command
- - - -
<br>

## .:: Transform ::. ##
🔸 <b>Installation</b>: `{p}plugin add WebKide/modmail-plugins/transform@master`

- [x] `{p}charinfo <🍆>` - Return UNICODE characters for emoji `\U0001f346` or character `\N{AUBERGINE}`
- [x] `{p}clap [message]` - Clap 👏 that 👏 message!
- [x] `{p}pray [message]` - Pray 🙏 that 🙏 message!
- [x] `{p}tiny [text]` - Convert any text into ᵗⁱⁿʸ text
- [x] `{p}wordai` - Generate words (fantasy names) artificially
- [ ] `{p}zalgo [name]` - <i>eye-rape</i> unreadable text
- - - -
<br>

## .:: Presence ::. ##
- [ ] there's already a command that works, but I might add one to loop a list of presence statuses
- - - -
- - - -

# .:: TO-DO ::. #

> `youtube`, `show_color`, `$modbot`, `Base` (`bg`, `sb`, `cc`, `search_group`)
