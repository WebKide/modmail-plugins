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
from datetime import date

dev_list = [323578534763298816]
ball_answers = [
  "It is certain, just relax and it will come/happen",
  "I have determined that, yes!",
  "Not to be a cunt, but no!",
  "Without a shred of doubt",
  "Yes definitely, no need to ask anymore for today",
  "You're so lucky, yet the answer is no.",
  "You may rely on it",
  "If it exists, there is porn of it — no exceptions",
  "As I see it... yes, don't worry about it anymore",
  "I cannot find a satisfactory answer on the internet either",
  "Most likely, but you have to take the first step",
  "Outlook is good, do your best!",
  "Yes",
  "I͢fͪ yͧo̞u̎ c̮ͭa̴ͫn̛̗̅'t̼̹̀ rͣ̒e̤̿a̜ͣd͕͗ ṯ̭͗h́̉͝i̵̥͠ș̽ͤ m̺̤ͧę̏̌s̫͓̕s̟̐̀â͟ͅg̡̖͛ḛ̼̉, p͙̞̽l̪̤͞e͏͙͊ă̳̟s̳͋ͬé̎̑... \ns̞͑̂e͖͋́e̓̑̾ a̳̎̊ D͙̹ͅo̬ͦ̍c̔͊͟t̼̹̀o͏̄̑r̵̝ͦ a̰̳̔n̛̗̅d̮̔͘ a̒́͠s̃́̓k͓͍̿ f̰͐ͭo̳̚͢rͭ̏͏ b̿̐̍e͍̪͋ṭ̑̏t̶̗̙e̝ͮ͊ṙͧ͠ g̐͆͠ḷ͗͝aͫ̌̉s̖̩̽s̲̏̌e̴̓͗s̞̃̎",
  "Signs point to yes, but with some difficulty",
  "I'm busy right now, can you come by later? \nThank you",
  "Hazy reply, try again after a cold shower",
  "You should know that I'm vegan, so I can't really tell the difference",
  "Ask again later, for now try to relax and think about something else",
  "Follow this tip: if they can't see you, they won't know about it",
  "There are a lot of possibilities, just do it, wisely",
  "Better not tell you now, you'll understand later",
  "Cannot predict now, ask anything else",
  "Concentrate, breathe, close your eyes and, ask again",
  "Learn to google, then, google-it!",
  "Seek joy first and foremost!",
  "Thou shall not pass",
  "Don't count on it, better do something else",
  "All things must pass",
  "My reply is no, have a nice day",
  "My imaginary friends said no, brb",
  "As hard as it might be to accept, the answer is,\nmaybe",
  "There might be problems, be ready",
  "Very doubtful, better don't get attached",
  "That's a lot of work and responsibility,\nwe'll miss you",
  "Never, just give up and be happy as you are",
  "Tip of the day: you need more sunlight",
  "Forget about it, turn on airplane mode and relax offline for a while",
  "Go and ask your mum",
  "乁( ⁰͡ Ĺ̯ ⁰͡ ) ㄏ who knows, who cares",
  "Please do not smoke marijuana, even if it's legal"
]
card_deck = [
  ":small_red_triangle: » Upright card meaning\n**0 The Fool:** ```css\nAct impulsively, follow your feelings, surprise, wonder, excitement, take opportunities that arise.```",
  ":small_red_triangle_down: » Downright card meaning\n**0 The Fool:** ```css\nDifficulty believing in your instincts, fear of stepping into the unknown, do not be reckless.```",
  ":small_red_triangle: » Upright card meaning\n**1 The Magician:** ```css\nPower, Strength, Being in control of one's life. Transforming old situations, bringing in new ones. A burst of energy, Creativity, Focused Will.```",
  ":small_red_triangle_down: » Downright card meaning\n**1 The Magician:** ```css\nNatural expression of energy blocked. Inner resistance. Arrogance. Misuse of personal power.```",
  ":small_red_triangle: » Upright card meaning\n**2 The High Priestess:** ```css\nA time for quiet, for looking inward. Seek peace. Use intuition and feeling. Peace and joy. Possibly, a lover who needs solitude or is avoiding commitment.```",
  ":small_red_triangle_down: » Downright card meaning\n**2 The High Priestess:** ```css\nA time for action, for involvements with others. Commitment in romance.```",
  ":small_red_triangle: » Upright card meaning\n**3 The Empress:** ```css\nPassion, Love of nature, Motherhood. Joyous Activity.```",
  ":small_red_triangle_down: » Downright card meaning\n**3 The Empress:** ```css\nPassion blocked. Difficulty expressing oneself. Problems with one's mother.```",
  ":small_red_triangle: » Upright card meaning\n**4 The Emperor:** ```css\nInfluence of Society, law. Resurgence of energy. Sexual potency. Arrogance. Insensitivity. Energy and Desire.```",
  ":small_red_triangle_down: » Downright card meaning\n**4 The Emperor:** ```css\nBlocked possibility. Development of sensitivity.```",
  ":small_red_triangle: » Upright card meaning\n**5 The Hierophant:** ```css\nTradition, community and teachings. Conformity. Marriage, or any solemn commitment.```",
  ":small_red_triangle_down: » Downright card meaning\n**5 The Hierophant:** ```css\nSocial pressure. Doctrines and ideas that have lost meaning. Originality. Gullibility.```",
  ":small_red_triangle: » Upright card meaning\n**6 The Lovers:** ```css\nThe importance of love. Depending on the place in the spread, the state of a specific relationship.```",
  ":small_red_triangle_down: » Downright card meaning\n**6 The Lovers:** ```css\na relationship ending, trouble in a relationship. Lack of love. Insecurity, loneliness. Loss of Balance.```",
  ":small_red_triangle: » Upright card meaning\n**7 The Chariot:** ```css\nWillpower in dealing with problems. Will to continue. Deep fear driving a person. Triumph over fear.```",
  ":small_red_triangle_down: » Downright card meaning\n**7 The Chariot:** ```css\nLack of will. Passivity or weakness. It may be best to let things run their course.```",
  ":small_red_triangle: » Upright card meaning\n**8 Strength:** ```css\nInner strength. Love and gentleness. Confidence. Ability to give love.```",
  ":small_red_triangle_down: » Downright card meaning\n**8 Strength:** ```css\nFeeling blocked from one's power. Weak. Overwhelmed. Meditation or some form of relaxation may help restore strength.```",
  ":small_red_triangle: » Upright card meaning\n**9 The Hermit:** ```css\nWithdrawal from outside interests. Self-reliance. Self-creation. Developing one's personality. Gaining wisdom. Powerful dreams.```",
  ":small_red_triangle_down: » Downright card meaning\n**9 The Hermit:** ```css\nInvolvement with others. Fear of loneliness. Disturbing dreams. A desire to not grow up.```",
  ":small_red_triangle: » Upright card meaning\n**10 The Wheel of Fortune:** ```css\nChange of circumstances. Taking hold of one's life. Grabbing hold of fate. Time to take what life has given you.```",
  ":small_red_triangle_down: » Downright card meaning\n**10 The Wheel of Fortune:** ```css\nDifficulty adjusting to changes. Resistance to change.```",
  ":small_red_triangle: » Upright card meaning\n**11 Justice:** ```css\nExamine your life, weigh things in the balance. A relationship is going badly. Analysis. Take a balanced view.```",
  ":small_red_triangle_down: » Downright card meaning\n**11 Justice:** ```css\nDo not act out of habit. Imbalance. You may be acting unfairly. Trying to avoid an honest evaluation.```",
  ":small_red_triangle: » Upright card meaning\n**12 The Hanged Man:** ```css\nAttachment. Deep spiritual awareness. Independence.```",
  ":small_red_triangle_down: » Downright card meaning\n**12 The Hanged Man:** ```css\nBeing overly influenced by outside ideas. Pressure to conform. Demands. Sacrificing something to get past hangups. Lack of purpose.```",
  ":small_red_triangle: » Upright card meaning\n**13 Death:** ```css\nRarely refers to physical death. More about ideas about death. Psychologically, letting go. New opportunities.```",
  ":small_red_triangle_down: » Downright card meaning\n**13 Death:** ```css\nResisting change. Stagnation. Inertia. Pain of giving something up.```",
  ":small_red_triangle: » Upright card meaning\n**14 Alchemy:** ```css\nMeasurement and combination. Do not allow setbacks to turn enthusiasm into its mirror image of dejection. Take control. Moderation.```",
  ":small_red_triangle_down: » Downright card meaning\n**14 Alchemy:** ```css\nGoing to extremes. Excessive behavior. Conserve energy. A person out of control.```",
  ":small_red_triangle: » Upright card meaning\n**15 The Devil:** ```css\nSomething exciting, possibly dangerous or forbidden. Temptation. Physical gratification. Exploring darker feelings. Wild action opens up new areas in life.```",
  ":small_red_triangle_down: » Downright card meaning\n**15 The Devil:** ```css\nResisting temptations. Not a time for sensuality. Fear of one's own decisions.```",
  ":small_red_triangle: » Upright card meaning\n**16 The Tower:** ```css\nLong-standing activity or approach that may bring about disaster if continued. Pressure building up. Long-buried emotions let loose. News. A flash of understanding.```",
  ":small_red_triangle_down: » Downright card meaning\n**16 The Tower:** ```css\nSimilar to upright meanings, but less severe. A shaking up. A minor disturbance.```",
  ":small_red_triangle: » Upright card meaning\n**17 The Star:** ```css\nRenewal. Reality and feeling. Cleansing. Humility. Hope.```",
  ":small_red_triangle_down: » Downright card meaning\n**17 The Star:** ```css\nFears for the future. Isolation. Tension or anxiety. Hope.```",
  ":small_red_triangle: » Upright card meaning\n**18 The Moon:** ```css\nImagination. Fantasies, daydreams, strong dreams. The sources of creativity.```",
  ":small_red_triangle_down: » Downright card meaning\n**18 The Moon:** ```css\nThe time to return to \"solar\", rational activities. Conscious mind blocking the unconscious.```",
  ":small_red_triangle: » Upright card meaning\n**19 The Sun:** ```css\nJoy and simplicity. Life is wonderful. Energy. Activity, excitement, optimism. Rational approach. Confidence. Sexual Desire.```",
  ":small_red_triangle_down: » Downright card meaning\n**19 The Sun:** ```css\nSun is clouded over. Day-to-day problems, though happiness remains. Loss of confidence. Frustration.```",
  ":small_red_triangle: » Upright card meaning\n**20 Aeon:** ```css\nRenewal. Optimism, in spite of a painful period of change. Change. Spontaneity. All things are possible. Old world seen through new eyes.```",
  ":small_red_triangle_down: » Downright card meaning\n**20 Aeon:** ```css\nRebirth. Resisting change. A new life, possibly not acknowledged.```",
  ":small_red_triangle: » Upright card meaning\n**21 The Universe:** ```css\nSuccess. Becoming happier, more fulfilled. Recovery from illness. An exciting future. Stagnation. Lack of willpower and confidence.```",
  ":small_red_triangle_down: » Downright card meaning\n**21 The Universe:** ```css\nStagnation. Lack of willpower and confidence. Self-defined limitations. Resistance or opposition.```",
  ":small_red_triangle: » Upright card meaning\n**Ace of Wands:** ```css\nGift of fire. Energy, optimism, confidence. Desire. Beginnings.```",
  ":small_red_triangle_down: » Downright card meaning\n**Ace of Wands:** ```css\nLack of focus. Scattered or confused efforts. Pessimism.```",
  ":small_red_triangle: » Upright card meaning\n**Two of Wands:** ```css\nPower, Strong Will. The power of spiritual truth.```",
  ":small_red_triangle_down: » Downright card meaning\n**Two of Wands:** ```css\nVoluntarily giving up a position of power. Seeking adventures. Misuse of power.```",
  ":small_red_triangle: » Upright card meaning\n**Three of Wands:** ```css\nActing in harmony with nature. Purpose. Good fortune.```",
  ":small_red_triangle_down: » Downright card meaning\n**Three of Wands:** ```css\nBeing out of harmony with the situation. Difficulty in finding the point of life or in discovering worthy goals.```",
  ":small_red_triangle: » Upright card meaning\n**Four of Wands:** ```css\nNew life. Take action at the right moment. Excitement and growth.```",
  ":small_red_triangle_down: » Downright card meaning\n**Four of Wands:** ```css\nErrors. Impatient for new start. Wait for genuine opportunity.```",
  ":small_red_triangle: » Upright card meaning\n**Five of Wands:** ```css\nStrife and battle, without hatred or bitterness. Avoidance.```",
  ":small_red_triangle_down: » Downright card meaning\n**Five of Wands:** ```css\nPersonal and aggressive conflicts. Bitterness towards others.```",
  ":small_red_triangle: » Upright card meaning\n**Six of Wands:** ```css\nTriumph. Confidence and firm action will lead to triumph. Inspiration.```",
  ":small_red_triangle_down: » Downright card meaning\n**Six of Wands:** ```css\nLoss of belief. Negative attitude can lead to failure.```",
  ":small_red_triangle: » Upright card meaning\n**Seven of Wands:** ```css\nCourage and daring - possibly, the courage to retreat. Using one's power for transformation.```",
  ":small_red_triangle_down: » Downright card meaning\n**Seven of Wands:** ```css\nLoss of nerve. Hesitation. Seek an alternative, possibly reconciliation.```",
  ":small_red_triangle: » Upright card meaning\n**Eight of Wands:** ```css\nDefinite movement. Progress. A worthy goal. Finding direction in life. Development of a new love affair.```",
  ":small_red_triangle_down: » Downright card meaning\n**Eight of Wands:** ```css\nScattered energy. Contradictory activities. Fear of taking action. Shyness, or jealousy.```",
  ":small_red_triangle: » Upright card meaning\n**Nine of Wands:** ```css\nGreat energy. Arrogance, especially toward those who feel weak. Life's resiliency.```",
  ":small_red_triangle_down: » Downright card meaning\n**Nine of Wands:** ```css\nWeakness. Passivity. Arrogance or misuse of power.```",
  ":small_red_triangle: » Upright card meaning\n**Ten of Wands:** ```css\nOppression. Depression. Transformation from cruelty to liberation. Possible fall.```",
  ":small_red_triangle_down: » Downright card meaning\n**Ten of Wands:** ```css\nEmerging from a bad situation. Wisdom gained through adversity.```",
  ":small_red_triangle: » Upright card meaning\n**Mother of Wands in the East (Kali):** ```css\nA wild, female energy. Dark power, sexual energy.```",
  ":small_red_triangle_down: » Downright card meaning\n**Mother of Wands in the East (Kali):** ```css\nKali-like energy suppressed. Destructiveness outweighs love and joy.```",
  ":small_red_triangle: » Upright card meaning\n**Father of Wands in the East (Brahma):** ```css\nA calm person, possibly stuffy. A rooted quality that gives strength.```",
  ":small_red_triangle_down: » Downright card meaning\n**Father of Wands in the East (Brahma):** ```css\nSnobbishness, especially intellectual. Devotion. Doubts, weakness, confusion.```",
  ":small_red_triangle: » Upright card meaning\n**Daughter of Wands in the East (Radha):** ```css\nAbundance. Joy. Good Sense. Culture.```",
  ":small_red_triangle_down: » Downright card meaning\n**Daughter of Wands in the East (Radha):** ```css\nUnfulfilled potential.```",
  ":small_red_triangle: » Upright card meaning\n**Son of Wands in the East (Krishna):** ```css\nLove of life. Interest in the arts. Trickster. Attractiveness.```",
  ":small_red_triangle_down: » Downright card meaning\n**Son of Wands in the East (Krishna):** ```css\nDifficulty. Conflict. Problems may bring out depths in a person.```",
  ":small_red_triangle: » Upright card meaning\n**Ace of Cups:** ```css\nHappiness. Love, joy, optimism. Love flowing openly between two people.```",
  ":small_red_triangle_down: » Downright card meaning\n**Ace of Cups:** ```css\nHappiness is blocked. Trouble communicating. Value of life questioned.```",
  ":small_red_triangle: » Upright card meaning\n**Two of Cups:** ```css\nRelationship. Possibly, the need to make a commitment.```",
  ":small_red_triangle_down: » Downright card meaning\n**Two of Cups:** ```css\nQuarreling or jealousy. Uncertain future. Lack of commitment.```",
  ":small_red_triangle: » Upright card meaning\n**Three of Cups:** ```css\nGreat feeling. Extreme joy that can turn to tears.```",
  ":small_red_triangle_down: » Downright card meaning\n**Three of Cups:** ```css\nFeelings dammed up. Instability.```",
  ":small_red_triangle: » Upright card meaning\n**Four of Cups:** ```css\nFind a moment of peace and balance. Action is possible and will lead to growth.```",
  ":small_red_triangle_down: » Downright card meaning\n**Four of Cups:** ```css\nLoss of balance. Suppressed emotions.```",
  ":small_red_triangle: » Upright card meaning\n**Five of Cups:** ```css\nBe patient. Confusion and disappointment are exaggerated.```",
  ":small_red_triangle_down: » Downright card meaning\n**Five of Cups:** ```css\nComing out of disappointment. A realistic view of the past.```",
  ":small_red_triangle: » Upright card meaning\n**Six of Cups:** ```css\nHappiness. Loving and being loved. Balance and peace.```",
  ":small_red_triangle_down: » Downright card meaning\n**Six of Cups:** ```css\nThe happy moment may be passing. Not recognizing happiness. Unbalanced or excessive behavior.```",
  ":small_red_triangle: » Upright card meaning\n**Seven of Cups:** ```css\nBeware of arrogance and complacency. Fantasies.```",
  ":small_red_triangle_down: » Downright card meaning\n**Seven of Cups:** ```css\nHidden problems emerging. More realistic outlook.```",
  ":small_red_triangle: » Upright card meaning\n**Eight of Cups:** ```css\nFailure. Arrogance and greed. Accept help from others.```",
  ":small_red_triangle_down: » Downright card meaning\n**Eight of Cups:** ```css\nHidden joy. New happiness. Positive change.```",
  ":small_red_triangle: » Upright card meaning\n**Nine of Cups:** ```css\nFortune. Wealth. Emotional breakthrough. Generosity.```",
  ":small_red_triangle_down: » Downright card meaning\n**Nine of Cups:** ```css\nStinginess. Loss.```",
  ":small_red_triangle: » Upright card meaning\n**Ten of Cups:** ```css\nSuccessful development, with some effort required.```",
  ":small_red_triangle_down: » Downright card meaning\n**Ten of Cups:** ```css\nSuccess Blocked. Negativity, apathy.```",
  ":small_red_triangle: » Upright card meaning\n**Mother of Cups in the North (Venus of Willendorf):** ```css\nEarthy, Plain, Honest person. Matriarch. Ancient Forces.```",
  ":small_red_triangle_down: » Downright card meaning\n**Mother of Cups in the North (Venus of Willendorf):** ```css\nSomeone out of touch with physical realities.```",
  ":small_red_triangle: » Upright card meaning\n**Father of Cups in the North (Odin):** ```css\nA powerful, domineering person. Intelligence. Creativity. Generous and Loving.```",
  ":small_red_triangle_down: » Downright card meaning\n**Father of Cups in the North (Odin):** ```css\nFather's power disrupted.```",
  ":small_red_triangle: » Upright card meaning\n**Daughter of Cups in the North (Brigid):** ```css\nCalmness and radiance. Peacefulness, and strength of power.```",
  ":small_red_triangle_down: » Downright card meaning\n**Daughter of Cups in the North (Brigid):** ```css\nLoss of self-assurance. Importance of personal history ignored.```",
  ":small_red_triangle: » Upright card meaning\n**Son of Cups in the North (Parsival):** ```css\nSweet-tempered, but naive person. A good heart. A test.```",
  ":small_red_triangle_down: » Downright card meaning\n**Son of Cups in the North (Parsival):** ```css\nAvoiding responsibility. Callousness.```",
  ":small_red_triangle: » Upright card meaning\n**Ace of Swords:** ```css\nIntelligence. Clear thinking. Powerful personality or emotions.```",
  ":small_red_triangle_down: » Downright card meaning\n**Ace of Swords:** ```css\nAnger. Aggression. Distorted thinking.```",
  ":small_red_triangle: » Upright card meaning\n**Two of Swords:** ```css\nTranquility. Opportunity for prospering.```",
  ":small_red_triangle_down: » Downright card meaning\n**Two of Swords:** ```css\nDisruption. Seek tranquility within.```",
  ":small_red_triangle: » Upright card meaning\n**Three of Swords:** ```css\nOppressive situations. Mourning. Sorrow.```",
  ":small_red_triangle_down: » Downright card meaning\n**Three of Swords:** ```css\nDifficulty accepting loss. The natural cycle will bring renewal.```",
  ":small_red_triangle: » Upright card meaning\n**Four of Swords:** ```css\nA moment of calm.```",
  ":small_red_triangle_down: » Downright card meaning\n**Four of Swords:** ```css\nMovement away from silence and peace. New beginnings or old troubles.```",
  ":small_red_triangle: » Upright card meaning\n**Five of Swords:** ```css\nAn overwhelming situation. Need to hold onto principles until the time comes to make a change.```",
  ":small_red_triangle_down: » Downright card meaning\n**Five of Swords:** ```css\nSituation growing better, with courage and persistence.```",
  ":small_red_triangle: » Upright card meaning\n**Six of Swords:** ```css\nNeed for objectivity and honesty.```",
  ":small_red_triangle_down: » Downright card meaning\n**Six of Swords:** ```css\nIdealism used for selfish ends.```",
  ":small_red_triangle: » Upright card meaning\n**Seven of Swords:** ```css\nDepression. Possibly, the need to leave a situation for new possibilities.```",
  ":small_red_triangle_down: » Downright card meaning\n**Seven of Swords:** ```css\nAttempting to deal with feelings of uselessness.```",
  ":small_red_triangle: » Upright card meaning\n**Eight of Swords:** ```css\nInterference. Gossip. Help or Advice.```",
  ":small_red_triangle_down: » Downright card meaning\n**Eight of Swords:** ```css\nNo interference. Avoiding responsibility.```",
  ":small_red_triangle: » Upright card meaning\n**Nine of Swords:** ```css\nCruelty. Feeling like a victim.```",
  ":small_red_triangle_down: » Downright card meaning\n**Nine of Swords:** ```css\nRelief from cruel conditions. Confusion. Manipulation.```",
  ":small_red_triangle: » Upright card meaning\n**Ten of Swords:** ```css\nPain, confusion. Personal difficulties. Problems.```",
  ":small_red_triangle_down: » Downright card meaning\n**Ten of Swords:** ```css\nTroubles passing. Relief. Need to rest.```",
  ":small_red_triangle: » Upright card meaning\n**Mother of Swords in the South (Nut):** ```css\nA mysterious person. Devotion. Autonomy.```",
  ":small_red_triangle_down: » Downright card meaning\n**Mother of Swords in the South (Nut):** ```css\nNeed for privacy exaggerated. Conflict between love of solitude and love for others.```",
  ":small_red_triangle: » Upright card meaning\n**Father of Swords in the South (Ra):** ```css\nDominant, autocratic person. Delegating authority to others. Strong, creative intellect. Fairness.```",
  ":small_red_triangle_down: » Downright card meaning\n**Father of Swords in the South (Ra):** ```css\nTyrant. A person jealous of personal powerful.```",
  ":small_red_triangle: » Upright card meaning\n**Daughter of Swords in the South (Isis):** ```css\nA powerful figure, confident and dynamic.```",
  ":small_red_triangle_down: » Downright card meaning\n**Daughter of Swords in the South (Isis):** ```css\nLoss of confidence. Depression.```",
  ":small_red_triangle: » Upright card meaning\n**Son of Swords in the South (Osiris):** ```css\nSomeone gentle yet persuasive. An initiate into esoteric mysteries. Kindness.```",
  ":small_red_triangle_down: » Downright card meaning\n**Son of Swords in the South (Osiris):** ```css\nWeakness, possibly corruption.```",
  ":small_red_triangle: » Upright card meaning\n**Ace of Stones:** ```css\nHealth. Prosperity. Beauty. Good weather.```",
  ":small_red_triangle_down: » Downright card meaning\n**Ace of Stones:** ```css\nUnappreciated gifts. Materialism. Conflicts over money or property.```",
  ":small_red_triangle: » Upright card meaning\n**Two of Stones:** ```css\nHarmonic situations.```",
  ":small_red_triangle_down: » Downright card meaning\n**Two of Stones:** ```css\nDisharmony. A time for solitude.```",
  ":small_red_triangle: » Upright card meaning\n**Three of Stones:** ```css\nWork. Satisfaction.```",
  ":small_red_triangle_down: » Downright card meaning\n**Three of Stones:** ```css\nWork not going well. Unemployment. Laziness.```",
  ":small_red_triangle: » Upright card meaning\n**Four of Stones:** ```css\nCreativity and new ideas. Overwhelming energy.```",
  ":small_red_triangle_down: » Downright card meaning\n**Four of Stones:** ```css\nLosing a sense of place. Fear.```",
  ":small_red_triangle: » Upright card meaning\n**Five of Stones:** ```css\nWintry time. Money troubles. Illness. Isolation.```",
  ":small_red_triangle_down: » Downright card meaning\n**Five of Stones:** ```css\nMovement for the better. Wait, act cautiously.```",
  ":small_red_triangle: » Upright card meaning\n**Six of Stones:** ```css\nGreat success and joy, possibly short-lived. Find inner truth and happiness.```",
  ":small_red_triangle_down: » Downright card meaning\n**Six of Stones:** ```css\nMoment beginning to end. Save or invest money carefully during prosperity.```",
  ":small_red_triangle: » Upright card meaning\n**Seven of Stones:** ```css\nDisharmony. Without careful redirection, failure is possible.```",
  ":small_red_triangle_down: » Downright card meaning\n**Seven of Stones:** ```css\nRecovery. Fresh Start.```",
  ":small_red_triangle: » Upright card meaning\n**Eight of Stones:** ```css\nBe careful and moderate. Avoid excessive action.```",
  ":small_red_triangle_down: » Downright card meaning\n**Eight of Stones:** ```css\nLack of moderation. Impatience. Ignorance.```",
  ":small_red_triangle: » Upright card meaning\n**Nine of Stones:** ```css\nFortune. Money, security, health, comfort. Avoid complacency, greed or conceit.```",
  ":small_red_triangle_down: » Downright card meaning\n**Nine of Stones:** ```css\nMisusing material gain. Greed.```",
  ":small_red_triangle: » Upright card meaning\n**Ten of Stones:** ```css\nGood life. Health. A sense of solid reality.```",
  ":small_red_triangle_down: » Downright card meaning\n**Ten of Stones:** ```css\nDelay. Not appreciating material wealth and security.```",
  ":small_red_triangle: » Upright card meaning\n**Mother of Stones in the West (Spider Woman):** ```css\nSerene, probably older woman. Self-confidence.```",
  ":small_red_triangle_down: » Downright card meaning\n**Mother of Stones in the West (Spider Woman):** ```css\nDifficulty in staying still and appreciating life. Loss of personal center.```",
  ":small_red_triangle: » Upright card meaning\n**Father of Stones in the West (Old Man):** ```css\nFundamental male principle. Someone who cares deeply for family and for nature. Hard Worker.```",
  ":small_red_triangle_down: » Downright card meaning\n**Father of Stones in the West (Old Man):** ```css\nCold and uncaring. Lack of success. Pain at the suffering of the world.```",
  ":small_red_triangle: » Upright card meaning\n**Daughter of Stones in the West (White Buffalo Woman):** ```css\nWillingness to take responsibility for something greater than oneself. Love, courage, and dedication. Inner beauty.```",
  ":small_red_triangle_down: » Downright card meaning\n**Daughter of Stones in the West (White Buffalo Woman):** ```css\nDifficulty getting across ideas or emotions. Feeling out of place.```",
  ":small_red_triangle: » Upright card meaning\n**Son of Stones in the West (Chief Seattle):** ```css\nTaking action to make positive change - with the benefit of the next seven generations in mind.```",
  ":small_red_triangle_down: » Downright card meaning\n**Son of Stones in the West (Chief Seattle):** ```css\nDespair. Selfishness leads to feeling lost.```"
]
oracle_answer = [
  "「1 乾」 **Chien** : `the vital spirit of heaven` ䷀\n*Force*, *the creative*, *strong action*, *the key*, and *god*.\n```bf\nGood fortune is coming your way in anything you do\n\nYour courage and perseverance will reward you with great success If you know how to take your actions and ideals forward with a sense of justice, the forces of Heaven will support you and you will receive the success you desire. Always keep your spirit in harmony with nature```",
  "「2 坤」 **K'un** : `a multiplicity of things` ䷁\n*Field*, *the receptive*, *acquiescence*, and *the flow*.\n```bf\nTroubles and problems are solved with little difficulty\n\nTo not lose the way, you must be patient not to force events. You will obtain great benefits and advantages if you learn how to adapt to various situations, using everyone and without taking initiative. This behaviour will lead you to fulfilling your aims```",
  "「3 屯」 **Chun** : `difficulty getting started` ䷂\n*Sprouting*, *difficulty at the beginning*, *gathering support*, and *hoarding*.\n```bf\nThere is a great danger in gossip getting out of hand\n\nIf you wish to undertake something new, you must consider difficulties which will certainly arise, especially at the beginning. Patience and faith in your goals will help you but will not be enough: you must choose someone who can help you and accept the advice of others with benevolence```",
  "「4 蒙」 **Meng** : `getting caught` ䷃\n*Enveloping*, *youthful folly*, *the young shoot*, and *discovering*.\n```bf\nYouthful foolishness. Wasting money. Your life is filled with idle gossip\n\nYou want to reach a goal but in order to do so you will have to trust a Master or guide who will help you overcome obstacles. Initially, you will have the innocence of a child but then, thanks to experience, you will finally reach self-awareness```",
  "「5 需」 **Hsu** : `waiting` ䷄\n*Attending*, *waiting*, *moistened*, and *arriving*.\n```bf\nHappiness is coming. Committed projects are successful\n\nYou must learn how to wait without accelerating time. It is not the right moment to act. You must wait patiently for events to occur until the exact moment for acting arives. Your wait will be useful to relax and collect your strength```",
  "「6 訟」 **Sung** : `conflict` ䷅\n*Arguing*, *conflict* and *lawsuit*.\n```bf\nThere are obstacles that block everything you do\n\nEven if you know you are right, stubbornness will cause you harm and conflict. You will have to look for equilibrium and the possibly for meditation to avoid disagreements from occurring. It will be vital for you to recognise the moment to stop, even if it is half way through the journey/project```",
  "「7 師」 **Shih** : `the mass of humanity` ䷆\n*Leading*, *the army* and *the troops*.\n```bf\nPlans find a favourable response\n\nSearch for self-discipline to realise your aims. You must organise and manage all your inner strength to be able to confidently move toward your goals. To keep to schedule, you will have to persist and always be constant```",
  "「8 比」 **Pi** : `a banding together` ䷇\n*Grouping*, *holding together* and *alliance*.\n```bf\nIt is important that you unite with others and feel part of a group; this will bring you luck. Approaching friends and people whom you trust helps in moments of need and always gives you great strength. So do not hesitate to put yourself forward in a disinterested way toward others```",
  "「9 小畜」 **Hsiao Ch'u** : `small involvement` ䷈\n*Small Accumulating*, *the taming power of the small* and *small harvest*.\n```bf\nNot a good time to expand. Good time to relax\n\nAt the moment you must wait and occupy yourself only with small things. You will be able to be victorious but you must not display this too much: use this period to analyse everything and be prepared to the best of your ability. Thus, you will gain strength and succeed in your endeavor```",
  "「10 履」 **Lu** : `smug self-confidence` ䷉\n*Treading*, *treading (conduct)* and *continuing*.\n```bf\nYou must find the best way to behave toward others. If you learn how to behave correctly, you will manage to conquer those people you want to, whatever their position. Through kindness, you will also gain a great deal from difficult and unpleasant people```",
  "「11 泰」 **Tai** : `rising above adversity` ䷊\n*Pervading*, *peace* and *greatness*.\n```bf\nRelationships enjoy a period of great harmony\n\nThis is a good moment for harmony in which peace, concordance and success govern. If you wish to prosper and be lucky, you will have to maintain this state. Ask help from someone who is capable of stabilising this favourable situation```",
  "「12 否」 **P'i** : `stagnation` ䷋\n*Obstruction*, *standstill (stagnation)* and *selfish persons*.\n```bf\nIt is not worth acting in this particular moment as the general situation is not entirely favourable. You will gain more profits by pulling back temporarily and maintaining your independence. Your wisdom now consists in waiting and avoiding the company of unpleasant people```",
  "「13 同人」 **T'ung Jen** : `people who have affinity with each other` ䷌\n*Concording People*, *fellowship with men* and *gathering men*.\n```bf\nTo achieve your aims, you will have to unite with virtuous people. Indeed it will be easier to reach every objective if a group of individuals (albeit of different characters), have the same common goal. However, always keep your own personality and act so that you benefit one another```",
  "「14 大有」 **Ta Yu** : `having great possessions` ䷍\n*Great Possessing*, *possession in great measure* and *the great possession*.\n```bf\nWhat you have lost will return to you\n\nTo win, you must use neither aggression nor arrogance. Indeed, you can obtain great things by being calm. Your attitude of apparent weakness is your strength and nobody can oppose you. Great success is certain to arrive```",
  "「15 謙」 **Ch'ien** : `holding one's tongue` ䷎\n*Humbling*, *modesty*.\n```bf\nDo not forget that in life, nothing remains unchanged and everything evolves through transformation. You must learn how to evaluate every situation with the correct amount of modesty. If you are living a moment of success, re-dimension your enthusiasm; If, on the other hand, you are waiting for some development, be patient; everything turns and re-news itself```",
  "「16 豫」 **Yu** : `eagerness to start` ䷏\n*Providing-For*, *enthusiasm* and *excess*.\n```bf\nIf you must lead a group, you must also understand others' intentions and moods. You will be able to fulfil your aims by eliminating every kind of resistance provided that you can understand and go along with everyone. Your enthusiasm will do the rest```",
  "「17 隨」 **Sui** : `obedient participation` ䷐\n*Following*.\n```bf\nThis is a time that favours you\n\nIn this particular moment, try not to waste energy in fighting but wait without forcing Destiny's hand. If you learn how to adapt yourself to the situation at hand, by coming to an agreement you will obtain great well-being and assured success```",
  "「18 蠱」 **Ku** : `inner turmoil` ䷑\n*Correcting*, *work on what has been spoiled*, *decaying* and *branch*.\n```bf\nThis is the right moment to modify some of your habits. Stagnant situations can only get worse. Eliminate laziness, intervene decisively and resolve any problem within the next few days```",
  "「19 臨」 **Lin** : `different classes of people` ䷒\n*Nearing*, *approach* and *the forest*.\n```bf\nIf you want others to approach you, first you must approach them. A positive moment, do not fear anything. Make the most of this as collaboration is very good at this particular time```",
  "「20 觀」 **Kuan** : `looking, seeing, confronting` ䷓\n*Viewing*, *contemplation (view)* and *looking up*.\n```bf\nTo take the best decisions, in this phase you must concede all the time necessary to reflect calmly. Evaluate every single aspect of the situation. Observe and understand everything before action```",
  "「21 噬嗑」 **Shih Ho** : `wrathful` ䷔\n*Gnawing Bite*, *biting through* and *biting and chewing*.\n```bf\nThe agony of loneliness finds respite\n\nIn this phase, the right way to face the situation is to intervene with decisiveness. It isn't the right time to ignore a problem, or stick your head in the sand. You must re-establish justice, use every means at your disposal: perseverance will help```",
  "「22 賁」 **Pi** : `grace and beauty` ䷕\n*Adorning*, *grace* and *luxuriance*.\n```bf\nConsider beauty and look for it both within yourself and in others. Even though beauty is simply an ornament, its contemplation can bring joy, albeit ephemeral. Highlight your own beauty and admire that of others. That which you focus on, expands```",
  "「23 剝」 **Po** : `finality of death` ䷖\n*Stripping*, *splitting apart* and *flaying*.\n```bf\nThis is the moment of expectation for you as sometimes danger can be hidden yet it's present, even if you don't see it. Some problems occur inside, in silence. Do not put yourself forward and take no decisions. Postpone everything and retreate into your safe zone```",
  "「24 復」 **Fu** : `turning back` ䷗\n*Returning*, *return (the turning point)*.\n```bf\nEven a friend can become an enemy. You need patience for this time of confusion\n\nAfter a period of darkness, the light always returns; now you can face a new phase of renewal. This is the right moment as you will be able to regenerate yourself. There will be no resistance on your path toward success```",
  "「25 無妄」 **Wu Wang** : `innocence` ䷘\n*Without Embroiling*, *innocence (the unexpected)* and *pestilence*.\n```bf\nYour lover is betraying you, be careful\n\nListen to what your internal voice suggests and go forward doing things you know are right. Do not act for a particular aim, or hoping for a financial reward. Be simple and listen to your profound inner-Being. Act freely and with serenity```",
  "「26 大畜」 **Ta Ch'u** : `big involvement` ䷙\n*Great Accumulating*, *the taming power of the great*, *great storage*, and *potential energy.*```bf\nClarity emerges where there was confusion\n\nGreat force of spirit and great physical power are hidden inside you. Even if you don't always notice it, this potential is present and you must simply learn to cultivate and discipline it. This is the right moment for using what's inside you```",
  "「27 頤」 **I** : `nourishment` ䷚\n*Swallowing*, *the corners of the mouth (providing nourishment)*, *jaws* and *comfort/security*.\n```bf\nThere's an excellent person helping you, a mentor.\n\nNourishment of your body and soul are equally important and correlated to one another. Be careful therefore to look after what you eat and pay great attention to your diet. You are what you eat. You'll understand what are your limits and will find equilibrium```",
  "「28 大過」 **Ta Kuo** : `great excess` ䷛\n*Great Exceeding*, *preponderance of the great*, *great surpassing* and *critical mass.*```bf\nAt the moment, events are overpowering and superior to your strength; you cannot win and it is useless to oppose them. You must try to eliminate this obstacle, avoid danger by pulling yourself away from the situation. Be firm and decisive. Learn to say no```",
  "「29 坎」 **Kan** : `the Abysmal` ䷜\n*Gorge*, *the abyss* (in the oceanographic sense) and *repeated entrapment*.\n```bf\nThe image of the Abysmal is like seeing a mirage\n\nYou feel you are in the midst of danger and negative circumstances. You must be true to your principles and profound ideals. If you resist with courage and perseverance, being always faithful to your sense of justice, you'll soon be free from this period of adversity```",
  "「30 離」 **Li** : `clinging` ䷝\n*Radiance*, *the clinging, fire* and *the net*.\n```bf\nEven if you have reached success, you must never forget who is present and near you. Those who act in your shadow contribute to sustain your position. There is always reciprocity and relations between people, whatever your level of evolution may be. Do not walk alone```",
  "「31 咸」 **Hsien** : `something felt in the heart` ䷞\n*Conjoining*, *influence (wooing)* and *feelings*.\n```bf\nThis is a favourable moment for you if you wish to start up or improve an emotional relationship. Indeed, now there is great harmony in the cosmos. The situation is favourable for change; this could make your heart and the one of whoever is near you richer```",
  "「32 恆」 **Heng** : `constancy` ䷟\n*Persevering*, *duration* and *constancy*.\n```bf\nDo not interrupt or modify the way you are going. Everything evolves and events run continuously toward their destination. This movement is positive, live it with self-awareness and you'll face all great and small difficulties with ease```",
  "「33 遯」 **Tun** : `running away` ䷠\n*Retiring*, *retreat* and *yielding*.\n```bf\nIt's the right moment to step back and observe the situation from outside, in a quiet corner. Renouncing action doesn't mean defeat; instead, it's a sign of great wisdom. Collect your strengths, you will evaluate the current events and intervene at the right moment with great success```",
  "「34 大壯」 **Ta Chuang** : `great wisdom` ䷡\n*Great Invigorating*, *the power of the great* and *great maturity*.\n```bf\nMeetings with friends go smoothly\n\nNow you have the opportunity to obtain your desires and reach your aims. Nothing is impossible as inside you there's great strength and you are fully aware of this. But beware: avoid over-confidence or arrogance and be sure you are always in the right```",
  "「35 晉」 **Chin** : `meting the great Man` ䷢\n*Prospering*, *progress* and *aquas*.\n```bf\nFor you, this is a winning moment which you must know how to make the most of. Nothing lasts forever. Remember you will obtain the best results by joining with people who share your interests and aspirations. You will all help one another```",
  "「36 明夷」 **Ming I** : `a darkening` ䷣\n*Darkening of the Light*, *brilliance injured* and *intelligence hidden*.\n```bf\nIt is not an easy moment and even if you feel to be in the darkness, light is there, albeit hidden. For now, do not confide your thoughts in those around you. Keep your integrity in silence```",
  "「37 家人」 **Chia Jen** : `the family type` ䷤\n*Dwelling People*, *the family (the clan)* and *family members*.\n```bf\nTry to understand what your role and position are within the family or social group. In fact, you will get the best results by being faithful to your current role, contributing to the well-being of others```",
  "「38 睽」 **Kuei** : `opposition` ䷥\n*Polarising*, *opposition* and *perversion*.\n```bf\nIt is not worth trying to harmonise things, people or situations which are simply not compatible. Remember, everyone has different personalities and it's important for you to maintain yours. You can find a harmonious way, even if this is in the distant future```",
  "「39 蹇」 **Chien** : `grave danger` ䷦\n*Limping*, *obstruction* and *afoot*.\n```bf\nThis is not the right moment to act; there are difficulties and it's worth it for you to stop and reflect. When something doesn’t work, do not blame someone else, instead, look for possible causes within you. Remember that you can always lean on someone you have trusted for some time now```",
  "「40 解」 **Hsieh** : `liberation`\n*Taking-Apart*, *deliverance* and *untangled*.\n```bf\nYour social life takes-off, suddenly you are very popular\n\nThis is the moment when adversities will be overcome. You'll realise that all problems are now behind you and that soon the road back to normality will be free. When you finally have victory, try not to show any form of rancour```",
  "「41 損」 **Sun** : `loss` ䷨\n*Diminishing*, *decrease*.\n```bf\nIn this period, you must try to eliminate all which is superficial in favour of what is essential. You must not consider this as a loss, because what you lose on one hand, you gain on another. To be lucky, you must concentrate only on what is really useful```",
  "「42 益」 **I** : `increase` ䷩\n*Augmenting*, *increase*.\n```bf\nMisfortune transforms into good fortune\n\nMake the most of this moment to grow and evolve. Now you can work on spiritual elevation and reach important goals. Remember you will grow more quickly if you help people who need you```",
  "「43 夬」 **Kuai** : `determination` ䷪\n*Displacement*, *resoluteness*, *parting*, and *break-through*.\n```bf\nDetermination gets you everywhere, it reaps you benefits\n\nNow you can finally take that decision which puts an end to a current hostile and unfavourable situation. Remember that it'll be enough for you to make the first step, the rest will come along. Take this opportunity and correct once and for all everything which is not right around you```",
  "「44 姤」 **Kou** : `an encounter` ䷫\n*Coupling*, *coming to meet* and *meeting*.\n```bf\nAn unexpected encounter is likely to take place. Don't go on the first impression. Try to understand what's hidden beneath the external veil. Try to avoid dangers and you'll obtain advantages and long-term success```",
  "「45 萃」 **Ts'ui** : `gathering` ䷬\n*Clustering*, *gathering together (massing)* and *finished*.\n```bf\nNow is a good time to meet others and make projects together. Remember that in a group you must always consider different ideas and expectations. Avoid all pretensions```",
  "「46 升」 **Sheng** : `ascending` ䷭\n*Ascending*, *pushing upward*.\n```bf\nFear nothing, for this is a favourable moment. You can reach high slowly and with constancy. Along the way you'll meet important and influential people. If they deserve your trust, treasure their example and advice```",
  "「47 困」 **K'un** : `oppression` ䷮\n*Confining*, *oppression (exhaustion)* and *entangled*.\n```bf\nDon't give up, even if something is worrying you. Make the most of this circumstance and transform every difficulty into a stimulus so that you can go ahead. Have faith in destiny which always changes bad into good. Luck is for the bravest!```bf\n",
  "「48 井」 **Ching** : `the well` ䷯\n*Welling*, *the well*.\n```bf\nExternal circumstances regularly change quickly. You must consider however that the most intimate essence of man is unchanged over time. Give what you have to grow. Try to help others as well as you can```",
  "「49 革」 **Ko** : `revolution` ䷰\n*Skinning*, *revolution (molting)* and *the bridle*.\n```bf\nThere will be a radical change which will let you make the most of renewing the current state of affairs. Be careful to consider others' needs, not just your own. In this way you'll reach your objective with serenity```",
  "「50 鼎」 **Ting** : `the cauldron` ䷱\n*Holding*, *the cauldron*.\n```bf\nA lucky moment with positive and favourable external forces. Remember however that he or she who is in a privileged position must be attentive to those who are not as fortunate```",
  "「51 震」 **Chen** : `thunder` ䷲\n*Shake*, *the arousing (shock, thunder)* and *thunder*.\n```bf\nInfluential friends help and protect you\n\nAn event will occur which will change the actual state of the things and the current situation. Make the most of this change by being calm. This will help you strengthen your character and make you wise and virtuous```",
  "「52 艮」 **ken** : `stillness` ䷳\n*Bound*, *keeping still, mountain* and *stilling*.\n```bf\nDon't run away from situations and don't avoid what could be a problem. Now it is opportune for you to stop and observe things as they really are. This moment of calm and reflection will give you the necessary awareness to go forward in the future```",
  "「53 漸」 **Chien** : `gradual development` ䷴\n*Infiltrating*, *development (gradual progress)* and *advancement*.\n```bf\nTo obtain what you want, you must proceed gradually. Do not try to rush things or be taken by enthusiasm. To reach the desired results, go forward calm and with constancy; on the way you will med your errors```",
  "「54 歸妹」 **Kuei Mei** : `marrying girl` ䷵\n*Converting the Maiden*, *the marrying maiden* and *returning maiden*.\n```bf\nIn your social relations, both friendships and love affairs, you must always respect fundamental rules. The ones which establish the different roles people have. Try therefore to proceed with the right amount of discretion, avoiding difficulties and paving he way for success```",
  "「55 豐」 **Feng** : `greatness` ䷶\n*Abounding*, *abundance* and *fullness*.\n```bf\nFor you, this is the moment for great fortune and prosperity. You can reach your objectives and success. Make the most of this lucky situation. Remember that great opportunities only come round once and you must not let them slip away```",
  "「56 旅」 **Lu** : `the exile` ䷷\n*Sojourning*, *the wanderer* and *traveling*.\n```bf\nNow is not the moment for starting projects; consider how everything is changeable and prone to transformation. For the moment you must rely on what you have and make it suffice. Free yourself from the sense of possessions and expectations which poison life```",
  "「57 巽」 **Sun** : `the wind` ䷸\n*Ground*, *the gentle (the penetrating, wind)* and *calculations*.\n```bf\nIn this period, your doubts dissipate and problems are resolved. The best way to see clearly is to observe the situation. Everything will sort itself out```",
  "「58 兌」 **Tui** : `joyousness` ䷹\n*Open*, *the joyous, lake* and *usurpation*.\n```bf\nIn this period, you can overcome all your difficulties with cheerfulness and lightheartedness. You'll enjoy being with others. Share this positive energy with everyone; there is great harmony inside you and you must learn to appreciate and enjoy it```",
  "「59 渙」 **Huan** : `dispersion` ䷺\n*Dispersing*, *dispersion (dissolution)* and *dispersal*.\n```bf\nYou will get the impression that something is preventing you from reaching your aims. This could be because of your indifference or coldness towards others. So it's important you relax and get rid of all your tension: then you will be able to open up to others```",
  "「60 節」 **Chieh** : `limitation` ䷻\n*Articulating*, *limitation* and *moderation*.\n```bf\nIn this period, self control and self-discipline are fundamental. Only in this way will you be able to achieve your all and avoid any harm. Do not follow your instincts but try to limit yourself to always keeping in mind boundaries you must not cross```",
  "「61 中孚」 **Chung Fu** : `inner truth` ䷼\n*Center Returning*, *inner truth* and *central return*.\n```bf\nIf you want a good and satisfying relationship with people around you, sincerity and honesty are important. Do not be silent, even with those who are different from you. Be available and let others approach you with joy and spontaneity```",
  "「62 小過」 **Hsiao Kuo** : `small error/weakness` ䷽\n*Small Exceeding*, *preponderance of the small* and *small surpassing*.\n```bf\nIt is not the right moment to accomplish great undertakings. In fact, now you can obtain something by moving slowly and being constant. Be content with your position and in this way you'll go far```",
  "「63 既濟」 **Chi Chi** : `completion` ䷾\n*Already Fording*, *after completion* and *already completed* or *already done*.\n```bf\nFinally, you have achieved what you desired. Your objective and success have been reached, At this point you must simply refine some particulars. You must maintain what you have built: everything changes and so it'll be necessary to be careful that you don't lose everything```",
  "「64 未濟」 **Wei Chi** : `before completion` ䷿\n*Not Yet Fording*, *before completion* and *not yet completed*.\n```bf\nSadness. A period of misfortune that lasts 28 days\n\nThis period is full of useful opportunities for you to achieve what you want. This is a transitional phase which can move you from a negative problematic phase to a positive serene phase. Continue to be prudent: success is in your hands and nearby```",
  "「0」 **Ling** : `zero answer`\n```bf\ntis' not the best time to ask\n\nAnswers are not received```",
  "「x」**Zaici** : `ask again`\n```bf\nWasn't able to get an answer at this moment\n\nBreathe and ask again```"
]


class Oracle(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Understand any cituation with these oracle commands,\nbut don't take them too seriously """
    def __init__(self, bot):
        self.bot = bot
        self.mod_color = discord.Colour(0x7289da)  # Blurple
        self.user_color = discord.Colour(0xed791d)  # Orange

    # +------------------------------------------------------------+
    # |            Prediction command: EIGHTBALL                   |
    # +------------------------------------------------------------+
    @commands.command(aliases=['8ball'], no_pm=True)
    async def eightball(self, ctx, *, question=None):
        """ Ask questions to the 8ball """
        author = ctx.message.author

        if not question:    return await ctx.send(f'What is your question {author.mention}?')  # 

        if question.endswith("?") and question != "?":
            response = random.choice(ball_answers)

            e = discord.Embed(color=self.user_color)
            e.set_author(name=f"{author.display_name}'s question:", icon_url=author.avatar_url)
            e.description = f'```{question}```'
            e.add_field(name='\N{BILLIARDS} answer:', value=f'```css\n{response}```')
            e.set_footer(text=f"ADVICE: Don't take this too seriously | {date.today()}")

            try:    return await ctx.send(embed=e)
            except discord.HTTPException:    await ctx.send(f'\N{BILLIARDS} answer: ```css\n{response}```')

        else:    await ctx.send(f"*{question}* doesn't look like a yes/no question.")

    # +------------------------------------------------------------+
    # |            Prediction command: TAROT                       |
    # +------------------------------------------------------------+
    @commands.group(invoke_without_command=True, descriptions='3 cards spread reading', no_pm=True)
    async def tarot(self, ctx):
        """ Basic Tarot spread
        Usage:
        {prefix}tarot reading
        """
        i = await ctx.send('Please relax and focus on your question...')
        await asyncio.sleep(6)

        ii = 'Inhale deeply through your nose...'
        await i.edit(ii)
        await asyncio.sleep(5)

        iii = 'Exhale fully through your mouth...'
        await i.edit(iii)
        await asyncio.sleep(5)

        last = f'You are ready, type:\n**`{ctx.prefix}tarot reading`**\nI will shuffle the cards and pick three for you.'
        return await i.edit(last, delete_after=17)

    @tarot.command(no_pm=True)
    async def reading(self, ctx, *, question: str = None):
        """ 3 cards spread reading """
        u = ctx.author
        deck = 'https://i.imgur.com/rUAjxYx.png'

        try:
            s = await ctx.send(f"Allow me to shuffle my Tarot deck... {u.display_name}")
            await ctx.channel.trigger_typing()
            await asyncio.sleep(5)

            first = "1\N{COMBINING ENCLOSING KEYCAP} ***The Past:***\nThis card represents your situation*—why " \
                    "you’re currently in the spot you’re in*. It often symbolizes a person or relationship " \
                    "in your life that has influenced your question."
            second = "2\N{COMBINING ENCLOSING KEYCAP} ***The Present:***\nThis card represents the current " \
                     "problem, often as a direct result of the situation. Pay close attention to this card " \
                     "as it may be trying to show you things that you’ve previously overlooked."
            third = "3\N{COMBINING ENCLOSING KEYCAP} ***The Future:***\nThe final card in this 3-card spread " \
                    "provides guidance to face and overcome your issue. It may provide options you hadn’t " \
                    "considered or resources and people you’d overlooked."

            e = discord.Embed(color=self.user_color)
            e.set_author(name=f'Interpretation for {u.display_name}', icon_url=u.avatar_url)
            e.set_thumbnail(url=deck)
            e.set_author(name=f'{u.name} | {u.display_name} | {u.id}')

            e.add_field(name='Situation As It Is',
                        value=f'{first}\n{random.choice(card_deck)}\n', inline=False)
            e.add_field(name='Course of Action to be Taken',
                        value=f'{second}\n{random.choice(card_deck)}\n', inline=False)
            e.add_field(name='New Situation that Will Evolve',
                        value=f'{third}\n{random.choice(card_deck)}\n', inline=False)
            e.set_footer(text=f"Three Card spread reading | {date.today()}", icon_url=deck)

            await s.edit(embed=e)

        except discord.Forbidden:    await ctx.send('I need embed perms in this channel to send the full result.')

    # +------------------------------------------------------------+
    # |            Prediction command: ORACLE                      |
    # +------------------------------------------------------------+
    @commands.command(aliases=['crystalball', 'oracle', 'i-ching'], no_pm=True)
    async def iching(self, ctx, *, question: str = None):
        """ Ancient Oracle prediction
        Based on the ancient divination I Ching oracle,
        [use it as a guide]
        
        Usage:
        {prefix}oracle [yes/no question?]
        """
        iching = 'http://i.imgur.com/biEvXBN.png'
        u = ctx.message.author
        p = ctx.invoked_with

        if question is None:    return await ctx.send('You have to ask a yes/no question to use this command.', delete_after=23)

        if question.endswith('?') and question != '?':
            try:
                await ctx.send(f'Allow me to shuffle 3 ancient Chinese coins to answer your question... {u.display_name}')
                await ctx.channel.trigger_typing()
                await asyncio.sleep(5)
            except discord.Forbidden:    pass

            e = discord.Embed(colour=discord.Colour(0xc5b358))
            e.set_thumbnail(url=iching)
            e.set_footer(text=f"Ancient Oracle's inspiration | {date.today()}", icon_url=iching)
            e.set_author(name=f'{p} interpretation for {u.display_name}', icon_url=u.avatar_url)
            e.description = f'Meditation:\n{random.choice(oracle_answer)}'
            return await ctx.send(embed=e)

        else:    return await ctx.send(f"*{question}*/ndoesn't look like a yes/no question.", delete_after=69)


def setup(bot):
    bot.add_cog(Oracle(bot))
