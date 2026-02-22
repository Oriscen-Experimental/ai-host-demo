from app.models import TaskCard, CardMode, OutputType

TASK_CARDS: dict[str, TaskCard] = {}

def _register(card: TaskCard):
    TASK_CARDS[card.id] = card

_register(TaskCard(
    id="CARD_01",
    title="Low-Barrier City Joy Map",
    duration_min=20,
    mode=CardMode.WHOLE_GROUP,
    goal='Create a shared "Low-Barrier City Joy List" for the group',
    steps=[
        "Each person writes 2 spots: coffee/walks/cheap eats/quiet corners (anything)",
        'Add one sentence: "Why it suits me/who it suits"',
        "Compile into a list",
    ],
    output=OutputType.LIST,
    agent_script="This isn't a guide competition, lighter is better.",
    fallback="Don't know a spot? Just write 'nearest highest-rated coffee shop to my home'.",
    tags=["low_risk", "week1"],
    safety_notes="Avoid judgment and comparison",
))

_register(TaskCard(
    id="CARD_02",
    title="Pair Interview + Three-Sentence Summary",
    duration_min=15,
    mode=CardMode.PAIRS,
    goal='Quickly create a sense of "being understood"',
    steps=[
        "A speaks for 2 minutes: life state you want recently",
        "B writes 3 sentences (facts mainly)",
        "Switch roles",
    ],
    output=OutputType.TEXT,
    agent_script="Summary should only contain facts, not evaluations.",
    fallback="Use template: 'You are currently...; You care about...; You hope...'",
    tags=["low_risk", "week1"],
    safety_notes="Don't dig into privacy",
))

_register(TaskCard(
    id="CARD_03",
    title="60-Second Group Podcast",
    duration_min=15,
    mode=CardMode.TRIOS,
    goal="Create a 60-second audio clip, building shared output",
    steps=[
        "Choose topic: a small discovery this week",
        "Write 4-sentence script (1 per person + intro/outro)",
        "Record (within group)",
    ],
    output=OutputType.AUDIO,
    agent_script="Reading from script is fine, camera off is fine.",
    fallback="No recording? Just submit the script.",
    tags=["medium_risk", "creative"],
    safety_notes="No humiliating feedback",
))

_register(TaskCard(
    id="CARD_04",
    title="Micro-Problem Solution Sprint",
    duration_min=20,
    mode=CardMode.TRIOS,
    goal="Each person gets 2 actionable suggestions",
    steps=[
        "Each person: 60 seconds describing a micro-problem",
        'Group members only give "next step + 5-minute minimum action"',
        "Record",
    ],
    output=OutputType.LIST,
    agent_script="No big lessons, just next steps.",
    fallback="Problem must be small enough to 'make progress this week'.",
    tags=["medium_risk", "practical"],
    safety_notes="No psychological diagnosis",
))

_register(TaskCard(
    id="CARD_05",
    title="Three-Person Accountability: One Small Action This Week",
    duration_min=15,
    mode=CardMode.TRIOS,
    goal="Form a commitment that can happen within the week",
    steps=[
        "Each person picks a small action (≤10 min prep)",
        "Choose reminder type (light/none/weekend)",
        "Write a one-sentence commitment announcement",
    ],
    output=OutputType.TEXT,
    agent_script="Action should be ridiculously small, the point is it happens.",
    fallback="Low energy? 'I'll just send one photo' is allowed.",
    tags=["commitment", "week1"],
    safety_notes="No judging failure",
))

_register(TaskCard(
    id="CARD_06",
    title="Teach a 3-Minute Micro-Skill",
    duration_min=20,
    mode=CardMode.WHOLE_GROUP,
    goal="Everyone gets to contribute",
    steps=[
        "Each person teaches a 3-minute micro-skill",
        "Others ask only 1 specific question",
    ],
    output=OutputType.LIST,
    agent_script="Smaller skills are better: shortcuts, cooking, organizing all count.",
    fallback="Can't think of one? Teach 'a small tool/habit you use often'.",
    tags=["low_risk", "fun"],
    safety_notes="Avoid comparison",
))

_register(TaskCard(
    id="CARD_07",
    title="Letter to Future Self (Share One Line Only)",
    duration_min=10,
    mode=CardMode.WHOLE_GROUP,
    goal="Light vulnerability with control",
    steps=[
        "Write privately for 3 minutes",
        "Voluntarily share one excerpt",
    ],
    output=OutputType.TEXT,
    agent_script="Only share what you're willing to share.",
    fallback="Can share a general sentence without private details.",
    tags=["medium_risk", "reflective"],
    safety_notes="No follow-up questions",
))

_register(TaskCard(
    id="CARD_08",
    title="2-Hour Micro Adventure Template",
    duration_min=35,
    mode=CardMode.TRIOS,
    goal="Each person produces a 2-hour plan that can happen within a week",
    steps=[
        "Fill 5 items: time/location/budget/companion role/invitation script",
        "Three people help shrink each plan",
        "Display on output wall",
    ],
    output=OutputType.FORM,
    agent_script="Focus on making it smaller, more specific, less awkward.",
    fallback="Location can be vague; script can be auto-generated draft.",
    tags=["main_task", "week1"],
    safety_notes="Don't force offline meetups",
))

_register(TaskCard(
    id="CARD_09",
    title="Friend-Style Introduction",
    duration_min=15,
    mode=CardMode.PAIRS,
    goal='Help each other form "identity expression you can take outside the Pod"',
    steps=[
        'Write one sentence: "I want to be introduced as..."',
        "Partner rephrases and removes exaggerations",
    ],
    output=OutputType.TEXT,
    agent_script="Life identity first, no professional packaging.",
    fallback="Template: 'I'm someone who likes..., recently doing...'",
    tags=["low_risk", "identity"],
    safety_notes="Avoid transactional networking",
))

_register(TaskCard(
    id="CARD_10",
    title="Mood Weather Report + Support Type",
    duration_min=8,
    mode=CardMode.WHOLE_GROUP,
    goal="Quickly align group energy, reduce misunderstandings",
    steps=[
        "Round robin: energy 1-5",
        "Support type: listen/advice/do together/relax",
    ],
    output=OutputType.NONE,
    agent_script="20 seconds each, I'll keep time.",
    fallback="Just say a number + one word.",
    tags=["opening", "low_risk", "week1"],
    safety_notes="Don't dig into reasons",
))

_register(TaskCard(
    id="CARD_11",
    title="Shared Resource Pack",
    duration_min=15,
    mode=CardMode.PAIRS,
    goal='Anchor the relationship to "useful"',
    steps=[
        "Choose topic: coffee shops/walks/productivity tools/food",
        "Each person contributes 3 items",
        "Merge into one list",
    ],
    output=OutputType.LIST,
    agent_script="Not comprehensive, just usable.",
    fallback="Don't know? Write 'I heard.../I want to try...'",
    tags=["low_risk", "practical"],
    safety_notes="No comparison",
))

_register(TaskCard(
    id="CARD_12",
    title="7-Day Micro Challenge",
    duration_min=10,
    mode=CardMode.WHOLE_GROUP,
    goal="Give next week something to look forward to",
    steps=[
        "Each person picks a micro-challenge (≤5 min/day)",
        "Agree on one-sentence review next time",
    ],
    output=OutputType.TEXT,
    agent_script="Failure is welcome to share.",
    fallback="Challenge options: walk 5 min daily/drink water/one English sentence.",
    tags=["commitment", "fun"],
    safety_notes="No shaming failure",
))

_register(TaskCard(
    id="CARD_13",
    title="Optional Light Offline Meetup Planning",
    duration_min=15,
    mode=CardMode.WHOLE_GROUP,
    goal="Bring online relationships offline (voluntary)",
    steps=[
        "Propose 2 candidate times/locations",
        "Clarify exit mechanism (no explanation needed to skip)",
    ],
    output=OutputType.TEXT,
    agent_script="Completely voluntary, no reason needed to skip.",
    fallback="Can change to online: co-reading/virtual walk.",
    tags=["medium_risk", "offline"],
    safety_notes="No pressure",
))

_register(TaskCard(
    id="CARD_14",
    title="Exchange Small Habits + Do Minimum Version",
    duration_min=15,
    mode=CardMode.PAIRS,
    goal="Low-cost ongoing mutual support",
    steps=[
        "Exchange a small habit you want to maintain",
        "Shrink it to ≤2 minute version",
    ],
    output=OutputType.TEXT,
    agent_script="Smaller = more likely to happen.",
    fallback="Template: 'Trigger __ → Action __ (2 min)'",
    tags=["low_risk", "habit"],
    safety_notes="Avoid discipline shaming",
))

_register(TaskCard(
    id="CARD_15",
    title="Three-Person 5-Minute Adult-Friendly Puzzle/Game",
    duration_min=10,
    mode=CardMode.TRIOS,
    goal="Quick shared experience, break awkwardness",
    steps=[
        "Give a light puzzle/creative prompt",
        "5 minutes to complete together",
    ],
    output=OutputType.NONE,
    agent_script="This is stress relief, not a smart competition.",
    fallback="Don't want to play? Change to 'three people write a 3-sentence story together'.",
    tags=["rescue", "fun", "low_risk"],
    safety_notes="No mocking",
))

_register(TaskCard(
    id="CARD_16",
    title="What I'm Learning Recently + Two Curious Questions",
    duration_min=15,
    mode=CardMode.WHOLE_GROUP,
    goal="Leave hooks for future conversations",
    steps=[
        "Each person: 60 seconds sharing",
        "Two specific curious questions",
    ],
    output=OutputType.LIST,
    agent_script="Time-limited, questions must be specific.",
    fallback="Don't know how to ask? Template: 'How did you start? What's next?'",
    tags=["low_risk", "curiosity"],
    safety_notes="Avoid judgment",
))

_register(TaskCard(
    id="CARD_17",
    title="Paraphrase Practice",
    duration_min=12,
    mode=CardMode.PAIRS,
    goal="Low-risk understanding building",
    steps=[
        "60 seconds expression",
        "20 seconds paraphrase",
        "Correct only 1 point",
    ],
    output=OutputType.NONE,
    agent_script="Before paraphrasing, say: 'I might have misunderstood...'",
    fallback="Just keywords is fine.",
    tags=["micro_task", "low_risk", "week1"],
    safety_notes="No follow-up questions",
))

_register(TaskCard(
    id="CARD_18",
    title="Mutual Help Request Wall",
    duration_min=10,
    mode=CardMode.WHOLE_GROUP,
    goal="Institutionalize reciprocity",
    steps=[
        "Each person writes one small request (progress-able in ≤30 min)",
        "Each person gives one response (next step + 5-min action)",
    ],
    output=OutputType.LIST,
    agent_script="Requests should be small, responses should be specific.",
    fallback="Don't know how to write? Template: 'I'm stuck on __, I want __'.",
    tags=["mutual_help", "week1"],
    safety_notes="No medical/legal advice",
))

_register(TaskCard(
    id="CARD_19",
    title="Group Code Word/Ritual",
    duration_min=8,
    mode=CardMode.WHOLE_GROUP,
    goal='Legitimize future "low energy/spectating"',
    steps=[
        "Choose a code word (e.g.: yellow = I'm just watching today)",
        "Agree on how to respond",
    ],
    output=OutputType.TEXT,
    agent_script="Ritual should be functional, not awkward.",
    fallback="Default: yellow=spectate, green=advice, blue=do together.",
    tags=["ritual", "fun"],
    safety_notes="Respect boundaries",
))

_register(TaskCard(
    id="CARD_20",
    title="10 Small Things We Learned",
    duration_min=20,
    mode=CardMode.WHOLE_GROUP,
    goal="Solidify shared memory",
    steps=[
        "Each person contributes 1-2 items",
        "Must point to specific person/moment",
    ],
    output=OutputType.LIST,
    agent_script="No big lessons, just specific moments.",
    fallback="Template: 'I remember __ said __, which made me __'",
    tags=["closing", "reflective"],
    safety_notes="Don't force sharing",
))

# Default card picks for a session
DEFAULT_SESSION_CARDS = {
    "opening": "CARD_10",
    "micro": "CARD_17",
    "main": "CARD_08",
    "help": "CARD_18",
    "commit": "CARD_05",
    "rescue": "CARD_15",
}
