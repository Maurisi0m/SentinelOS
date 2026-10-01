# SentinelOS Skills Registry
from .klipper import KlipperSkill
from .voice import VoiceSkill
from .netsec import NetSecSkill
from .mesh import MeshSkill

AVAILABLE_SKILLS = [
    KlipperSkill,
    VoiceSkill,
    NetSecSkill,
    MeshSkill
]
