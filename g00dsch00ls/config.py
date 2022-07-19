# School properties
# -----------------

SUBJECTS = ['historia', 'j\u0119zyk angielski', 'j\u0119zyk polski', 'matematyka', 'historiawos', 'biologia', 'geografia', 'biologiageografia', 'informatyka', 'chemia', 'biologiachemia', 'fizyka', 'wos', 'j\u0119zyk ?aci?ski', 'j\u0119zyk obcy', 'geografiawos', 'historia sztuki', 'j\u0119zyk niemiecki', 'chemiageografia', 'geografiahistoria', 'j?zyk angielskij?zyk hiszpa?skij?zyk niemiecki', 'j?zyk hiszpa?ski', 'j?zyk w?oski', 'j?zyk francuskij?zyk hiszpa?skij?zyk niemieckij?zyk rosyjskij?zyk w?oski', 'historiaj?zyk obcyplastykawos', 'biologiahistoriaj?zyk obcywos', 'biologiachemiaj?zyk obcy', 'biologiageografiaj?zyk obcywf', 'geografiaj?zyk obcywos', 'chemiafizykainformatykaj?zyk obcy', 'biologiahistoriawos', 'geografiainformatykawos', 'biologiachemiaj?zyk angielski', 'geografiaj?zyk obcy', 'j?zyk angielskiwos', 'fizykainformatyka', 'j?zyk francuski', 'geografiaj?zyk angielski', 'historiaj?zyk angielskiwos', 'j?zyk angielskij?zyk niemiecki', 'geografiainformatyka', 'biologiageografiaj?zyk angielski', 'wf', 'j?zyk angielskij?zyk hiszpa?skij?zyk niemieckiwos', 'biologiafizyka', 'technika', 'biologiachemiaedukacja dla bezpiecze?stwafizykageografiahistoriainformatykaj?zyk obcymuzykaplastykaprzyrodatechnikawfwos', 'plastyka', '', 'j', 'geografiainformatykaj?zyk niemiecki', 'biologiaj?zyk angielskij?zyk francuski', 'geografiainformatykamuzyka']
SCHOOL_TYPES = {
    "liceum / publiczna": 0,
    "liceum / niepubliczna": 0,
    "technikum / publiczna": 1,
    "technikum / niepubliczna": 1,
    "bran?owa szko?a i stopnia / publiczna": 2,
    "bran\u017cowa szko\u0142a i stopnia / publiczna": 2
}
MIN_SCHOOL_TYPE = min(SCHOOL_TYPES.values())
MAX_SCHOOL_TYPE = max(SCHOOL_TYPES.values())

MIN_GRADE = 1
MAX_GRADE = 6
POINTS_FOR_GRADES = (0, 0, 2, 8, 14, 17, 18)
POLISH_EXAM_WEIGHT = .35
MATH_EXAM_WEIGHT = .35
ENGLISH_EXAM_WEIGHT = .30
DIPLOMA_HONORS_POINTS = 7
DIPLOMA_HONORS_GPA = 4.75
MIN_POINTS = 0
MAX_POINTS = 200
