# -*- coding: utf-8 -*-
"""Baking & Bread (7) și Fermentation & Preserving (6)."""

LESSONS = [
    # ================= BAKING & BREAD =================
    {
        "slug": "bake-measuring", "branch": "bake", "title": "Weigh, Don't Scoop", "icon": "⚖️",
        "req_tier": 2, "est_min": 15,
        "summary": "Baking is chemistry with a deadline. Volume measurements are the reason your results vary.",
        "intro": (
            "A cup of flour can weigh anywhere from 120 to 160 grams depending on how it got into the cup. "
            "That is a thirty percent swing in the main structural ingredient — enough to turn a tender cake "
            "into a dry one, and it explains most 'the recipe didn't work' complaints."
        ),
        "steps": [
            "Buy a digital scale that reads to one gram. It is the cheapest improvement available to a baker.",
            "Weigh everything, including liquids — one millilitre of water is one gram, which makes it simple.",
            "Use baker's percentages: every ingredient expressed as a percentage of the flour weight.",
            "Note that hydration is simply water weight divided by flour weight — 70% hydration means 700 g water per kilo of flour.",
            "Tare the bowl between additions rather than dirtying several containers.",
            "Record what you did. A recipe you cannot reproduce is not yet a recipe.",
        ],
        "tips": [
            "If you must use cups, spoon flour into the cup and level it — never scoop with the cup itself.",
            "Baker's percentages always exceed 100% in total. That is expected, not an error.",
        ],
        "quiz": [
            {"q": "The main problem with measuring flour by volume is that…", "options": ["It is slow", "The weight varies hugely with how it is packed", "Cups are inaccurate sizes", "It needs more washing up"], "correct": 1},
            {"q": "In baker's percentages, every ingredient is expressed relative to…", "options": ["Total weight", "Flour weight", "Water weight", "Yeast weight"], "correct": 1},
            {"q": "70% hydration means…", "options": ["700 g water per kilo of flour", "70 g water per kilo of flour", "70% of the dough is water", "Water and flour are equal"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Two bakers follow the same cup-based recipe and get different crumb. The most likely cause is…", "options": ["Oven temperature", "Different flour weight from different scooping methods", "Different water", "Different bowls"], "correct": 1},
            {"q": "Baker's percentages total more than 100% because…", "options": ["Of an error", "Flour is the 100% baseline and everything else is added on top", "Water is counted twice", "Yeast is excluded"], "correct": 1},
            {"q": "Two doughs at the same hydration behave differently. The likeliest reason is…", "options": ["Different flour protein content and absorption", "Different scales", "Different bowls", "Different water temperature only"], "correct": 0},
        ],
    },
    {
        "slug": "bake-gluten", "branch": "bake", "title": "Gluten & Kneading", "icon": "🌾",
        "req_tier": 3, "est_min": 25,
        "summary": "The protein network that traps gas — how to build it, and when to build less of it.",
        "intro": (
            "Flour contains two proteins that, once wet and worked, link into gluten: an elastic network that "
            "traps the gas fermentation produces. Bread wants a lot of it. Pastry wants almost none. Knowing "
            "which you are making tells you how to handle the dough."
        ),
        "steps": [
            "Mix flour and water and let it rest before kneading — an autolyse develops gluten with no effort at all.",
            "Knead by stretching and folding rather than tearing; gluten builds by alignment, not violence.",
            "Test with the windowpane: stretch a piece thin enough to see light through without tearing.",
            "Use high-protein bread flour for chew and structure, low-protein flour for tenderness.",
            "Add salt after the autolyse — it tightens the dough and slows hydration if added too early.",
            "For cakes and pastry, mix as little as possible once the flour is wet.",
        ],
        "tips": [
            "Rest is a substitute for work. A tight dough that fights you needs twenty minutes, not more kneading.",
            "Fat and sugar both interfere with gluten formation — that is precisely why enriched doughs are soft.",
        ],
        "quiz": [
            {"q": "Kneading mainly develops…", "options": ["Gluten", "Sugar", "Fat", "Salt"], "correct": 0},
            {"q": "The windowpane test checks whether…", "options": ["The dough has risen", "Gluten is sufficiently developed", "The oven is hot", "The dough is salted"], "correct": 1},
            {"q": "For tender pastry you want to…", "options": ["Knead thoroughly", "Mix as little as possible once flour is wet", "Use bread flour", "Add more water"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "An autolyse develops gluten without kneading because…", "options": ["Enzymes and hydration let the proteins link on their own over time", "Water heats the dough", "It adds oxygen", "Salt activates it"], "correct": 0},
            {"q": "Fat produces tenderness by…", "options": ["Coating flour proteins and shortening the gluten strands", "Adding moisture", "Killing yeast", "Adding air"], "correct": 0},
            {"q": "Salt added at the very start of mixing…", "options": ["Tightens gluten and slows hydration", "Kills the gluten", "Has no effect", "Speeds fermentation"], "correct": 0},
        ],
    },
    {
        "slug": "bake-leavening", "branch": "bake", "title": "Leavening Agents", "icon": "🫧",
        "req_tier": 4, "est_min": 20,
        "summary": "Yeast, baking soda, baking powder and steam — four ways to make things rise, each with rules.",
        "intro": (
            "Everything that rises does so because gas is produced or expands faster than the structure sets. "
            "Biological leavening is slow and flavourful, chemical leavening is fast and neutral, and steam "
            "is what makes choux and puff pastry possible."
        ),
        "steps": [
            "Use yeast when you want flavour from fermentation and have time; temperature controls its speed.",
            "Use baking soda only when the batter contains acid — buttermilk, yoghurt, cocoa, honey — or it will taste soapy.",
            "Use baking powder when there is no acid present; it carries its own.",
            "Get chemically leavened batters into the oven promptly; single-acting powders start working immediately.",
            "Rely on steam for choux and puff pastry — a hot oven turning water into vapour does the lifting.",
            "Never substitute soda and powder one-for-one; powder is roughly three to four times weaker.",
        ],
        "tips": [
            "Too much baking soda tastes metallic and soapy. Too much powder tastes bitter. Both collapse the crumb.",
            "Yeast doubles in speed for roughly every 10°C warmer, up to a point — which is why dough proofs faster in summer.",
        ],
        "quiz": [
            {"q": "Baking soda requires…", "options": ["An acid in the batter", "A hot oven only", "Yeast", "Sugar"], "correct": 0},
            {"q": "Choux pastry rises mainly from…", "options": ["Yeast", "Steam", "Baking powder", "Whipped whites"], "correct": 1},
            {"q": "Baking powder compared with baking soda is…", "options": ["Much weaker per gram", "Much stronger per gram", "Identical", "Only for bread"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "A cake made with baking soda but no acid tastes soapy because…", "options": ["Unreacted sodium bicarbonate remains", "It burns", "The sugar caramelises", "The gluten develops"], "correct": 0},
            {"q": "Double-acting baking powder is more forgiving because it releases gas…", "options": ["Once on mixing and again on heating", "Only in the oven", "Only when cold", "Continuously for hours"], "correct": 0},
            {"q": "Yeast fermentation adds flavour that chemical leavening cannot because it produces…", "options": ["Only carbon dioxide", "Organic acids, alcohols and esters alongside the gas", "More gluten", "More steam"], "correct": 1},
        ],
    },
    {
        "slug": "bake-pastry", "branch": "bake", "title": "Shortcrust & Lamination", "icon": "🥐",
        "req_tier": 6, "est_min": 30,
        "summary": "Cold butter, minimum handling, visible layers. Why pastry hates warm hands.",
        "intro": (
            "Pastry is a fight between fat and gluten, and you want fat to win. Cold, solid pieces of butter "
            "stay separate in the dough; in the oven they melt and steam, pushing the layers apart. Warm "
            "butter blends in, and you get bread instead."
        ),
        "steps": [
            "Keep everything cold — butter, water, bowl, and ideally your hands and the room.",
            "For shortcrust, rub or cut butter into flour until you have coarse crumbs with visible pieces still showing.",
            "Add just enough ice water to bring it together, then stop; over-worked pastry shrinks and toughens.",
            "Rest the dough in the fridge before rolling, and again after shaping, to relax the gluten.",
            "For lamination, encase a butter block in dough and repeat fold-and-roll turns, chilling between each.",
            "Bake hot at the start so the water in the butter turns to steam before the fat simply leaks out.",
        ],
        "tips": [
            "Shrinking pastry means the gluten was stretched and not rested. More resting, not more flour.",
            "If butter starts breaking through during lamination, stop and chill — pushing on ruins the layers.",
        ],
        "quiz": [
            {"q": "Butter in pastry must be…", "options": ["Cold and in visible pieces", "Melted", "Room temperature", "Whipped"], "correct": 0},
            {"q": "Pastry that shrinks in the tin was…", "options": ["Under-baked", "Over-worked and under-rested", "Too cold", "Too fatty"], "correct": 1},
            {"q": "Laminated pastry rises because…", "options": ["Yeast ferments", "Water in the butter layers turns to steam and pushes them apart", "Baking powder reacts", "Gluten expands"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "Warm butter ruins pastry because it…", "options": ["Blends into the flour instead of staying as discrete layers", "Burns faster", "Adds water", "Kills the leavening"], "correct": 0},
            {"q": "Laminated dough is chilled between turns mainly to…", "options": ["Keep the butter solid and let the gluten relax", "Add flavour", "Speed the process", "Dry the surface"], "correct": 0},
            {"q": "Puff pastry baked in a cool oven fails because…", "options": ["The butter melts and leaks out before steam can lift the layers", "Gluten does not set", "Water evaporates too fast", "Sugar burns"], "correct": 0},
        ],
    },
    {
        "slug": "bake-bread", "branch": "bake", "title": "Straight-Dough Bread", "icon": "🍞",
        "req_tier": 8, "est_min": 40,
        "summary": "Mix, bulk ferment, shape, proof, bake. The five stages every loaf goes through.",
        "intro": (
            "Bread has exactly five stages, and nearly every fault maps to one of them. Once you can name "
            "which stage went wrong — under-fermented, under-shaped, over-proofed, under-baked — you stop "
            "needing recipes and start adjusting."
        ),
        "steps": [
            "Mix flour, water, salt and yeast, then rest for the gluten to develop before working the dough.",
            "Bulk ferment until noticeably risen and airy, folding the dough every half hour to build strength.",
            "Pre-shape gently, rest, then shape with real surface tension — a slack loaf spreads instead of rising.",
            "Proof until the dough springs back slowly when poked, leaving a slight indentation.",
            "Score the top decisively so the loaf expands where you decided, not where it chooses.",
            "Bake hot with steam for the first ten minutes, then dry heat until the crust is deeply coloured and the base sounds hollow.",
        ],
        "tips": [
            "The poke test beats the clock. Dough ferments on temperature, not on your schedule.",
            "Let bread cool completely before cutting — the crumb is still setting as it cools.",
        ],
        "quiz": [
            {"q": "Bulk fermentation happens…", "options": ["After shaping", "Before shaping", "During baking", "After baking"], "correct": 1},
            {"q": "Dough is properly proofed when poked it…", "options": ["Springs back instantly", "Springs back slowly, leaving a slight indentation", "Does not move", "Collapses"], "correct": 1},
            {"q": "Steam in the first minutes of baking…", "options": ["Lets the loaf expand before the crust sets", "Cools the oven", "Adds flavour only", "Prevents browning entirely"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "An over-proofed loaf collapses in the oven because…", "options": ["The gluten network is exhausted and can no longer hold the gas", "There is too little yeast", "The oven is too hot", "It was scored"], "correct": 0},
            {"q": "Scoring controls the loaf's expansion because it…", "options": ["Creates a deliberate weak point for oven spring", "Releases steam entirely", "Cools the surface", "Adds surface tension"], "correct": 0},
            {"q": "A dense, tight crumb with a pale crust most likely means the dough was…", "options": ["Over-proofed", "Under-fermented", "Over-hydrated", "Over-scored"], "correct": 1},
        ],
        "extra": ["heat-roasting"],
    },
    {
        "slug": "bake-sourdough", "branch": "bake", "title": "Sourdough & Hydration", "icon": "🥖",
        "req_tier": 10, "est_min": 45,
        "summary": "A wild culture, a wetter dough, and an open crumb that takes practice to earn.",
        "intro": (
            "Sourdough replaces commercial yeast with a culture of wild yeast and lactic bacteria you keep "
            "alive yourself. It is slower, more variable, and more flavourful — and it rewards paying "
            "attention to your dough rather than to a timetable."
        ),
        "steps": [
            "Keep a starter fed on a regular schedule; use it when it reliably doubles and smells pleasantly sour.",
            "Mix at higher hydration — 75% and up — for a more open crumb, accepting that the dough is harder to handle.",
            "Use stretch-and-folds rather than kneading to build strength in a wet dough.",
            "Judge bulk fermentation by rise and feel, not by hours; a cold kitchen can double the time.",
            "Shape with wet hands and confident, quick movements to preserve the gas already in the dough.",
            "Cold-proof overnight in the fridge for better flavour, easier scoring and a more reliable schedule.",
        ],
        "tips": [
            "A starter that is not doubling will not raise a loaf. Fix the starter before blaming the recipe.",
            "Higher hydration is not automatically better — an open crumb you cannot shape is not a win.",
        ],
        "quiz": [
            {"q": "Higher-hydration dough tends to give a…", "options": ["Denser crumb", "More open crumb", "Sweeter loaf", "Thicker crust only"], "correct": 1},
            {"q": "Bulk fermentation should be judged by…", "options": ["The clock", "The dough's rise and feel", "The oven temperature", "The starter's age"], "correct": 1},
            {"q": "Cold-proofing overnight mainly improves…", "options": ["Flavour and handling", "Rise speed", "Hydration", "Gluten content"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Sourdough tastes more complex than yeasted bread mainly because…", "options": ["It bakes longer", "Lactic and acetic acid bacteria produce acids and aromatics alongside the yeast", "It has more salt", "It is wetter"], "correct": 1},
            {"q": "Stretch-and-fold suits high-hydration dough better than kneading because it…", "options": ["Builds strength without tearing a slack, sticky gluten network", "Is faster", "Adds air", "Warms the dough"], "correct": 0},
            {"q": "Cold-proofing improves scoring because the chilled dough…", "options": ["Is firmer, so the blade cuts cleanly instead of dragging", "Has more gas", "Is drier", "Has stronger gluten"], "correct": 0},
        ],
        "extra": ["ferment-starter"],
    },
    {
        "slug": "bake-enriched", "branch": "bake", "title": "Enriched & Viennoiserie", "icon": "🥯",
        "req_tier": 12, "est_min": 45,
        "summary": "Butter, egg and sugar fight the yeast and the gluten. Brioche is the exam.",
        "intro": (
            "Enriched doughs add fat, sugar and egg to bread, and every one of those slows fermentation and "
            "weakens gluten. The result is soft and rich, but it needs the gluten built before the butter "
            "goes in, and it needs cold to stay workable."
        ),
        "steps": [
            "Build the gluten fully with flour, liquid, egg and yeast before adding any butter.",
            "Add softened butter gradually, letting each addition fully incorporate before the next.",
            "Expect the dough to look broken partway through — keep mixing and it comes back together.",
            "Chill the dough thoroughly before shaping; warm brioche dough is unworkable.",
            "Proof enriched doughs more slowly and more gently — high sugar slows the yeast.",
            "Bake at a lower temperature than lean bread, since sugar and dairy brown far faster.",
        ],
        "tips": [
            "If butter is leaking out of the dough, it is too warm. Chill it, do not add flour.",
            "Enriched doughs stale more slowly than lean breads: fat and sugar hold moisture.",
        ],
        "quiz": [
            {"q": "In brioche, butter should be added…", "options": ["At the very start with the flour", "After the gluten is developed", "After proofing", "Only on top"], "correct": 1},
            {"q": "Enriched doughs are baked at a lower temperature because…", "options": ["Sugar and dairy brown much faster", "They contain more water", "They rise less", "The gluten is weak"], "correct": 0},
            {"q": "High sugar content in a dough…", "options": ["Slows the yeast", "Speeds the yeast indefinitely", "Has no effect", "Replaces the yeast"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Sugar slows fermentation at high concentrations because it…", "options": ["Draws water out of the yeast cells osmotically", "Kills the yeast instantly", "Lowers the pH", "Adds heat"], "correct": 0},
            {"q": "Brioche dough looks broken mid-mix because…", "options": ["The butter has not yet dispersed into the gluten network", "The gluten has torn permanently", "The eggs curdled", "It is over-proofed"], "correct": 0},
            {"q": "Enriched breads stale more slowly because fat and sugar…", "options": ["Interfere with starch retrogradation and hold moisture", "Kill bacteria", "Add gluten", "Lower the baking temperature"], "correct": 0},
        ],
    },

    # ================= FERMENTATION & PRESERVING =================
    {
        "slug": "ferment-salt", "branch": "ferment", "title": "Salt, Brine & Safety", "icon": "🧂",
        "req_tier": 4, "est_min": 20,
        "summary": "The rules that make fermentation safe: enough salt, no oxygen, and everything below the brine.",
        "intro": (
            "Fermentation is controlled spoilage: you make conditions that favour the microbes you want and "
            "suppress the ones you do not. Salt concentration and the absence of oxygen do almost all of "
            "that work, which is why the rules are short and non-negotiable."
        ),
        "steps": [
            "Work by weight: a typical vegetable ferment uses 2–3% salt relative to the weight of vegetables and water.",
            "Keep everything submerged under the brine — mould grows on what pokes out, not on what is covered.",
            "Use a weight or a filled bag to hold the vegetables down, and a lid that lets gas escape.",
            "Ferment at cool room temperature; heat speeds things up and makes results mushy and unpredictable.",
            "Taste regularly and refrigerate when you like it — cold slows fermentation to a crawl.",
            "Trust your senses: a good ferment smells sharp and clean, a bad one smells genuinely rotten.",
        ],
        "tips": [
            "White film on the surface is usually harmless kahm yeast. Fuzzy, coloured mould is not — discard it.",
            "Use non-iodised salt and unchlorinated water; both additives inhibit the bacteria you want.",
        ],
        "quiz": [
            {"q": "Salt in a ferment mainly…", "options": ["Adds sweetness", "Favours good microbes and slows bad ones", "Speeds up browning", "Thickens the brine"], "correct": 1},
            {"q": "A healthy vegetable ferment should be kept…", "options": ["Exposed to the air", "Submerged under its brine", "In the freezer", "In direct sun"], "correct": 1},
            {"q": "A typical vegetable ferment uses roughly…", "options": ["2–3% salt by weight", "10% salt by weight", "0.1% salt by weight", "No salt"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Lactic acid bacteria dominate a brine ferment because they…", "options": ["Tolerate salt and low oxygen better than spoilage organisms", "Grow fastest at any condition", "Need oxygen", "Are added deliberately"], "correct": 0},
            {"q": "Iodised salt is avoided because iodine…", "options": ["Inhibits the bacteria you are cultivating", "Tastes bitter", "Dissolves poorly", "Adds colour"], "correct": 0},
            {"q": "A ferment becomes safe from pathogens over time mainly because…", "options": ["Salt kills everything", "Accumulating lactic acid drops the pH below what pathogens tolerate", "Oxygen is removed", "It is refrigerated"], "correct": 1},
        ],
    },
    {
        "slug": "ferment-kraut", "branch": "ferment", "title": "Kraut & Kimchi", "icon": "🥬",
        "req_tier": 5, "est_min": 25,
        "summary": "Dry-salting vegetables so they make their own brine — the simplest ferment there is.",
        "intro": (
            "Cabbage contains enough water that you do not need to add any: salt it, work it, and it releases "
            "its own brine. That makes kraut the ideal first ferment — one ingredient, one variable, and a "
            "result you can taste changing day by day."
        ),
        "steps": [
            "Shred the cabbage finely and weigh it, then add 2% of that weight in salt.",
            "Massage and squeeze for several minutes until liquid pools freely in the bowl.",
            "Pack tightly into a jar, pressing down hard so the brine rises above the vegetables.",
            "Weight it down, cover loosely, and leave at cool room temperature.",
            "Burp the jar daily for the first week if the lid is tight — fermentation produces real pressure.",
            "For kimchi, add a paste of chilli, garlic, ginger and fish sauce after the initial salting.",
        ],
        "tips": [
            "If the cabbage does not release enough liquid, top up with a 2% brine rather than plain water.",
            "Taste from day three. Knowing what each stage tastes like is the point of making it yourself.",
        ],
        "quiz": [
            {"q": "Sauerkraut brine comes from…", "options": ["Added water", "The cabbage's own liquid drawn out by salt", "Vinegar", "Stock"], "correct": 1},
            {"q": "Salt for kraut is roughly…", "options": ["2% of the cabbage weight", "20% of the cabbage weight", "A pinch regardless of weight", "None"], "correct": 0},
            {"q": "Jars with tight lids need burping because fermentation…", "options": ["Produces carbon dioxide and real pressure", "Creates a vacuum", "Absorbs air", "Heats the jar"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Salt draws liquid from cabbage through…", "options": ["Osmosis across the cell membranes", "Evaporation", "Chemical reaction", "Heat"], "correct": 0},
            {"q": "Kraut fermented too warm turns mushy because…", "options": ["Pectin-degrading enzymes and unwanted microbes work faster at high temperature", "Salt dissolves", "Too much acid forms", "Oxygen enters"], "correct": 0},
            {"q": "Kimchi ferments faster than plain kraut largely because…", "options": ["The added sugars in the paste feed the bacteria", "Chilli is antibacterial", "It uses less salt always", "It is warmer"], "correct": 0},
        ],
    },
    {
        "slug": "ferment-starter", "branch": "ferment", "title": "Wild Starters", "icon": "🫧",
        "req_tier": 7, "est_min": 30,
        "summary": "Building and keeping a sourdough starter — a culture you feed rather than a product you buy.",
        "intro": (
            "A starter is a stable community of wild yeast and lactic bacteria living in flour and water. "
            "Creating one takes a week of feeding; keeping one takes minutes. The main skill is reading what "
            "it is telling you rather than following a fixed schedule."
        ),
        "steps": [
            "Mix equal weights of wholemeal flour and water and leave it at room temperature.",
            "Feed daily by discarding most of it and refreshing with fresh flour and water.",
            "Expect an early burst of activity from the wrong bacteria around day two, then a lull — this is normal.",
            "Continue until it reliably doubles within four to eight hours of feeding.",
            "Store in the fridge and feed weekly if you bake occasionally; keep it at room temperature and feed daily if you bake often.",
            "Judge readiness by the rise-and-fall cycle, not by the calendar.",
        ],
        "tips": [
            "Discard feels wasteful but is essential — without it, acidity builds until the culture stalls.",
            "A grey liquid on top ('hooch') means it is hungry, not dead. Stir it in or pour it off and feed.",
        ],
        "quiz": [
            {"q": "A starter is ready to bake with when it…", "options": ["Smells sour", "Reliably doubles within a few hours of feeding", "Is one week old", "Has liquid on top"], "correct": 1},
            {"q": "Discarding part of the starter before feeding…", "options": ["Wastes flour needlessly", "Stops acidity building until the culture stalls", "Adds yeast", "Cools it"], "correct": 1},
            {"q": "Dark liquid on top of a starter means it is…", "options": ["Dead", "Hungry", "Contaminated", "Ready"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "The early day-two activity in a new starter is usually caused by…", "options": ["Wild yeast", "Non-sourdough bacteria that later die off as acidity rises", "Contamination", "The flour's own enzymes only"], "correct": 1},
            {"q": "A refrigerated starter needs less frequent feeding because cold…", "options": ["Slows the microbial metabolism dramatically", "Kills the bacteria", "Removes acid", "Adds oxygen"], "correct": 0},
            {"q": "Wholemeal flour is recommended for starting a culture because it carries…", "options": ["More wild microorganisms and more minerals", "More gluten", "Less water", "More sugar"], "correct": 0},
        ],
    },
    {
        "slug": "ferment-pickle", "branch": "ferment", "title": "Pickling & Acidity", "icon": "🥒",
        "req_tier": 8, "est_min": 25,
        "summary": "Quick vinegar pickles versus true fermented ones — two different things with the same name.",
        "intro": (
            "A quick pickle is a vinegar marinade: acid is added, nothing ferments, and it is ready in an "
            "hour. A fermented pickle makes its own acid over days. They taste completely different, and "
            "confusing the two is why some 'pickle' recipes fail."
        ),
        "steps": [
            "For quick pickles, make a brine of vinegar, water, salt and sugar, and pour it hot over the vegetables.",
            "Balance to taste: a common starting ratio is equal parts vinegar and water.",
            "Use firm vegetables and cut them thick enough to survive the hot brine.",
            "For fermented pickles, use a 3–5% salt brine and no vinegar at all, and wait days rather than hours.",
            "Add tannin — grape, oak or black tea leaves — to fermented cucumbers to keep them crisp.",
            "Refrigerate quick pickles and treat them as a fresh product; they are not shelf-stable preserves.",
        ],
        "tips": [
            "Quick pickles keep weeks in the fridge, not months on a shelf. Shelf stability needs proper canning.",
            "Cucumbers go soft when their pectin breaks down — cut the blossom end off, it carries the enzyme.",
        ],
        "quiz": [
            {"q": "A quick pickle gets its acidity from…", "options": ["Fermentation", "Added vinegar", "Salt", "Sugar"], "correct": 1},
            {"q": "A fermented pickle brine contains…", "options": ["Vinegar and salt", "Salt and water, no vinegar", "Only vinegar", "Sugar and water"], "correct": 1},
            {"q": "Quick pickles should be stored…", "options": ["In the fridge", "On a shelf indefinitely", "In the freezer", "At room temperature for months"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Tannin-containing leaves keep fermented cucumbers crisp because tannins…", "options": ["Inhibit the pectin-degrading enzymes that soften them", "Add acid", "Absorb water", "Kill all bacteria"], "correct": 0},
            {"q": "Removing the blossom end of a cucumber helps because it contains…", "options": ["Enzymes that soften the pickle", "Excess salt", "Bitter compounds only", "Air pockets"], "correct": 0},
            {"q": "Shelf stability in preserving requires…", "options": ["A sufficiently low pH plus proper heat processing and sealing", "Salt alone", "Vinegar alone", "Refrigeration"], "correct": 0},
        ],
    },
    {
        "slug": "ferment-cure", "branch": "ferment", "title": "Curing & Smoking", "icon": "🥓",
        "req_tier": 10, "est_min": 35,
        "summary": "Salt, time and smoke — preserving protein, and the one ingredient you must measure exactly.",
        "intro": (
            "Curing draws water out of protein and makes it inhospitable to spoilage. Short cures for flavour "
            "are forgiving; long cures intended for preservation are not, and they involve curing salts that "
            "must be weighed precisely rather than estimated."
        ),
        "steps": [
            "Weigh the protein and calculate salt as a percentage of it — equilibrium curing removes the guesswork.",
            "Use around 2–3% salt for a flavour cure, applied evenly and left in the fridge in a sealed bag.",
            "Flip the bag daily so the developing brine reaches every surface.",
            "Rinse and dry thoroughly after curing; a dry surface is what takes smoke and forms a pellicle.",
            "Cold-smoke below 30°C for flavour only, or hot-smoke to cook and flavour at the same time.",
            "For anything cured long, at low temperature, or stored anaerobically, follow a tested recipe using nitrite curing salt exactly as specified.",
        ],
        "tips": [
            "Equilibrium curing means the meat cannot get saltier than your calculation, so it cannot be over-cured.",
            "Curing salts are not optional flavourings for long cures — treat their quantities as a safety measure.",
        ],
        "quiz": [
            {"q": "Equilibrium curing means…", "options": ["Salt is calculated as a percentage of the meat's weight", "The meat is buried in salt", "Salt is added by eye", "No salt is used"], "correct": 0},
            {"q": "A pellicle is…", "options": ["The dried surface that takes on smoke", "A type of salt", "A smoking wood", "A curing bag"], "correct": 0},
            {"q": "Cold smoking…", "options": ["Flavours without cooking", "Cooks the food through", "Requires no curing", "Happens above 100°C"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Curing preserves food primarily by…", "options": ["Reducing water activity so microbes cannot grow", "Adding acid", "Killing bacteria with smoke", "Freezing the surface"], "correct": 0},
            {"q": "Nitrite curing salts are specified for long, low-temperature cures because they…", "options": ["Inhibit Clostridium botulinum in anaerobic conditions", "Add colour only", "Speed up the cure", "Improve texture"], "correct": 0},
            {"q": "Equilibrium curing cannot over-salt the meat because…", "options": ["The salt available is capped at exactly what you weighed in", "Salt evaporates", "The meat rejects excess", "Rinsing removes it"], "correct": 0},
        ],
    },
    {
        "slug": "ferment-koji", "branch": "ferment", "title": "Koji & Umami", "icon": "🍶",
        "req_tier": 12, "est_min": 35,
        "summary": "Miso, soy and garum — long ferments that manufacture glutamate and change how a dish tastes.",
        "intro": (
            "Some ferments do not just preserve, they build flavour that was not there. Koji mould produces "
            "enzymes that break proteins into amino acids — including glutamate, which we taste as savoury "
            "depth. It is the engine behind miso, soy sauce and much of Japanese cooking."
        ),
        "steps": [
            "Understand the principle: enzymes cut long protein and starch chains into small, flavourful fragments.",
            "Start with a bought koji rice rather than cultivating spores yourself.",
            "For a simple miso, blend cooked legumes with koji and salt, pack tightly, and weight the surface.",
            "Ferment at cool room temperature for months, checking occasionally for surface issues.",
            "Expect colour to deepen over time as Maillard reactions proceed slowly, without heat.",
            "Use these ferments as seasonings rather than ingredients — a spoonful changes an entire dish.",
        ],
        "tips": [
            "Long ferments are a patience skill. Start one, forget it, and be surprised in six months.",
            "A little miso whisked into a butter sauce or a dressing adds depth almost nothing else can.",
        ],
        "quiz": [
            {"q": "Koji enzymes break proteins down into…", "options": ["Amino acids, including glutamate", "Sugars only", "Fats", "Starch"], "correct": 0},
            {"q": "Miso should be used mainly as…", "options": ["A seasoning", "A main ingredient by volume", "A leavening agent", "A thickener"], "correct": 0},
            {"q": "The colour of a long-fermented miso deepens because of…", "options": ["Slow Maillard reactions without heat", "Added colouring", "Oxidation of salt", "Mould growth"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Glutamate tastes savoury because it…", "options": ["Activates dedicated umami receptors on the tongue", "Is salty", "Is acidic", "Contains protein"], "correct": 0},
            {"q": "Koji is applied to starchy substrates in sake brewing to…", "options": ["Convert starch into fermentable sugars for the yeast", "Add salt", "Kill bacteria", "Add colour"], "correct": 0},
            {"q": "A high salt percentage in miso serves to…", "options": ["Restrict fermentation to salt-tolerant organisms over a very long period", "Speed fermentation", "Add flavour only", "Prevent Maillard reactions"], "correct": 0},
        ],
    },
]
