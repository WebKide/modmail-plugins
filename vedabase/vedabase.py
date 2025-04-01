#  v0.02
"""
MIT License
Copyright (c) 2020-2025 WebKide [d.id @323578534763298816]
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

import discord
import aiohttp
import random
import asyncio
import time

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from typing import Tuple, Union
from discord.ext import commands
from datetime import datetime

# Chapter info dict for Bhagavad Gītā
BG_CHAPTER_INFO = {
    1: {"total_verses": 46, "grouped_ranges": [(16, 18), (21, 22), (32, 35), (37, 38)], "chapter_title": "1. Observing the Armies on the Battlefield of Kurukṣetra"},
    2: {"total_verses": 72, "grouped_ranges": [(42, 43)], "chapter_title": "2. Contents of the Gītā Summarized"},
    3: {"total_verses": 43, "grouped_ranges": [], "chapter_title": "3. Karma-yoga"},
    4: {"total_verses": 42, "grouped_ranges": [], "chapter_title": "4. Transcendental Knowledge"},
    5: {"total_verses": 29, "grouped_ranges": [(8, 9), (27, 28)], "chapter_title": "5. Karma-yoga — Action in Kṛṣṇa Consciousness"},
    6: {"total_verses": 47, "grouped_ranges": [(11, 12), (13, 14), (20, 23)], "chapter_title": "6. Sāṅkhya-yoga"},
    7: {"total_verses": 30, "grouped_ranges": [], "chapter_title": "7. Knowledge of the Absolute"},
    8: {"total_verses": 28, "grouped_ranges": [], "chapter_title": "8. Attaining the Supreme"},
    9: {"total_verses": 34, "grouped_ranges": [], "chapter_title": "9. The Most Confidential Knowledge"},
    10: {"total_verses": 42, "grouped_ranges": [(4, 5), (12, 13)], "chapter_title": "10. The Opulence of the Absolute"},
    11: {"total_verses": 55, "grouped_ranges": [(10, 11), (26, 27), (41, 42)], "chapter_title": "11. The Universal Form"},
    12: {"total_verses": 20, "grouped_ranges": [(3, 4), (6, 7), (13, 14), (18, 19)], "chapter_title": "12. Devotional Service"},
    13: {"total_verses": 35, "grouped_ranges": [(1, 2), (6, 7), (8, 12)], "chapter_title": "13. Nature, the Enjoyer, and Consciousness"},
    14: {"total_verses": 27, "grouped_ranges": [(22, 25)], "chapter_title": "14. The Three Modes of Material Nature"},
    15: {"total_verses": 20, "grouped_ranges": [(3, 4)], "chapter_title": "15. The Yoga of the Supreme Person"},
    16: {"total_verses": 24, "grouped_ranges": [(1, 3), (11, 12), (13, 15)], "chapter_title": "16. The Divine and Demoniac Natures"},
    17: {"total_verses": 28, "grouped_ranges": [(5, 6), (26, 27)], "chapter_title": "17. The Divisions of Faith"},
    18: {"total_verses": 78, "grouped_ranges": [(13, 14), (36, 37), (51, 53)], "chapter_title": "18. Conclusion-The Perfection of Renunciation"}
}

# Book info for Caitanya-caritāmṛta
CC_BOOK_INFO = {
    "adi": {
        "num": 1,
        "title": "Ādi-līlā",
        "chapter_title": [
            "CHAPTER ONE: The Spiritual Masters",
            "CHAPTER TWO: Śrī Caitanya Mahāprabhu, the Supreme Personality of Godhead",
            "CHAPTER THREE: The External Reasons for the Appearance of Śrī Caitanya Mahāprabhu",
            "CHAPTER FOUR: The Confidential Reasons for the Appearance of Śrī Caitanya Mahāprabhu",
            "CHAPTER FIVE: The Glories of Lord Nityānanda Balarāma",
            "CHAPTER SIX: The Glories of Śrī Advaita Ācārya",
            "CHAPTER SEVEN: Lord Caitanya in Five Features",
            "CHAPTER EIGHT: The Author Receives the Orders of Kṛṣṇa and Guru",
            "CHAPTER NINE: The Desire Tree of Devotional Service",
            "CHAPTER TEN: The Trunk, Branches and Subbranches of the Caitanya Tree",
            "CHAPTER ELEVEN: The Expansions of Lord Nityānanda",
            "CHAPTER TWELVE: The Expansions of Advaita Ācārya and Gadādhara Paṇḍita",
            "CHAPTER THIRTEEN: The Advent of Lord Śrī Caitanya Mahāprabhu",
            "CHAPTER FOURTEEN: Lord Caitanya’s Childhood Pastimes",
            "CHAPTER FIFTEEN: The Lord’s Paugaṇḍa-līlā",
            "CHAPTER SIXTEEN: The Pastimes of the Lord in His Childhood and Youth",
            "CHAPTER SEVENTEEN: The Pastimes of Lord Caitanya Mahāprabhu in His Youth"
        ]
    },
    "madhya": {
        "num": 2,
        "title": "Madhya-līlā",
        "chapter_title": [
            "CHAPTER ONE: The Later Pastimes of Lord Śrī Caitanya Mahāprabhu",
            "CHAPTER TWO: The Ecstatic Manifestations of Lord Śrī Caitanya Mahāprabhu",
            "CHAPTER THREE: Lord Śrī Caitanya Mahāprabhu’s Stay at the House of Advaita Ācārya",
            "CHAPTER FOUR: Śrī Mādhavendra Purī’s Devotional Service",
            "CHAPTER FIVE: The Activities of Sākṣi-gopāla",
            "CHAPTER SIX: The Liberation of Sārvabhauma Bhaṭṭācārya",
            "CHAPTER SEVEN: The Lord Begins His Tour of South India",
            "CHAPTER EIGHT: Talks Between Śrī Caitanya Mahāprabhu and Rāmānanda Rāya",
            "CHAPTER NINE: Lord Śrī Caitanya Mahāprabhu’s Travels to the Holy Places",
            "CHAPTER TEN: The Lord’s Return to Jagannātha Purī",
            "CHAPTER ELEVEN: The Beḍā-kīrtana Pastimes of Śrī Caitanya Mahāprabhu",
            "CHAPTER TWELVE: The Cleansing of the Guṇḍicā Temple",
            "CHAPTER THIRTEEN: The Ecstatic Dancing of the Lord at Ratha-yātrā",
            "CHAPTER FOURTEEN: Performance of the Vṛndāvana Pastimes",
            "CHAPTER FIFTEEN: The Lord Accepts Prasādam at the House of Sārvabhauma Bhaṭṭācārya",
            "CHAPTER SIXTEEN: The Lord’s Attempt to Go to Vṛndāvana",
            "CHAPTER SEVENTEEN: The Lord Travels to Vṛndāvana",
            "CHAPTER EIGHTEEN: Lord Śrī Caitanya Mahāprabhu’s Visit to Śrī Vṛndāvana",
            "CHAPTER NINETEEN: Lord Śrī Caitanya Mahāprabhu Instructs Śrīla Rūpa Gosvāmī",
            "CHAPTER TWENTY: Lord Śrī Caitanya Mahāprabhu Instructs Sanātana Gosvāmī in the Science of the Absolute Truth",
            "CHAPTER TWENTY-ONE: The Opulence and Sweetness of Lord Śrī Kṛṣṇa",
            "CHAPTER TWENTY-TWO: The Process of Devotional Service",
            "CHAPTER TWENTY-THREE: Life’s Ultimate Goal — Love of Godhead",
            "CHAPTER TWENTY-FOUR: The Sixty-One Explanations of the Ātmārāma Verse",
            "CHAPTER TWENTY-FIVE: How All the Residents of Vārāṇasī Became Vaiṣṇavas"
        ]
    },
    "antya": {
        "num": 3,
        "title": "Antya-līlā",
        "chapter_title": [
            "CHAPTER ONE: Śrīla Rūpa Gosvāmī’s Second Meeting with the Lord",
            "CHAPTER TWO: The Chastisement of Junior Haridāsa",
            "CHAPTER THREE: The Glories of Śrīla Haridāsa Ṭhākura",
            "CHAPTER FOUR: Sanātana Gosvāmī Visits the Lord at Jagannātha Purī",
            "CHAPTER FIVE: How Pradyumna Miśra Received Instructions from Rāmānanda Rāya",
            "CHAPTER SIX: The Meeting of Śrī Caitanya Mahāprabhu and Raghunātha dāsa Gosvāmī",
            "CHAPTER SEVEN: The Meeting of Śrī Caitanya Mahāprabhu and Vallabha Bhaṭṭa",
            "CHAPTER EIGHT: Rāmacandra Purī Criticizes the Lord",
            "CHAPTER NINE: The Deliverance of Gopīnātha Paṭṭanāyaka",
            "CHAPTER TEN: Śrī Caitanya Mahāprabhu Accepts Prasādam from His Devotees",
            "CHAPTER ELEVEN: The Passing of Haridāsa Ṭhākura",
            "CHAPTER TWELVE: The Loving Dealings Between Lord Śrī Caitanya Mahāprabhu and Jagadānanda Paṇḍita",
            "CHAPTER THIRTEEN: Pastimes with Jagadānanda Paṇḍita and Raghunātha Bhaṭṭa Gosvāmī",
            "CHAPTER FOURTEEN: Lord Śrī Caitanya Mahāprabhu’s Feelings of Separation from Kṛṣṇa",
            "CHAPTER FIFTEEN: The Transcendental Madness of Lord Śrī Caitanya Mahāprabhu",
            "CHAPTER SIXTEEN: Lord Śrī Caitanya Mahāprabhu Tastes Nectar from the Lips of Lord Śrī Kṛṣṇa",
            "CHAPTER SEVENTEEN: The Bodily Transformations of Lord Śrī Caitanya Mahāprabhu",
            "CHAPTER EIGHTEEN: Rescuing the Lord from the Sea",
            "CHAPTER NINETEEN: The Inconceivable Behavior of Lord Śrī Caitanya Mahāprabhu",
            "CHAPTER TWENTY: The Śikṣāṣṭaka Prayers"
        ]
    },
    "1": {"title": "Ādi-līlā", "chapter_title": CC_BOOK_INFO["adi"]["chapter_title"]},
    "2": {"title": "Madhya-līlā", "chapter_title": CC_BOOK_INFO["madhya"]["chapter_title"]},
    "3": {"title": "Antya-līlā", "chapter_title": CC_BOOK_INFO["antya"]["chapter_title"]}
}


# Canto info for Śrīmad Bhāgavatam
SB_CANTO_INFO = {
    "1": {
        "title": "Canto 1: Creation",
        "chapter_title": [
            "CHAPTER ONE: Questions by the Sages",
            "CHAPTER TWO: Divinity and Divine Service",
            "CHAPTER THREE: Kṛṣṇa Is the Source of All Incarnations",
            "CHAPTER FOUR: The Appearance of Śrī Nārada",
            "CHAPTER FIVE: Nārada’s Instructions on Śrīmad-Bhāgavatam for Vyāsadeva",
            "CHAPTER SIX: Conversation Between Nārada and Vyāsadeva",
            "CHAPTER SEVEN: The Son of Droṇa Punished",
            "CHAPTER EIGHT: Prayers by Queen Kuntī and Parīkṣit Saved",
            "CHAPTER NINE: The Passing Away of Bhīṣmadeva in the Presence of Lord Kṛṣṇa",
            "CHAPTER TEN: Departure of Lord Kṛṣṇa for Dvārakā",
            "CHAPTER ELEVEN: Lord Kṛṣṇa’s Entrance into Dvārakā",
            "CHAPTER TWELVE: Birth of Emperor Parīkṣit",
            "CHAPTER THIRTEEN: Dhṛtarāṣṭra Quits Home",
            "CHAPTER FOURTEEN: The Disappearance of Lord Kṛṣṇa",
            "CHAPTER FIFTEEN: The Pāṇḍavas Retire Timely",
            "CHAPTER SIXTEEN: How Parīkṣit Received the Age of Kali",
            "CHAPTER SEVENTEEN: Punishment and Reward of Kali",
            "CHAPTER EIGHTEEN: Mahārāja Parīkṣit Cursed by a Brāhmaṇa Boy",
            "CHAPTER NINETEEN: The Appearance of Śukadeva Gosvāmī"
        ]
    },
    "2": {
        "title": "Canto 2: The Cosmic Manifestation",
        "chapter_title": [
            "CHAPTER ONE: The First Step in God Realization",
            "CHAPTER TWO: The Lord in the Heart",
            "CHAPTER THREE: Pure Devotional Service: The Change in Heart",
            "CHAPTER FOUR: The Process of Creation",
            "CHAPTER FIVE: The Cause of All Causes",
            "CHAPTER SIX: Puruṣa-sūkta Confirmed",
            "CHAPTER SEVEN: Scheduled Incarnations with Specific Functions",
            "CHAPTER EIGHT: Questions by King Parīkṣit",
            "CHAPTER NINE: Answers by Citing the Lord’s Version",
            "CHAPTER TEN: Bhāgavatam Is the Answer to All Questions"
        ]
    },
    "3": {
        "title": "Canto 3: The Status Quo",
        "chapter_title": [
            "CHAPTER ONE: Questions by Vidura",
            "CHAPTER TWO: Remembrance of Lord Kṛṣṇa",
            "CHAPTER THREE: The Lord’s Pastimes Out of Vṛndāvana",
            "CHAPTER FOUR: Vidura Approaches Maitreya",
            "CHAPTER FIVE: Vidura’s Talks with Maitreya",
            "CHAPTER SIX: Creation of the Universal Form",
            "CHAPTER SEVEN: Further Inquires by Vidura",
            "CHAPTER EIGHT: Manifestation of Brahmā from Garbhodakaśāyī Viṣṇu",
            "CHAPTER NINE: Brahmā’s Prayers for Creative Energy",
            "CHAPTER TEN: Divisions of the Creation",
            "CHAPTER ELEVEN: Calculation of Time, from the Atom",
            "CHAPTER TWELVE: Creation of the Kumāras and Others",
            "CHAPTER THIRTEEN: The Appearance of Lord Varāha",
            "CHAPTER FOURTEEN: Pregnancy of Diti in the Evening",
            "CHAPTER FIFTEEN: Description of the Kingdom of God",
            "CHAPTER SIXTEEN: The Two Doorkeepers of Vaikuṇṭha, Jaya and Vijaya, Cursed by the Sages",
            "CHAPTER SEVENTEEN: Victory of Hiraṇyākṣa Over All the Directions of the Universe",
            "CHAPTER EIGHTEEN: The Battle Between Lord Boar and the Demon Hiraṇyākṣa",
            "CHAPTER NINETEEN: The Killing of the Demon Hiraṇyākṣa",
            "CHAPTER TWENTY: Conversation Between Maitreya and Vidura",
            "CHAPTER TWENTY-ONE: Conversation Between Manu and Kardama",
            "CHAPTER TWENTY-TWO: The Marriage of Kardama Muni and Devahūti",
            "CHAPTER TWENTY-THREE: Devahūti’s Lamentation",
            "CHAPTER TWENTY-FOUR: The Renunciation of Kardama Muni",
            "CHAPTER TWENTY-FIVE: The Glories of Devotional Service",
            "CHAPTER TWENTY-SIX: Fundamental Principles of Material Nature",
            "CHAPTER TWENTY-SEVEN: Understanding Material Nature",
            "CHAPTER TWENTY-EIGHT: Kapila’s Instructions on the Execution of Devotional Service",
            "CHAPTER TWENTY-NINE: Explanation of Devotional Service by Lord Kapila",
            "CHAPTER THIRTY: Description by Lord Kapila of Adverse Fruitive Activities",
            "CHAPTER THIRTY-ONE: Lord Kapila’s Instructions on the Movements of the Living Entities",
            "CHAPTER THIRTY-TWO: Entanglement in Fruitive Activities",
            "CHAPTER THIRTY-THREE: Activities of Kapila"
        ]
    },
    "4": {
        "title": "Canto 4: The Creation of the Fourth Order",
        "chapter_title": [
            "CHAPTER ONE: Genealogical Table of the Daughters of Manu",
            "CHAPTER TWO: Dakṣa Curses Lord Śiva",
            "CHAPTER THREE: Talks Between Lord Śiva and Satī",
            "CHAPTER FOUR: Satī Quits Her Body",
            "CHAPTER FIVE: Frustration of the Sacrifice of Dakṣa",
            "CHAPTER SIX: Brahmā Satisfies Lord Śiva",
            "CHAPTER SEVEN: The Sacrifice Performed by Dakṣa",
            "CHAPTER EIGHT: Dhruva Mahārāja Leaves Home for the Forest",
            "CHAPTER NINE: Dhruva Mahārāja Returns Home",
            "CHAPTER TEN: Dhruva Mahārāja’s Fight with the Yakṣas",
            "CHAPTER ELEVEN: Svāyambhuva Manu Advises Dhruva Mahārāja to Stop Fighting",
            "CHAPTER TWELVE: Dhruva Mahārāja Goes Back to Godhead",
            "CHAPTER THIRTEEN: Description of the Descendants of Dhruva Mahārāja",
            "CHAPTER FOURTEEN: The Story of King Vena",
            "CHAPTER FIFTEEN: King Pṛthu’s Appearance and Coronation",
            "CHAPTER SIXTEEN: Praise of King Pṛthu by the Professional Reciters",
            "CHAPTER SEVENTEEN: Mahārāja Pṛthu Becomes Angry at the Earth",
            "CHAPTER EIGHTEEN: Pṛthu Mahārāja Milks the Earth Planet",
            "CHAPTER NINETEEN: King Pṛthu’s One Hundred Horse Sacrifices",
            "CHAPTER TWENTY: Lord Viṣṇu’s Appearance in the Sacrificial Arena of Mahārāja Pṛthu",
            "CHAPTER TWENTY-ONE: Instructions by Mahārāja Pṛthu",
            "CHAPTER TWENTY-TWO: Pṛthu Mahārāja’s Meeting with the Four Kumāras",
            "CHAPTER TWENTY-THREE: Mahārāja Pṛthu’s Going Back Home",
            "CHAPTER TWENTY-FOUR: Chanting the Song Sung by Lord Śiva",
            "CHAPTER TWENTY-FIVE: The Descriptions of the Characteristics of King Purañjana",
            "CHAPTER TWENTY-SIX: King Purañjana Goes to the Forest to Hunt, and His Queen Becomes Angry",
            "CHAPTER TWENTY-SEVEN: Attack by Caṇḍavega on the City of King Purañjana; the Character of Kālakanyā",
            "CHAPTER TWENTY-EIGHT: Purañjana Becomes a Woman in the Next Life",
            "CHAPTER TWENTY-NINE: Talks Between Nārada and King Prācīnabarhi",
            "CHAPTER THIRTY: The Activities of the Pracetās",
            "CHAPTER THIRTY-ONE: Nārada Instructs the Pracetās"
        ]
    },
    "5": {
        "title": "Canto 5: The Creative Impetus",
        "chapter_title": [
            "CHAPTER ONE: The Activities of Mahārāja Priyavrata",
            "CHAPTER TWO: The Activities of Mahārāja Āgnīdhra",
            "CHAPTER THREE: Ṛṣabhadeva’s Appearance in the Womb of Merudevī, the Wife of King Nābhi",
            "CHAPTER FOUR: The Characteristics of Ṛṣabhadeva, the Supreme Personality of Godhead",
            "CHAPTER FIVE: Lord Ṛṣabhadeva’s Teachings to His Sons",
            "CHAPTER SIX: The Activities of Lord Ṛṣabhadeva",
            "CHAPTER SEVEN: The Activities of King Bharata",
            "CHAPTER EIGHT: A Description of the Character of Bharata Mahārāja",
            "CHAPTER NINE: The Supreme Character of Jaḍa Bharata",
            "CHAPTER TEN: The Discussion Between Jaḍa Bharata and Mahārāja Rahūgaṇa",
            "CHAPTER ELEVEN: Jaḍa Bharata Instructs King Rahūgaṇa",
            "CHAPTER TWELVE: Conversation Between Mahārāja Rahūgaṇa and Jaḍa Bharata",
            "CHAPTER THIRTEEN: Further Talks Between King Rahūgaṇa and Jaḍa Bharata",
            "CHAPTER FOURTEEN: The Material World as the Great Forest of Enjoyment",
            "CHAPTER FIFTEEN: The Glories of the Descendants of King Priyavrata",
            "CHAPTER SIXTEEN: A Description of Jambūdvīpa",
            "CHAPTER SEVENTEEN: The Descent of the River Ganges",
            "CHAPTER EIGHTEEN: The Prayers Offered to the Lord by the Residents of Jambūdvīpa",
            "CHAPTER NINETEEN: A Description of the Island of Jambūdvīpa",
            "CHAPTER TWENTY: Studying the Structure of the Universe",
            "CHAPTER TWENTY-ONE: The Movements of the Sun",
            "CHAPTER TWENTY-TWO: The Orbits of the Planets",
            "CHAPTER TWENTY-THREE: The Śiśumāra Planetary Systems",
            "CHAPTER TWENTY-FOUR: The Subterranean Heavenly Planets",
            "CHAPTER TWENTY-FIVE: The Glories of Lord Ananta",
            "CHAPTER TWENTY-SIX: A Description of the Hellish Planets"
        ]
    },
    "6": {
        "title": "Canto 6: Prescribed Duties for Mankind",
        "chapter_title": [
            "CHAPTER ONE: The History of the Life of Ajāmila",
            "CHAPTER TWO: Ajāmila Delivered by the Viṣṇudūtas",
            "CHAPTER THREE: Yamarāja Instructs His Messengers",
            "CHAPTER FOUR: The Haṁsa-guhya Prayers Offered to the Lord by Prajāpati Dakṣa",
            "CHAPTER FIVE: Nārada Muni Cursed by Prajāpati Dakṣa",
            "CHAPTER SIX: The Progeny of the Daughters of Dakṣa",
            "CHAPTER SEVEN: Indra Offends His Spiritual Master, Bṛhaspati.",
            "CHAPTER EIGHT: The Nārāyaṇa-kavaca Shield",
            "CHAPTER NINE: Appearance of the Demon Vṛtrāsura",
            "CHAPTER TEN: The Battle Between the Demigods and Vṛtrāsura",
            "CHAPTER ELEVEN: The Transcendental Qualities of Vṛtrāsura",
            "CHAPTER TWELVE: Vṛtrāsura’s Glorious Death",
            "CHAPTER THIRTEEN: King Indra Afflicted by Sinful Reaction",
            "CHAPTER FOURTEEN: King Citraketu’s Lamentation",
            "CHAPTER FIFTEEN: The Saints Nārada and Aṅgirā Instruct King Citraketu",
            "CHAPTER SIXTEEN: King Citraketu Meets the Supreme Lord",
            "CHAPTER SEVENTEEN: Mother Pārvatī Curses Citraketu",
            "CHAPTER EIGHTEEN: Diti Vows to Kill King Indra",
            "CHAPTER NINETEEN: Performing the Puṁsavana Ritualistic Ceremony"
        ]
    },
    "7": {
        "title": "Canto 7: The Science of God",
        "chapter_title": [
            "CHAPTER ONE: The Supreme Lord Is Equal to Everyone",
            "CHAPTER TWO: Hiraṇyakaśipu, King of the Demons",
            "CHAPTER THREE: Hiraṇyakaśipu’s Plan to Become Immortal",
            "CHAPTER FOUR: Hiraṇyakaśipu Terrorizes the Universe",
            "CHAPTER FIVE: Prahlāda Mahārāja, the Saintly Son of Hiraṇyakaśipu",
            "CHAPTER SIX: Prahlāda Instructs His Demoniac Schoolmates",
            "CHAPTER SEVEN: What Prahlāda Learned in the Womb",
            "CHAPTER EIGHT: Lord Nṛsiṁhadeva Slays the King of the Demons",
            "CHAPTER NINE: Prahlāda Pacifies Lord Nṛsiṁhadeva with Prayers",
            "CHAPTER TEN: Prahlāda, the Best Among Exalted Devotees",
            "CHAPTER ELEVEN: The Perfect Society: Four Social Classes",
            "CHAPTER TWELVE: The Perfect Society: Four Spiritual Classes",
            "CHAPTER THIRTEEN: The Behavior of a Perfect Person",
            "CHAPTER FOURTEEN: Ideal Family Life",
            "CHAPTER FIFTEEN: Instructions for Civilized Human Beings"
        ]
    },
    "8": {
        "title": "Canto 8: Withdrawal of the Cosmic Creations",
        "chapter_title": [
            "CHAPTER ONE: The Manus, Administrators of the Universe",
            "CHAPTER TWO: The Elephant Gajendra’s Crisis",
            "CHAPTER THREE: Gajendra’s Prayers of Surrender",
            "CHAPTER FOUR: Gajendra Returns to the Spiritual World",
            "CHAPTER FIVE: The Demigods Appeal to the Lord for Protection",
            "CHAPTER SIX: The Demigods and Demons Declare a Truce",
            "CHAPTER SEVEN: Lord Śiva Saves the Universe by Drinking Poison",
            "CHAPTER EIGHT: The Churning of the Milk Ocean",
            "CHAPTER NINE: The Lord Incarnates as Mohinī-Mūrti",
            "CHAPTER TEN: The Battle Between the Demigods and the Demons",
            "CHAPTER ELEVEN: King Indra Annihilates the Demons",
            "CHAPTER TWELVE: The Mohinī-mūrti Incarnation Bewilders Lord Śiva",
            "CHAPTER THIRTEEN: Description of Future Manus",
            "CHAPTER FOURTEEN: The System of Universal Management",
            "CHAPTER FIFTEEN: Bali Mahārāja Conquers the Heavenly Planets",
            "CHAPTER SIXTEEN: Executing the Payo-vrata Process of Worship",
            "CHAPTER SEVENTEEN: The Supreme Lord Agrees to Become Aditi’s Son",
            "CHAPTER EIGHTEEN: Lord Vāmanadeva, the Dwarf Incarnation",
            "CHAPTER NINETEEN: Lord Vāmanadeva Begs Charity from Bali Mahārāja",
            "CHAPTER TWENTY: Bali Mahārāja Surrenders the Universe",
            "CHAPTER TWENTY-ONE: Bali Mahārāja Arrested by the Lord",
            "CHAPTER TWENTY-TWO: Bali Mahārāja Surrenders His Life",
            "CHAPTER TWENTY-THREE: The Demigods Regain the Heavenly Planets",
            "CHAPTER TWENTY-FOUR: Matsya, the Lord’s Fish Incarnation"
        ]
    },
    "9": {
        "title": "Canto 9: Liberation",
        "chapter_title": [
            "CHAPTER ONE: King Sudyumna Becomes a Woman",
            "CHAPTER TWO: The Dynasties of the Sons of Manu",
            "CHAPTER THREE: The Marriage of Sukanyā and Cyavana Muni",
            "CHAPTER FOUR: Ambarīṣa Mahārāja Offended by Durvāsā Muni",
            "CHAPTER FIVE: Durvāsā Muni’s Life Spared",
            "CHAPTER SIX: The Downfall of Saubhari Muni",
            "CHAPTER SEVEN: The Descendants of King Māndhātā",
            "CHAPTER EIGHT: The Sons of Sagara Meet Lord Kapiladeva",
            "CHAPTER NINE: The Dynasty of Aṁśumān",
            "CHAPTER TEN: The Pastimes of the Supreme Lord, Rāmacandra",
            "CHAPTER ELEVEN: Lord Rāmacandra Rules the World",
            "CHAPTER TWELVE: The Dynasty of Kuśa, the Son of Lord Rāmacandra",
            "CHAPTER THIRTEEN: The Dynasty of Mahārāja Nimi",
            "CHAPTER FOURTEEN: King Purūravā Enchanted by Urvaśī",
            "CHAPTER FIFTEEN: Paraśurāma, the Lord’s Warrior Incarnation",
            "CHAPTER SIXTEEN: Lord Paraśurāma Destroys the World’s Ruling Class",
            "CHAPTER SEVENTEEN: The Dynasties of the Sons of Purūravā",
            "CHAPTER EIGHTEEN: King Yayāti Regains His Youth",
            "CHAPTER NINETEEN: King Yayāti Achieves Liberation",
            "CHAPTER TWENTY: The Dynasty of Pūru",
            "CHAPTER TWENTY-ONE: The Dynasty of Bharata",
            "CHAPTER TWENTY-TWO: The Descendants of Ajamīḍha",
            "CHAPTER TWENTY-THREE: The Dynasties of the Sons of Yayāti",
            "CHAPTER TWENTY-FOUR: Kṛṣṇa, the Supreme Personality of Godhead"
        ]
    },
    "10": {
        "title": "Canto 10: The Summum Bonum",
        "chapter_title": [
            "CHAPTER ONE: The Advent of Lord Kṛṣṇa: Introduction",
            "CHAPTER TWO: Prayers by the Demigods for Lord Kṛṣṇa in the Womb",
            "CHAPTER THREE: The Birth of Lord Kṛṣṇa",
            "CHAPTER FOUR: The Atrocities of King Kaṁsa",
            "CHAPTER FIVE: The Meeting of Nanda Mahārāja and Vasudeva",
            "CHAPTER SIX: The Killing of the Demon Pūtanā",
            "CHAPTER SEVEN: The Killing of the Demon Tṛṇāvarta",
            "CHAPTER EIGHT: Lord Kṛṣṇa Shows the Universal Form Within His Mouth",
            "CHAPTER NINE: Mother Yaśodā Binds Lord Kṛṣṇa",
            "CHAPTER TEN: The Deliverance of the Yamala-arjuna Trees",
            "CHAPTER ELEVEN: The Childhood Pastimes of Kṛṣṇa",
            "CHAPTER TWELVE: The Killing of the Demon Aghāsura",
            "CHAPTER THIRTEEN: The Stealing of the Boys and Calves by Brahmā",
            "CHAPTER FOURTEEN: Brahmā’s Prayers to Lord Kṛṣṇa",
            "CHAPTER FIFTEEN: The Killing of Dhenuka, the Ass Demon",
            "CHAPTER SIXTEEN: Kṛṣṇa Chastises the Serpent Kāliya",
            "CHAPTER SEVENTEEN: The History of Kāliya",
            "CHAPTER EIGHTEEN: Lord Balarāma Slays the Demon Pralamba",
            "CHAPTER NINETEEN: Swallowing the Forest Fire",
            "CHAPTER TWENTY: The Rainy Season and Autumn in Vṛndāvana",
            "CHAPTER TWENTY-ONE: The Gopīs Glorify the Song of Kṛṣṇa’s Flute",
            "CHAPTER TWENTY-TWO: Kṛṣṇa Steals the Garments of the Unmarried Gopīs",
            "CHAPTER TWENTY-THREE: The Brāhmaṇas’ Wives Blessed",
            "CHAPTER TWENTY-FOUR: Worshiping Govardhana Hill",
            "CHAPTER TWENTY-FIVE: Lord Kṛṣṇa Lifts Govardhana Hill",
            "CHAPTER TWENTY-SIX: Wonderful Kṛṣṇa",
            "CHAPTER TWENTY-SEVEN: Lord Indra and Mother Surabhi Offer Prayers",
            "CHAPTER TWENTY-EIGHT: Kṛṣṇa Rescues Nanda Mahārāja from the Abode of Varuṇa",
            "CHAPTER TWENTY-NINE: Kṛṣṇa and the Gopīs Meet for the Rāsa Dance",
            "CHAPTER THIRTY: The Gopīs Search for Kṛṣṇa",
            "CHAPTER THIRTY-ONE: The Gopīs’ Songs of Separation",
            "CHAPTER THIRTY-TWO: The Reunion",
            "CHAPTER THIRTY-THREE: The Rāsa Dance",
            "CHAPTER THIRTY-FOUR: Nanda Mahārāja Saved and Śaṅkhacūḍa Slain",
            "CHAPTER THIRTY-FIVE: The Gopīs Sing of Kṛṣṇa as He Wanders in the Forest",
            "CHAPTER THIRTY-SIX: The Slaying of Ariṣṭā, the Bull Demon",
            "CHAPTER THIRTY-SEVEN: The Killing of the Demons Keśi and Vyoma",
            "CHAPTER THIRTY-EIGHT: Akrūra’s Arrival in Vṛndāvana",
            "CHAPTER THIRTY-NINE: Akrūra’s Vision",
            "CHAPTER FORTY: The Prayers of Akrūra",
            "CHAPTER FORTY-ONE: Kṛṣṇa and Balarāma Enter Mathurā",
            "CHAPTER FORTY-TWO: The Breaking of the Sacrificial Bow",
            "CHAPTER FORTY-THREE: Kṛṣṇa Kills the Elephant Kuvalayāpīḍa",
            "CHAPTER FORTY-FOUR: The Killing of Kaṁsa",
            "CHAPTER FORTY-FIVE: Kṛṣṇa Rescues His Teacher’s Son",
            "CHAPTER FORTY-SIX: Uddhava Visits Vṛndāvana",
            "CHAPTER FORTY-SEVEN: The Song of the Bee",
            "CHAPTER FORTY-EIGHT: Kṛṣṇa Pleases His Devotees",
            "CHAPTER FORTY-NINE: Akrūra’s Mission in Hastināpura",
            "CHAPTER FIFTY: Kṛṣṇa Establishes the City of Dvārakā",
            "CHAPTER FIFTY-ONE: The Deliverance of Mucukunda",
            "CHAPTER FIFTY-TWO: Rukmiṇī’s Message to Lord Kṛṣṇa",
            "CHAPTER FIFTY-THREE: Kṛṣṇa Kidnaps Rukmiṇī",
            "CHAPTER FIFTY-FOUR: The Marriage of Kṛṣṇa and Rukmiṇī",
            "CHAPTER FIFTY-FIVE: The History of Pradyumna",
            "CHAPTER FIFTY-SIX: The Syamantaka Jewel",
            "CHAPTER FIFTY-SEVEN: Satrājit Murdered, the Jewel Returned",
            "CHAPTER FIFTY-EIGHT: Kṛṣṇa Marries Five Princesses",
            "CHAPTER FIFTY-NINE: The Killing of the Demon Naraka",
            "CHAPTER SIXTY: Lord Kṛṣṇa Teases Queen Rukmiṇī.",
            "CHAPTER SIXTY-ONE: Lord Balarāma Slays Rukmī",
            "CHAPTER SIXTY-TWO: The Meeting of Ūṣā and Aniruddha",
            "CHAPTER SIXTY-THREE: Lord Kṛṣṇa Fights with Bāṇāsura",
            "CHAPTER SIXTY-FOUR: The Deliverance of King Nṛga",
            "CHAPTER SIXTY-FIVE: Lord Balarāma Visits Vṛndāvana",
            "CHAPTER SIXTY-SIX: Pauṇḍraka, the False Vāsudeva",
            "CHAPTER SIXTY-SEVEN: Lord Balarāma Slays Dvivida Gorilla",
            "CHAPTER SIXTY-EIGHT: The Marriage of Sāmba",
            "CHAPTER SIXTY-NINE: Nārada Muni Visits Lord Kṛṣṇa’s Palaces in Dvārakā",
            "CHAPTER SEVENTY: Lord Kṛṣṇa’s Daily Activities",
            "CHAPTER SEVENTY-ONE: The Lord Travels to Indraprastha",
            "CHAPTER SEVENTY-TWO: The Slaying of the Demon Jarāsandha",
            "CHAPTER SEVENTY-THREE: Lord Kṛṣṇa Blesses the Liberated Kings",
            "CHAPTER SEVENTY-FOUR: The Deliverance of Śiśupāla at the Rājasūya Sacrifice",
            "CHAPTER SEVENTY-FIVE: Duryodhana Humiliated",
            "CHAPTER SEVENTY-SIX: The Battle Between Śālva and the Vṛṣṇis",
            "CHAPTER SEVENTY-SEVEN: Lord Kṛṣṇa Slays the Demon Śālva",
            "CHAPTER SEVENTY-EIGHT: The Killing of Dantavakra, Vidūratha and Romaharṣaṇa",
            "CHAPTER SEVENTY-NINE: Lord Balarāma Goes on Pilgrimage",
            "CHAPTER EIGHTY: The Brāhmaṇa Sudāmā Visits Lord Kṛṣṇa in Dvārakā",
            "CHAPTER EIGHTY-ONE: The Lord Blesses Sudāmā Brāhmaṇa",
            "CHAPTER EIGHTY-TWO: Kṛṣṇa and Balarāma Meet the Inhabitants of Vṛndāvana",
            "CHAPTER EIGHTY-THREE: Draupadī Meets the Queens of Kṛṣṇa",
            "CHAPTER EIGHTY-FOUR: The Sages’ Teachings at Kurukṣetra",
            "CHAPTER EIGHTY-FIVE: Lord Kṛṣṇa Instructs Vasudeva and Retrieves Devakī’s Sons",
            "CHAPTER EIGHTY-SIX: Arjuna Kidnaps Subhadrā, and Kṛṣṇa Blesses His Devotees",
            "CHAPTER EIGHTY-SEVEN: The Prayers of the Personified Vedas",
            "CHAPTER EIGHTY-EIGHT: Lord Śiva Saved from Vṛkāsura",
            "CHAPTER EIGHTY-NINE: Kṛṣṇa and Arjuna Retrieve a Brāhmaṇa’s Sons",
            "CHAPTER NINETY: Summary of Lord Kṛṣṇa’s Glories"
        ]
    },
    "11": {
        "title": "Canto 11: General History",
        "chapter_title": [
            "CHAPTER ONE: The Curse upon the Yadu Dynasty",
            "CHAPTER TWO: Mahārāja Nimi Meets the Nine Yogendras",
            "CHAPTER THREE: Liberation from the Illusory Energy",
            "CHAPTER FOUR: Drumila Explains the Incarnations of Godhead to King Nimi",
            "CHAPTER FIVE: Nārada Concludes His Teachings to Vasudeva",
            "CHAPTER SIX: The Yadu Dynasty Retires to Prabhāsa",
            "CHAPTER SEVEN: Lord Kṛṣṇa Instructs Uddhava",
            "CHAPTER EIGHT: The Story of Piṅgalā",
            "CHAPTER NINE: Detachment from All that Is Material",
            "CHAPTER TEN: The Nature of Fruitive Activity",
            "CHAPTER ELEVEN: The Symptoms of Conditioned and Liberated Living Entities",
            "CHAPTER TWELVE: Beyond Renunciation and Knowledge",
            "CHAPTER THIRTEEN: The Haṁsa-avatāra Answers the Questions of the Sons of Brahmā",
            "CHAPTER FOURTEEN: Lord Kṛṣṇa Explains the Yoga System to Śrī Uddhava",
            "CHAPTER FIFTEEN: Lord Kṛṣṇa’s Description of Mystic Yoga Perfections",
            "CHAPTER SIXTEEN: The Lord’s Opulence",
            "CHAPTER SEVENTEEN: Lord Kṛṣṇa’s Description of the Varṇāśrama System",
            "CHAPTER EIGHTEEN: Description of Varṇāśrama-dharma",
            "CHAPTER NINETEEN: The Perfection of Spiritual Knowledge",
            "CHAPTER TWENTY: Pure Devotional Service Surpasses Knowledge and Detachment",
            "CHAPTER TWENTY-ONE: Lord Kṛṣṇa’s Explanation of the Vedic Path",
            "CHAPTER TWENTY-TWO: Enumeration of the Elements of Material Creation",
            "CHAPTER TWENTY-THREE: The Song of the Avantī Brāhmaṇa",
            "CHAPTER TWENTY-FOUR: The Philosophy of Sāṅkhya",
            "CHAPTER TWENTY-FIVE: The Three Modes of Nature and Beyond",
            "CHAPTER TWENTY-SIX: The Aila-gītā",
            "CHAPTER TWENTY-SEVEN: Lord Kṛṣṇa’s Instructions on the Process of Deity Worship",
            "CHAPTER TWENTY-EIGHT: Jñāna-yoga",
            "CHAPTER TWENTY-NINE: Bhakti-yoga",
            "CHAPTER THIRTY: The Disappearance of the Yadu Dynasty",
            "CHAPTER THIRTY-ONE: The Disappearance of Lord Śrī Kṛṣṇa"
        ]
    },
    "12": {
        "title": "Canto 12: The Age of Deterioration",
        "chapter_title": [
            "CHAPTER ONE: The Degraded Dynasties of Kali-yuga",
            "CHAPTER TWO: The Symptoms of Kali-yuga",
            "CHAPTER THREE: The Bhūmi-gītā",
            "CHAPTER FOUR: The Four Categories of Universal Annihilation",
            "CHAPTER FIVE: Śukadeva Gosvāmī’s Final Instructions to Mahārāja Parīkṣit",
            "CHAPTER SIX: Mahārāja Parīkṣit Passes Away",
            "CHAPTER SEVEN: The Purāṇic Literatures",
            "CHAPTER EIGHT: Mārkaṇḍeya’s Prayers to Nara-Nārāyaṇa Ṛṣi",
            "CHAPTER NINE: Mārkaṇḍeya Ṛṣi Sees the Illusory Potency of the Lord",
            "CHAPTER TEN: Lord Śiva and Umā Glorify Mārkaṇḍeya Ṛṣi",
            "CHAPTER ELEVEN: Summary Description of the Mahāpuruṣa",
            "CHAPTER TWELVE: The Topics of Śrīmad-Bhāgavatam Summarized",
            "CHAPTER THIRTEEN: The Glories of Śrīmad-Bhāgavatam"
        ]
    }
}


class VedaBase(commands.Cog):
    """ Retrieve ślokas from Bhagavad Gītā, Caitanya-caritāmṛta and Śrīmad Bhāgavatam from Vedabase.io

    - Supports Devanāgarī, Sanskrit/Bengali, Synonyms and Translation
    - Supports multiple verses grouped together
    - Supports formatted word-for-word with bold-italics
    - Robust scraping for web-crawler function
    """
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://vedabase.io/en/library/"
        self.ua = UserAgent(use_cache_server=False)  # Disable caching self.ua = UserAgent()
        self.session = None
        self.last_request_time = 0
        self.request_delay = 5  # seconds between requests
        
    async def ensure_session(self):
        """Initialize session with proper headers if not exists"""
        if not self.session or self.session.closed:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://vedabase.io/',
                'DNT': '1',
                'Connection': 'keep-alive'
            }
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)

    async def scrape_with_retry(self, url, max_retries=3):
        """Robust scraping with retry logic"""
        await self.ensure_session()
        
        for attempt in range(max_retries):
            try:
                # Respect crawl delay
                elapsed = time.time() - self.last_request_time
                if elapsed < self.request_delay:
                    await asyncio.sleep(self.request_delay - elapsed)
                
                self.last_request_time = time.time()
                
                # Rotate user agent
                self.session.headers.update({'User-Agent': self.ua.random})
                
                async with self.session.get(url) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 5))
                        await asyncio.sleep(retry_after)
                        continue
                        
                    if response.status == 403:
                        raise ValueError("Access forbidden - potentially blocked")
                        
                    if response.status != 200:
                        continue
                        
                    return await response.text()
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1 + random.random())
                
        raise ValueError(f"Failed after {max_retries} attempts")

    def get_chapter_title(self, scripture: str, chapter_ref: Union[int, str]) -> str:
        """Retrieve the formatted chapter title based on scripture type"""
        if scripture == 'bg':
            if chapter_ref not in BG_CHAPTER_INFO:
                return f"Number {chapter_ref}"
            return BG_CHAPTER_INFO[chapter_ref].get('chapter_title', f"Number {chapter_ref}")
        elif scripture == 'cc':
            book = str(chapter_ref).lower()
            return CC_BOOK_INFO.get(book, {}).get('title', f"Book {book}")
        elif scripture == 'sb':
            canto = str(chapter_ref)
            return f"Canto {canto} - {SB_CANTO_INFO.get(canto, {}).get('title', 'Unknown')}"
        return f"Number {chapter_ref}"

    # +------------------------------------------------------------+
    # |                     Common Helper Methods                   |
    # +------------------------------------------------------------+
    def _get_verse_section(self, soup, class_name):
        """Helper method to extract verse sections"""
        section = soup.find('div', class_=class_name)
        if not section:
            return "Not available"
        
        if class_name == 'av-devanagari':  # Devanāgarī for SB and BG
            text_div = section.find('div', class_='text-center')
            if text_div:
                for br in text_div.find_all('br'):
                    br.replace_with('\n')
                return text_div.get_text(strip=False)
        
        elif class_name == 'av-bengali':  # Bengali for CC
            text_div = section.find('div', class_='text-center')
            if text_div:
                for br in text_div.find_all('br'):
                    br.replace_with('\n')
                return text_div.get_text(strip=False)

        elif class_name == 'av-verse_text':
            verse_parts = []
            for italic_div in section.find_all('div', class_='italic'):
                for br in italic_div.find_all('br'):
                    br.replace_with('\n')
                verse_parts.append(italic_div.get_text(strip=False))
            return '\n'.join(verse_parts)

        elif class_name == 'av-synonyms':
            text_div = section.find('div', class_='text-justify')
            if text_div:
                for a in text_div.find_all('a'):
                    if '-' in a.text:
                        parent_span = a.find_parent('span', class_='inline')
                        if parent_span:
                            hyphenated_term = '_' + a.text + '_'
                            parent_span.replace_with(hyphenated_term)
                
                for em in text_div.find_all('em'):
                    em.replace_with(f"_**{em.get_text(strip=True)}**_")
                
                text = text_div.get_text(' ', strip=True)
                text = text.replace(' - ', '-')
                text = text.replace(' ;', ';')
                text = text.replace(' .', '.')
                return text

        elif class_name == 'av-translation':
            text_div = section.find('div', class_='s-justify')
            if text_div:
                return text_div.get_text(strip=True)
        
        return "Not found: 404"

    def _split_content(self, text: str, max_len: int = 1020) -> list:
        """Smart content splitting at natural breaks"""
        if len(text) <= max_len:
            return [text]
        
        if ';' in text:
            parts = []
            current_chunk = ""
            
            for segment in text.split(';'):
                segment = segment.strip()
                if not segment:
                    continue
                    
                temp_chunk = f"{current_chunk}; {segment}" if current_chunk else segment
                if len(temp_chunk) <= max_len:
                    current_chunk = temp_chunk
                else:
                    if current_chunk:
                        parts.append(current_chunk)
                    current_chunk = segment
            
            if current_chunk:
                parts.append(current_chunk)
                
            if len(parts) > 1:
                parts = [f"{p};" for p in parts[:-1]] + [parts[-1]]
                return parts
        
        chunks = []
        while text:
            split_pos = max(
                text.rfind(';', 0, max_len),
                text.rfind(',', 0, max_len),
                text.rfind(' ', 0, max_len)
            )
            
            if split_pos <= 0:
                split_pos = max_len
                
            chunk = text[:split_pos].strip()
            chunks.append(chunk)
            text = text[split_pos:].strip()
        
        return chunks

    async def _add_field_safe(self, embed, name, value, inline=False):
        """Add field with automatic splitting if needed"""
        if not value:
            return
        
        if isinstance(value, list):
            value = ' '.join(value)
        
        chunks = self._split_content(str(value))
        embed.add_field(name=name, value=chunks[0], inline=inline)
        for chunk in chunks[1:]:
            embed.add_field(name="↳", value=chunk, inline=inline)

    # +------------------------------------------------------------+
    # |                     Input Validation                        |
    # +------------------------------------------------------------+
    def validate_bg_input(self, chapter: int, verse_input: str):
        """Validate BG chapter and verse input"""
        if chapter not in BG_CHAPTER_INFO:
            return (False, f"Invalid chapter number. The Bhagavad Gītā has 18 chapters (requested {chapter}).")
        
        chapter_data = BG_CHAPTER_INFO[chapter]
        total_verses = chapter_data['total_verses']

        if '-' in verse_input:
            try:
                start, end = sorted(map(int, verse_input.split('-')))
                if end > total_verses:
                    return (False, f"Chapter {chapter} only has {total_verses} verses.")
                
                for r_start, r_end in chapter_data['grouped_ranges']:
                    if start >= r_start and end <= r_end:
                        return (True, f"{r_start}-{r_end}")
                    if (start <= r_end and end >= r_start):
                        return (False, f"Requested verses {start}-{end} overlap with predefined grouped range {r_start}-{r_end}.")
                
                return (True, f"{start}-{end}")
            except ValueError:
                return (False, "Invalid verse range format. Use for example '20-23' or a single verse like '21'.")
        
        try:
            verse_num = int(verse_input)
            if verse_num < 1 or verse_num > total_verses:
                return (False, f"Chapter {chapter} has only {total_verses} verses.")
            
            for r_start, r_end in chapter_data['grouped_ranges']:
                if r_start <= verse_num <= r_end:
                    return (True, f"{r_start}-{r_end}")
            
            return (True, str(verse_num))
        except ValueError:
            return (False, f"Invalid verse number: {verse_input}")

    def validate_cc_input(self, book: str, chapter: int, verse_input: str):
        """Validate CC book, chapter and verse input"""
        book = book.lower()
        if book not in CC_BOOK_INFO and book not in {'1', '2', '3'}:
            return (False, "Invalid book. Use 'adi' or '1', 'madhya' or '2', 'antya' or '3'.")
        
        # Note: CC doesn't have predefined verse counts, so we'll just validate format
        if '-' in verse_input:
            try:
                start, end = sorted(map(int, verse_input.split('-')))
                if start < 1:
                    return (False, "Verse numbers must be positive.")
                return (True, f"{start}-{end}")
            except ValueError:
                return (False, "Invalid verse range format. Use for example '20-23' or a single verse like '21'.")
        
        try:
            verse_num = int(verse_input)
            if verse_num < 1:
                return (False, "Verse numbers must be positive.")
            return (True, str(verse_num))
        except ValueError:
            return (False, f"Invalid verse number: {verse_input}")

    def validate_sb_input(self, canto: str, chapter: int, verse_input: str):
        """Validate SB canto, chapter and verse input"""
        if canto not in SB_CANTO_INFO and not (canto.isdigit() and 1 <= int(canto) <= 12):
            return (False, "Invalid canto. Śrīmad Bhāgavatam has 12 cantos (1-12).")
        
        if '-' in verse_input:
            try:
                start, end = sorted(map(int, verse_input.split('-')))
                if start < 1:
                    return (False, "Verse numbers must be positive.")
                return (True, f"{start}-{end}")
            except ValueError:
                return (False, "Invalid verse range format. Use for example '20-23' or a single verse like '21'.")
        
        try:
            verse_num = int(verse_input)
            if verse_num < 1:
                return (False, "Verse numbers must be positive.")
            return (True, str(verse_num))
        except ValueError:
            return (False, f"Invalid verse number: {verse_input}")

    # +------------------------------------------------------------+
    # |                     Bhagavad Gītā Command                   |
    # +------------------------------------------------------------+
    @commands.command(aliases=['gita', 'bhagavad_gita', 'bhagavad-gita'], no_pm=True)
    async def bhagavadgita(self, ctx, chapter: int, verse: str):
        """Retrieve a Bhagavad Gītā śloka from Vedabase.io"""
        is_valid, validated_verse_or_error = self.validate_bg_input(chapter, verse)
        if not is_valid:
            return await ctx.send(validated_verse_or_error)
        
        verse = validated_verse_or_error
        url = f"{self.base_url}bg/{chapter}/{verse}/"
        
        try:
            html = await self.scrape_with_retry(url)
            soup = BeautifulSoup(html, 'html.parser')
            chapter_title = self.get_chapter_title('bg', chapter)

            devanagari = self._get_verse_section(soup, 'av-devanagari')
            verse_text = self._get_verse_section(soup, 'av-verse_text')
            synonyms = self._get_verse_section(soup, 'av-synonyms')
            translation = self._get_verse_section(soup, 'av-translation')

            distance = self.bot or self.bot.message
            duration = f'Śloka retrieved in {distance.ws.latency * 1000:.2f} ms'
            
            embed = discord.Embed(
                colour=discord.Colour(0x50e3c2),
                url=url,
                description=f"**{chapter_title}**"
            )
            embed.set_footer(text=duration)
            embed.set_author(name=f"Bhagavad Gītā ⁿᵉʷ — Śloka [ {chapter}.{verse} ]", url=url, icon_url="https://imgur.com/Yx661rW.png")

            await self._add_field_safe(embed, "देवनागरी:", devanagari)
            await self._add_field_safe(embed, f"TEXT {verse}:", f"**```py\n{verse_text}\n```**")
            await self._add_field_safe(embed, "SYNONYMS:", synonyms)
            await self._add_field_safe(embed, "TRANSLATION:", f"> **{translation}**")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"🚫 Error retrieving verse: \n{str(e)}")
            if hasattr(self.bot, 'logger'):
                self.bot.logger.error(f"BG command failed: \n\n{e}", exc_info=True)

    # +------------------------------------------------------------+
    # |                 Caitanya-caritāmṛta Command                 |
    # +------------------------------------------------------------+
    @commands.command(aliases=['cc', 'caritamrta', 'caitanya-caritamrta'], no_pm=True)
    async def caitanyacaritamrta(self, ctx, book: str, chapter: int, verse: str):
        """Retrieve a Caitanya-caritāmṛta śloka from Vedabase.io"""
        is_valid, validated_verse_or_error = self.validate_cc_input(book, chapter, verse)
        if not is_valid:
            return await ctx.send(validated_verse_or_error)
        
        # Normalize book name (convert '1' to 'adi', etc.)
        book = book.lower()
        if book in {'1', '2', '3'}:
            book = {v['num']: k for k, v in CC_BOOK_INFO.items() if 'num' in v}.get(int(book), book)
        
        verse = validated_verse_or_error
        url = f"{self.base_url}cc/{book}/{chapter}/{verse}/"
        
        try:
            html = await self.scrape_with_retry(url)
            soup = BeautifulSoup(html, 'html.parser')
            book_title = self.get_chapter_title('cc', book)

            bengali = self._get_verse_section(soup, 'av-bengali')
            verse_text = self._get_verse_section(soup, 'av-verse_text')
            synonyms = self._get_verse_section(soup, 'av-synonyms')
            translation = self._get_verse_section(soup, 'av-translation')

            distance = self.bot or self.bot.message
            duration = f'Śloka retrieved in {distance.ws.latency * 1000:.2f} ms'
            
            embed = discord.Embed(
                colour=discord.Colour(0x3b88c3),  # Different color for CC
                url=url,
                description=f"**{book_title} - Chapter {chapter}**"
            )
            embed.set_footer(text=duration)
            embed.set_author(name=f"Caitanya-caritāmṛta — Śloka [ {book}.{chapter}.{verse} ]", url=url, icon_url="https://imgur.com/Yx661rW.png")

            await self._add_field_safe(embed, "देवनागरी/বাংলা:", bengali)
            await self._add_field_safe(embed, f"TEXT {verse}:", f"**```py\n{verse_text}\n```**")
            await self._add_field_safe(embed, "SYNONYMS:", synonyms)
            await self._add_field_safe(embed, "TRANSLATION:", f"> **{translation}**")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"🚫 Error retrieving verse: \n{str(e)}")
            if hasattr(self.bot, 'logger'):
                self.bot.logger.error(f"CC command failed: \n\n{e}", exc_info=True)

    # +------------------------------------------------------------+
    # |                 Śrīmad Bhāgavatam Command                  |
    # +------------------------------------------------------------+
    @commands.command(aliases=['sb', 'bhagavatam', 'srimad-bhagavatam'], no_pm=True)
    async def srimadbhagavatam(self, ctx, canto: str, chapter: int, verse: str):
        """Retrieve a Śrīmad Bhāgavatam śloka from Vedabase.io"""
        is_valid, validated_verse_or_error = self.validate_sb_input(canto, chapter, verse)
        if not is_valid:
            return await ctx.send(validated_verse_or_error)
        
        verse = validated_verse_or_error
        url = f"{self.base_url}sb/{canto}/{chapter}/{verse}/"
        
        try:
            html = await self.scrape_with_retry(url)
            soup = BeautifulSoup(html, 'html.parser')
            canto_title = self.get_chapter_title('sb', canto)

            devanagari = self._get_verse_section(soup, 'av-devanagari')
            verse_text = self._get_verse_section(soup, 'av-verse_text')
            synonyms = self._get_verse_section(soup, 'av-synonyms')
            translation = self._get_verse_section(soup, 'av-translation')

            distance = self.bot or self.bot.message
            duration = f'Śloka retrieved in {distance.ws.latency * 1000:.2f} ms'
            
            embed = discord.Embed(
                colour=discord.Colour(0x9b59b6),  # Different color for SB
                url=url,
                description=f"**{canto_title} - Chapter {chapter}**"
            )
            embed.set_footer(text=duration)
            embed.set_author(name=f"Śrīmad Bhāgavatam — Śloka [ {canto}.{chapter}.{verse} ]", url=url, icon_url="https://imgur.com/Yx661rW.png")

            await self._add_field_safe(embed, "देवनागरी:", devanagari)
            await self._add_field_safe(embed, f"TEXT {verse}:", f"**```py\n{verse_text}\n```**")
            await self._add_field_safe(embed, "SYNONYMS:", synonyms)
            await self._add_field_safe(embed, "TRANSLATION:", f"> **{translation}**")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"🚫 Error retrieving verse: \n{str(e)}")
            if hasattr(self.bot, 'logger'):
                self.bot.logger.error(f"SB command failed: \n\n{e}", exc_info=True)

    def cog_unload(self):
        if hasattr(self, 'ua'):
            self.ua = None  # Helps with garbage collection
        if self.session:
            self.bot.loop.create_task(self.session.close())

async def setup(bot):
    await bot.add_cog(VedaBase(bot))
