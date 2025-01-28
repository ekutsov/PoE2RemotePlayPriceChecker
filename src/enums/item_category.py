from enum import Enum
from typing import List, Dict, Optional, Union

class ItemCategory(Enum):
    Map = "Map"
    CapturedBeast = "Captured Beast"
    MetamorphSample = "Metamorph Sample"
    Helmet = "Helmet"
    BodyArmour = "Body Armour"
    Gloves = "Gloves"
    Boots = "Boots"
    Shield = "Shield"
    Amulet = "Amulet"
    Belt = "Belt"
    Ring = "Ring"
    Flask = "Flask"
    AbyssJewel = "Abyss Jewel"
    Jewel = "Jewel"
    Quiver = "Quiver"
    Claw = "Claw"
    Bow = "Bow"
    Sceptre = "Sceptre"
    Wand = "Wand"
    FishingRod = "Fishing Rod"
    Staff = "Staff"
    Warstaff = "Warstaff"
    Dagger = "Dagger"
    RuneDagger = "Rune Dagger"
    OneHandedAxe = "One-Handed Axe"
    TwoHandedAxe = "Two-Handed Axe"
    OneHandedMace = "One-Handed Mace"
    TwoHandedMace = "Two-Handed Mace"
    OneHandedSword = "One-Handed Sword"
    TwoHandedSword = "Two-Handed Sword"
    ClusterJewel = "Cluster Jewel"
    HeistBlueprint = "Heist Blueprint"
    HeistContract = "Heist Contract"
    HeistTool = "Heist Tool"
    HeistBrooch = "Heist Brooch"
    HeistGear = "Heist Gear"
    HeistCloak = "Heist Cloak"
    Trinket = "Trinket"
    Invitation = "Invitation"
    Gem = "Gem"
    Currency = "Currency"
    DivinationCard = "Divination Card"
    Voidstone = "Voidstone"
    Sentinel = "Sentinel"
    MemoryLine = "Memory Line"
    SanctumRelic = "Sanctum Relic"
    Tincture = "Tincture"
    Charm = "Charm"
    Crossbow = "Crossbow"
    SkillGem = "Skill Gem"
    SupportGem = "Support Gem"
    MetaGem = "Meta Gem"
    Focus = "Focus"

class StatBetter(Enum):
    NegativeRoll = -1
    PositiveRoll = 1
    NotComparable = 0

class StatMatcher:
    def __init__(self, string: str, advanced: Optional[str] = None, negate: Optional[bool] = None, value: Optional[int] = None, oils: Optional[str] = None):
        self.string = string
        self.advanced = advanced
        self.negate = negate
        self.value = value
        self.oils = oils

class Stat:
    def __init__(self, ref: str, dp: Optional[bool] = None, matchers: List[StatMatcher] = None, better: StatBetter = StatBetter.NotComparable, from_area_mods: Optional[bool] = None, from_uber_area_mods: Optional[bool] = None, from_heist_area_mods: Optional[bool] = None, anointments: Optional[List[Dict[str, Union[int, str]]]] = None, trade: Optional[Dict[str, Union[bool, Dict[str, List[str]]]]] = None):
        self.ref = ref
        self.dp = dp
        self.matchers = matchers if matchers else []
        self.better = better
        self.from_area_mods = from_area_mods
        self.from_uber_area_mods = from_uber_area_mods
        self.from_heist_area_mods = from_heist_area_mods
        self.anointments = anointments if anointments else []
        self.trade = trade if trade else {}

class DropEntry:
    def __init__(self, query: List[str], items: List[str]):
        self.query = query
        self.items = items

class BaseType:
    def __init__(self, name: str, ref_name: str, namespace: str, icon: str, w: Optional[int] = None, h: Optional[int] = None, trade_tag: Optional[str] = None, trade_disc: Optional[str] = None, disc: Optional[Dict[str, Union[bool, Dict[str, str], str]]] = None, craftable: Optional[Dict[str, Union[str, bool]]] = None, unique: Optional[Dict[str, Union[str, List[str]]]] = None, map: Optional[Dict[str, str]] = None, gem: Optional[Dict[str, Union[bool, str]]] = None, armour: Optional[Dict[str, List[int]]] = None):
        self.name = name
        self.ref_name = ref_name
        self.namespace = namespace
        self.icon = icon
        self.w = w
        self.h = h
        self.trade_tag = trade_tag
        self.trade_disc = trade_disc
        self.disc = disc if disc else {}
        self.craftable = craftable if craftable else {}
        self.unique = unique if unique else {}
        self.map = map if map else {}
        self.gem = gem if gem else {}
        self.armour = armour if armour else {}