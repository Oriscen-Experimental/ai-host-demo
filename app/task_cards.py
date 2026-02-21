from app.models import TaskCard, CardMode, OutputType

TASK_CARDS: dict[str, TaskCard] = {}

def _register(card: TaskCard):
    TASK_CARDS[card.id] = card

_register(TaskCard(
    id="CARD_01",
    title="城市低门槛快乐地图",
    duration_min=20,
    mode=CardMode.WHOLE_GROUP,
    goal='产出一份组内共享「城市低门槛快乐清单」',
    steps=[
        "每人写 2 个点：咖啡/散步/便宜好饭/安静角落（任意）",
        '每个点补一句「为什么适合我/适合谁」',
        "汇总成清单",
    ],
    output=OutputType.LIST,
    agent_script="这不是攻略比赛，越轻越好。",
    fallback="不知道地点就写'离我家最近评分最高的咖啡店'。",
    tags=["low_risk", "week1"],
    safety_notes="避免评判与攀比",
))

_register(TaskCard(
    id="CARD_02",
    title="两两互访 + 三句人设摘要",
    duration_min=15,
    mode=CardMode.PAIRS,
    goal='快速产生「被理解感」',
    steps=[
        "A 讲 2 分钟：最近想要的生活状态",
        "B 写 3 句摘要（事实为主）",
        "交换角色",
    ],
    output=OutputType.TEXT,
    agent_script="摘要只写事实，不写评价。",
    fallback="可以用模板：'你现在在…；你在乎…；你希望…'",
    tags=["low_risk", "week1"],
    safety_notes="不深挖隐私",
))

_register(TaskCard(
    id="CARD_03",
    title="60 秒共同播客",
    duration_min=15,
    mode=CardMode.TRIOS,
    goal="产出一段 60 秒音频，建立共同产物",
    steps=[
        "选主题：本周一个小发现",
        "写 4 句脚本（每人 1 句 + 开头结尾）",
        "录音（组内）",
    ],
    output=OutputType.AUDIO,
    agent_script="可读稿，可不开镜头。",
    fallback="不录音也可：只交脚本。",
    tags=["medium_risk", "creative"],
    safety_notes="禁止羞辱式点评",
))

_register(TaskCard(
    id="CARD_04",
    title="微难题方案冲刺",
    duration_min=20,
    mode=CardMode.TRIOS,
    goal="每人获得 2 条可执行建议",
    steps=[
        "每人 60 秒描述一个微难题",
        '组员只给「下一步 + 5分钟最小动作」',
        "记录",
    ],
    output=OutputType.LIST,
    agent_script="不讲大道理，只讲下一步。",
    fallback="难题必须缩小到'本周能推进一点'。",
    tags=["medium_risk", "practical"],
    safety_notes="不做心理诊断",
))

_register(TaskCard(
    id="CARD_05",
    title="三人共担保：本周一个小行动",
    duration_min=15,
    mode=CardMode.TRIOS,
    goal="形成周内可发生的承诺",
    steps=[
        "每人选一个≤10分钟准备的小行动",
        "选择提醒方式（轻提醒/不提醒/周末提醒）",
        "写成一句承诺公告",
    ],
    output=OutputType.TEXT,
    agent_script="行动要小到离谱，重点是发生。",
    fallback="如果能量低，允许'我只发一张照片'。",
    tags=["commitment", "week1"],
    safety_notes="不审判失败",
))

_register(TaskCard(
    id="CARD_06",
    title="互教 3 分钟小技能",
    duration_min=20,
    mode=CardMode.WHOLE_GROUP,
    goal="每个人都有贡献位",
    steps=[
        "每人教一个 3 分钟小技能",
        "其他人只问 1 个具体问题",
    ],
    output=OutputType.LIST,
    agent_script="技能越小越好：快捷键、做饭、整理都算。",
    fallback="想不到就教'一个你常用的小工具/小习惯'。",
    tags=["low_risk", "fun"],
    safety_notes="避免比较",
))

_register(TaskCard(
    id="CARD_07",
    title="给未来自己的信（只分享一句）",
    duration_min=10,
    mode=CardMode.WHOLE_GROUP,
    goal="轻脆弱但可控",
    steps=[
        "私下写 3 分钟",
        "自愿分享一句摘录",
    ],
    output=OutputType.TEXT,
    agent_script="只分享你愿意分享的部分。",
    fallback="可以分享泛化句，不含隐私。",
    tags=["medium_risk", "reflective"],
    safety_notes="禁止追问",
))

_register(TaskCard(
    id="CARD_08",
    title="2 小时微冒险模板",
    duration_min=35,
    mode=CardMode.TRIOS,
    goal="每人产出一个一周内可发生的 2 小时计划",
    steps=[
        "填 5 项：时间/地点/预算/同伴角色/邀请话术",
        "三人互相把计划缩小",
        "产出墙展示",
    ],
    output=OutputType.FORM,
    agent_script="重点是变小、变具体、变不尬。",
    fallback="地点可以模糊；话术可一键生成草稿。",
    tags=["main_task", "week1"],
    safety_notes="不强迫线下",
))

_register(TaskCard(
    id="CARD_09",
    title="朋友版引荐",
    duration_min=15,
    mode=CardMode.PAIRS,
    goal='帮彼此形成「可带出 Pod 的身份表达」',
    steps=[
        '写一句「我希望被介绍成...」',
        "对方复述并删掉夸张部分",
    ],
    output=OutputType.TEXT,
    agent_script="生活身份优先，不做职业包装。",
    fallback="模板：'我是一个喜欢…的人，最近在…'",
    tags=["low_risk", "identity"],
    safety_notes="避免功利社交",
))

_register(TaskCard(
    id="CARD_10",
    title="情绪天气预报 + 支持类型",
    duration_min=8,
    mode=CardMode.WHOLE_GROUP,
    goal="快速对齐群体能量，降低误解",
    steps=[
        "轮转：能量 1–5",
        "支持类型：倾听/建议/一起做事/轻松一下",
    ],
    output=OutputType.NONE,
    agent_script="每人 20 秒，我会控时。",
    fallback="可以只说数字+一个词。",
    tags=["opening", "low_risk", "week1"],
    safety_notes="不深挖原因",
))

_register(TaskCard(
    id="CARD_11",
    title="共同整理资源包",
    duration_min=15,
    mode=CardMode.PAIRS,
    goal='让关系锚到「有用」',
    steps=[
        "选主题：咖啡店/散步/效率工具/吃饭",
        "每人贡献 3 条",
        "合并成一张清单",
    ],
    output=OutputType.LIST,
    agent_script="不求全，求可用。",
    fallback="不知道就写'我听说…/我想试…'",
    tags=["low_risk", "practical"],
    safety_notes="不比较",
))

_register(TaskCard(
    id="CARD_12",
    title="7 天微挑战",
    duration_min=10,
    mode=CardMode.WHOLE_GROUP,
    goal="让下周有期待",
    steps=[
        "每人选一个微挑战（≤5分钟/天）",
        "约定下次复盘一句话",
    ],
    output=OutputType.TEXT,
    agent_script="失败也欢迎分享。",
    fallback="挑战可选：每天走5分钟/喝水/一句英语。",
    tags=["commitment", "fun"],
    safety_notes="不羞辱失败",
))

_register(TaskCard(
    id="CARD_13",
    title="可选线下轻见面策划",
    duration_min=15,
    mode=CardMode.WHOLE_GROUP,
    goal="把线上关系落地（自愿）",
    steps=[
        "提 2 个候选时间地点",
        "明确退出机制（不参加不解释）",
    ],
    output=OutputType.TEXT,
    agent_script="完全自愿，不参加不需要理由。",
    fallback="可改线上：共读/云散步。",
    tags=["medium_risk", "offline"],
    safety_notes="不施压",
))

_register(TaskCard(
    id="CARD_14",
    title="交换小习惯并做最小版本",
    duration_min=15,
    mode=CardMode.PAIRS,
    goal="低成本持续互助",
    steps=[
        "交换一个想坚持的小习惯",
        "把它缩小到≤2分钟版本",
    ],
    output=OutputType.TEXT,
    agent_script="越小越容易发生。",
    fallback="模板：'触发点__ → 动作__（2分钟）'",
    tags=["low_risk", "habit"],
    safety_notes="避免自律羞耻",
))

_register(TaskCard(
    id="CARD_15",
    title="三人 5 分钟成人友好谜题/小游戏",
    duration_min=10,
    mode=CardMode.TRIOS,
    goal="快速共同体验，解尴尬",
    steps=[
        "给一个轻谜题/创意题",
        "5分钟一起完成",
    ],
    output=OutputType.NONE,
    agent_script="这是解压，不是比聪明。",
    fallback="如果不想玩：改成'三人共同写一个三句小故事'。",
    tags=["rescue", "fun", "low_risk"],
    safety_notes="避免嘲笑",
))

_register(TaskCard(
    id="CARD_16",
    title="我最近在学的东西 + 两个好奇问题",
    duration_min=15,
    mode=CardMode.WHOLE_GROUP,
    goal="留下未来对话钩子",
    steps=[
        "每人 60 秒分享",
        "两个具体好奇问题",
    ],
    output=OutputType.LIST,
    agent_script="限时，问题必须具体。",
    fallback="不会提问就用模板：'你怎么开始的？下一步是什么？'",
    tags=["low_risk", "curiosity"],
    safety_notes="避免评判",
))

_register(TaskCard(
    id="CARD_17",
    title="复述练习",
    duration_min=12,
    mode=CardMode.PAIRS,
    goal="低风险建立理解",
    steps=[
        "60秒表达",
        "20秒复述",
        "只纠正1点",
    ],
    output=OutputType.NONE,
    agent_script="复述前先说：'我可能理解错了…'",
    fallback="只说关键词也可以。",
    tags=["micro_task", "low_risk", "week1"],
    safety_notes="不追问",
))

_register(TaskCard(
    id="CARD_18",
    title="互助请求墙",
    duration_min=10,
    mode=CardMode.WHOLE_GROUP,
    goal="把互惠制度化",
    steps=[
        "每人写一个小请求（≤30分钟能推进）",
        "每人给一个回应（下一步+5分钟动作）",
    ],
    output=OutputType.LIST,
    agent_script="请求要小、回应要具体。",
    fallback="不会写请求就用模板：'我卡在__，想要__'。",
    tags=["mutual_help", "week1"],
    safety_notes="不做医疗/法律建议",
))

_register(TaskCard(
    id="CARD_19",
    title="小组暗号/仪式",
    duration_min=8,
    mode=CardMode.WHOLE_GROUP,
    goal='给未来「低能量/旁听」合法化',
    steps=[
        "选一个暗号（例：🟡=我今天只旁听）",
        "约定如何响应",
    ],
    output=OutputType.TEXT,
    agent_script="仪式要功能化，不要尬。",
    fallback="默认：🟡旁听，🟢建议，🔵一起做事。",
    tags=["ritual", "fun"],
    safety_notes="尊重边界",
))

_register(TaskCard(
    id="CARD_20",
    title="我们学到的 10 件小事",
    duration_min=20,
    mode=CardMode.WHOLE_GROUP,
    goal="固化共同记忆",
    steps=[
        "每人贡献 1–2 条",
        "必须指向具体人/具体时刻",
    ],
    output=OutputType.LIST,
    agent_script="不要大道理，要具体瞬间。",
    fallback="模板：'我记得__说过__，让我__'",
    tags=["closing", "reflective"],
    safety_notes="不强迫分享",
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
