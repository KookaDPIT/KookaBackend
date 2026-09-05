# -*- coding: utf-8 -*-
"""Ramurile fundamentale: Knife Skills (6) și Heat & Searing (6)."""

LESSONS = [
    # ================= KNIFE SKILLS =================
    {
        "slug": "knife-grip", "branch": "knife", "title": "Grip & Claw", "icon": "✋",
        "req_tier": 0, "est_min": 15,
        "summary": "How to hold a knife so it becomes an extension of your hand — and how to keep your fingertips.",
        "intro": (
            "Most home cooks hold a knife by the handle alone, which gives the blade a mind of its own. "
            "The pinch grip puts your hand on the blade itself, where the control is. Paired with the claw "
            "on your guiding hand, it is the single change that makes chopping both faster and safer."
        ),
        "steps": [
            "Pinch the blade between thumb and the side of your index finger, just ahead of the handle; wrap the remaining fingers around the handle.",
            "Curl the fingertips of your other hand under, so the flat of your knuckles — not your nails — touches the blade.",
            "Rest the side of the blade against those knuckles and let them steer the cut width.",
            "Keep the tip of the knife on the board and rock the blade down through the food rather than lifting it clear each time.",
            "Move your guiding hand backwards in small steps; the knife stays where it is and the food comes to it.",
        ],
        "tips": [
            "If your wrist aches, your grip is too far back on the handle.",
            "Slow, correct repetitions build speed. Speed first builds scars.",
        ],
        "quiz": [
            {"q": "The 'claw' grip mainly protects your…", "options": ["Wrist", "Fingertips", "Thumb only", "Palm"], "correct": 1},
            {"q": "In a pinch grip, your thumb and index finger sit on…", "options": ["The very end of the handle", "The blade, just ahead of the handle", "The spine near the tip", "The bolster underneath"], "correct": 1},
            {"q": "A sharp knife is safer because it…", "options": ["Needs less force and slips less", "Cuts faster so you finish sooner", "Looks more professional", "Is heavier to hold"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "What actually controls the thickness of each slice?", "options": ["How hard you press", "How far the guiding-hand knuckles move back", "The knife's weight", "The angle of the handle"], "correct": 1},
            {"q": "Keeping the tip on the board during a rock chop mainly…", "options": ["Sharpens the blade", "Keeps the cut path consistent and the blade controlled", "Reduces noise", "Protects the board"], "correct": 1},
            {"q": "Your cuts drift diagonally instead of straight down. The usual cause is…", "options": ["A dull knife", "Gripping the handle only, letting the blade twist", "A wet board", "Cold ingredients"], "correct": 1},
        ],
    },
    {
        "slug": "knife-sharpening", "branch": "knife", "title": "Sharpening & Honing", "icon": "🪛",
        "req_tier": 1, "est_min": 20,
        "summary": "The difference between honing and sharpening, and why a dull knife is the dangerous one.",
        "intro": (
            "A blade dulls in two ways: the fine edge folds over to one side, and the steel actually wears "
            "away. A honing rod fixes the first in seconds. Only a stone fixes the second. Confusing the two "
            "is why most kitchen knives are permanently blunt."
        ),
        "steps": [
            "Test the edge on a sheet of paper held upright: a sharp knife slices, a dull one tears or slides.",
            "Hone before most cooking sessions — a dozen light passes per side at roughly 15–20°, letting the weight of the knife do the work.",
            "Sharpen on a stone only when honing stops helping, typically every few months of regular use.",
            "Soak a whetstone as its maker directs, start on the coarse side, and keep the angle constant for the whole stroke.",
            "Work until you feel a fine burr along the whole opposite edge, then flip and repeat, then refine on the fine side.",
            "Finish with a few very light alternating passes to remove the burr, then wash and dry the blade immediately.",
        ],
        "tips": [
            "Never put a good knife in the dishwasher — heat, detergent and knocking ruin both edge and handle.",
            "A cheap knife you sharpen beats an expensive one you don't.",
        ],
        "quiz": [
            {"q": "Honing a knife…", "options": ["Removes steel to create a new edge", "Realigns the existing edge", "Polishes the handle", "Hardens the blade"], "correct": 1},
            {"q": "A typical honing angle for a European kitchen knife is around…", "options": ["5°", "15–20°", "45°", "90°"], "correct": 1},
            {"q": "You know you've sharpened one side enough when…", "options": ["The blade feels warm", "A burr appears along the opposite edge", "The stone turns grey", "Ten minutes have passed"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "Why does a burr form during sharpening?", "options": ["The steel folds over past the apex as it thins", "The stone deposits grit", "Water hardens the edge", "The blade expands with heat"], "correct": 0},
            {"q": "Honing no longer restores your edge. That means…", "options": ["The rod is dirty", "The edge steel is worn away and needs a stone", "The knife is too hard", "You honed at too low an angle"], "correct": 1},
            {"q": "Sharpening at a wider angle than the original bevel produces an edge that is…", "options": ["Sharper and more delicate", "More durable but less keen", "Identical", "Impossible to hone"], "correct": 1},
        ],
    },
    {
        "slug": "knife-dice", "branch": "knife", "title": "The Even Dice", "icon": "🧅",
        "req_tier": 2, "est_min": 20,
        "summary": "Turn an onion into an even dice. Uniform pieces cook evenly — that is the whole point.",
        "intro": (
            "An even dice is not about looking professional. Pieces of different sizes finish at different "
            "times, so half your onion is raw while the other half burns. The onion method generalises to "
            "nearly every round vegetable."
        ),
        "steps": [
            "Halve the onion through the root and peel, leaving the root intact — it holds the layers together.",
            "Lay a half flat and make horizontal cuts towards the root, stopping short of it.",
            "Make vertical cuts following the curve of the onion, again stopping before the root.",
            "Slice across those cuts and the dice falls apart on its own.",
            "Choose the spacing to match the dish: fine for a sauce base, larger for a stew where you want texture.",
            "Discard the root end last — it is your handle for the whole process.",
        ],
        "tips": [
            "Cut vertically along the onion's natural curve rather than straight down; the dice comes out far more even.",
            "Chill onions for fifteen minutes before cutting and they sting less.",
        ],
        "quiz": [
            {"q": "Why keep the root end of the onion intact?", "options": ["It adds flavour", "It holds the layers together while you cut", "It peels more easily", "It stops the onion rolling"], "correct": 1},
            {"q": "Uniform dice matters mainly because…", "options": ["It looks tidy", "The pieces cook evenly", "It is faster", "It uses less oil"], "correct": 1},
            {"q": "For a smooth sauce base you want the dice…", "options": ["Fine", "Large and chunky", "Sliced into rings", "Left whole"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Following the onion's curve with your vertical cuts gives a more even dice because…", "options": ["The layers are curved, so radial cuts keep segment width constant", "It is faster", "It releases less sulphur", "It avoids the root"], "correct": 0},
            {"q": "A mirepoix for a long-braised stew is cut coarse rather than fine because…", "options": ["It is quicker", "Fine dice would dissolve completely over the cook time", "Coarse cuts brown less", "It uses fewer onions"], "correct": 1},
            {"q": "Onions make you cry less when chilled because cold…", "options": ["Kills the enzymes permanently", "Slows the enzyme reaction and the compound's evaporation", "Adds moisture", "Hardens the cell walls only"], "correct": 1},
        ],
    },
    {
        "slug": "knife-julienne", "branch": "knife", "title": "Julienne & Batonnet", "icon": "🥕",
        "req_tier": 3, "est_min": 20,
        "summary": "Square off, plank, stack, slice. The cut that makes stir-fries and slaws behave.",
        "intro": (
            "Julienne is matchstick-thin, batonnet is its thicker cousin, and both start the same way: make "
            "the vegetable a rectangle first. Round things roll, and rolling is how people cut themselves."
        ),
        "steps": [
            "Trim the vegetable to a manageable length, then slice a thin strip off one side to create a flat, stable face.",
            "Lay it on that flat face and square off the remaining sides into a rectangular block.",
            "Cut the block into even planks — about 3 mm for julienne, 6 mm for batonnet.",
            "Stack a few planks, keeping edges aligned, and slice through them at the same thickness.",
            "Keep the stack short; too tall and it slips mid-cut.",
            "Save the trimmings for stock rather than throwing them away.",
        ],
        "tips": [
            "The first cut is always the one that makes the thing stop rolling.",
            "Julienned vegetables cook in a minute or two — add them near the end, not the start.",
        ],
        "quiz": [
            {"q": "The first step when julienning a carrot is to…", "options": ["Slice it into rounds", "Create a flat face so it stops rolling", "Peel it twice", "Cut it in half lengthways"], "correct": 1},
            {"q": "Julienne is roughly…", "options": ["3 mm matchsticks", "1 cm cubes", "Paper-thin rounds", "Random chunks"], "correct": 0},
            {"q": "Batonnet differs from julienne mainly in…", "options": ["Length", "Thickness", "The vegetable used", "The knife used"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "Squaring off a vegetable wastes trim but is worth it because…", "options": ["It looks better", "Every piece is then identical in thickness, so they cook identically", "It removes bitterness", "It speeds up peeling"], "correct": 1},
            {"q": "Julienne is added late to a stir-fry because its high surface-to-volume ratio means it…", "options": ["Absorbs more oil", "Cooks and overcooks very quickly", "Releases water slowly", "Browns poorly"], "correct": 1},
            {"q": "A brunoise is produced by…", "options": ["Dicing a julienne crossways", "A separate rolling cut", "Grating", "Slicing a batonnet lengthways"], "correct": 0},
        ],
    },
    {
        "slug": "knife-protein", "branch": "knife", "title": "Breaking Down Protein", "icon": "🍗",
        "req_tier": 5, "est_min": 30,
        "summary": "Joints, grain and silverskin. Butchering a chicken and trimming meat properly saves money and improves texture.",
        "intro": (
            "Buying a whole chicken and breaking it down costs far less than buying parts, gives you a "
            "carcass for stock, and teaches you where the joints are — which is the only difficult bit. "
            "You never cut through bone; you cut through the gap between bones."
        ),
        "steps": [
            "Pull a leg away from the body until the skin tightens, then cut through the skin only.",
            "Bend the leg back until the hip joint pops, then cut through the exposed joint — no sawing, no force.",
            "Remove the wings the same way, feeling for the shoulder joint with the knife tip.",
            "Run the knife down either side of the breastbone, following the ribcage to release each breast.",
            "For steaks and roasts, slide the blade under silverskin at a shallow upward angle and pull the membrane taut as you cut.",
            "Keep the carcass, wing tips and trimmings — they become stock in a later lesson.",
        ],
        "tips": [
            "If you are sawing, you are not on the joint. Reposition instead of pushing harder.",
            "Always slice cooked meat across the grain: it shortens the muscle fibres and makes it far more tender.",
        ],
        "quiz": [
            {"q": "To separate a chicken leg you should…", "options": ["Cut straight through the thigh bone", "Pop the hip joint and cut through the gap", "Use kitchen shears on the bone", "Freeze it first"], "correct": 1},
            {"q": "Slicing cooked meat across the grain makes it…", "options": ["More tender", "Juicier but tougher", "Cook faster", "Keep longer"], "correct": 0},
            {"q": "Silverskin should be removed because it…", "options": ["Is unsafe to eat", "Does not break down and turns chewy", "Absorbs salt", "Prevents browning"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "Cutting across the grain works because it…", "options": ["Shortens the muscle fibres you have to chew through", "Removes connective tissue", "Releases juices", "Breaks down collagen"], "correct": 0},
            {"q": "Buying whole birds is cheaper per kilo mainly because…", "options": ["They are lower quality", "You are paying for butchery labour when you buy parts", "Parts are always frozen", "Whole birds are older"], "correct": 1},
            {"q": "Removing silverskin at a shallow upward angle rather than flat…", "options": ["Is faster", "Keeps the blade under the membrane without cutting into the meat", "Sharpens the knife", "Prevents tearing the skin"], "correct": 1},
        ],
    },
    {
        "slug": "knife-fish", "branch": "knife", "title": "Filleting Fish", "icon": "🐟",
        "req_tier": 7, "est_min": 30,
        "summary": "A flexible blade, the spine as your guide, and the patience to let the fish come apart.",
        "intro": (
            "Filleting looks like surgery and is mostly geometry: there is one continuous bone plate down "
            "the middle and the flesh sits on either side of it. Your job is to keep the blade flat against "
            "that plate and let it lead."
        ),
        "steps": [
            "Use a thin, flexible filleting knife — a stiff chef's knife cannot follow the bone contour.",
            "Cut down behind the gill plate to the spine, but not through it.",
            "Turn the blade flat and run it along the spine from head to tail, using long strokes rather than short saws.",
            "Keep the blade angled very slightly downward so it stays in contact with the bones — that is where the waste is avoided.",
            "Flip the fish and repeat on the second side.",
            "Pin-bone the fillets by feel, pulling each bone in the direction it points with tweezers, then skin by anchoring the tail and running the blade flat against the skin.",
        ],
        "tips": [
            "Rinse and dry the blade between sides; a slippery blade with scales on it wanders.",
            "Keep the frames and heads for fish stock — but simmer them briefly, never for hours.",
        ],
        "quiz": [
            {"q": "A filleting knife should be…", "options": ["Thin and flexible", "Heavy and stiff", "Serrated", "Very short"], "correct": 0},
            {"q": "When running the blade along the spine you keep it…", "options": ["Angled slightly downward, in contact with the bones", "Angled upward into the flesh", "Perpendicular to the fish", "Off the bone entirely"], "correct": 0},
            {"q": "Pin bones should be pulled…", "options": ["Straight up hard", "In the direction they point", "Backwards towards the tail", "After cooking only"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "Angling the blade upward while filleting produces…", "options": ["Cleaner fillets", "Flesh left on the frame — wasted yield", "Fewer pin bones", "Better skin removal"], "correct": 1},
            {"q": "Fish stock is simmered briefly, unlike meat stock, because fish bones…", "options": ["Contain no collagen", "Release their gelatine fast and turn bitter with long cooking", "Are too small", "Float"], "correct": 1},
            {"q": "When skinning a fillet, the blade should be…", "options": ["Angled into the flesh", "Held flat, pressed slightly towards the skin while you pull the skin", "Held vertically", "Serrated"], "correct": 1},
        ],
    },

    # ================= HEAT & SEARING =================
    {
        "slug": "heat-pans", "branch": "heat", "title": "Reading Your Pan", "icon": "🍳",
        "req_tier": 1, "est_min": 15,
        "summary": "Stainless, cast iron, non-stick and carbon steel each want a different job. Choosing wrong is why food sticks.",
        "intro": (
            "Sticking is rarely the pan's fault. Each material has a temperature range and a task it suits: "
            "non-stick cannot brown, stainless browns beautifully but demands preheating, and cast iron holds "
            "heat so well that it barely notices a cold steak arriving."
        ),
        "steps": [
            "Use stainless steel for anything you want to deglaze — it builds fond, non-stick does not.",
            "Use cast iron or carbon steel when you need the pan to stay hot as cold food hits it.",
            "Reserve non-stick for eggs and delicate fish, and keep it below high heat to protect the coating.",
            "Preheat stainless properly: a drop of water should skitter across the surface as a bead rather than sizzling away instantly.",
            "Add the fat after the pan is hot, not before, and give it a few seconds to thin out and shimmer.",
            "Match pan size to food volume — a crowded pan steams, an empty one scorches the fat.",
        ],
        "tips": [
            "Thin pans have hot spots; heavy pans even them out. Weight matters more than brand.",
            "If food sticks to stainless, it usually needs another thirty seconds — a proper crust releases itself.",
        ],
        "quiz": [
            {"q": "Which pan is the wrong choice when you want to deglaze and make a pan sauce?", "options": ["Stainless steel", "Cast iron", "Non-stick", "Carbon steel"], "correct": 2},
            {"q": "The water-drop test on hot stainless shows readiness when the drop…", "options": ["Evaporates instantly", "Beads and skitters across the surface", "Spreads flat", "Sizzles loudly and sticks"], "correct": 1},
            {"q": "Oil should go into the pan…", "options": ["Before heating", "Once the pan is hot", "Halfway through cooking", "Only at the end"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "A water droplet skitters rather than boiling away because…", "options": ["The pan is not hot enough", "Vapour forms underneath and lifts it — the Leidenfrost effect", "The oil repels it", "Steel is hydrophobic"], "correct": 1},
            {"q": "Cast iron suits searing not because it conducts well but because it…", "options": ["Is non-stick", "Stores a lot of heat, so its surface temperature drops less when food lands", "Heats evenly", "Is heavy"], "correct": 1},
            {"q": "Food that sticks to hot stainless usually releases once…", "options": ["More oil is added", "The crust has formed and the protein-metal bond breaks", "The heat is lowered", "It is flipped repeatedly"], "correct": 1},
        ],
    },
    {
        "slug": "heat-maillard", "branch": "heat", "title": "The Maillard Reaction", "icon": "🥩",
        "req_tier": 2, "est_min": 20,
        "summary": "Why browning tastes like something and boiling tastes like nothing.",
        "intro": (
            "Browning is not 'cooking more'. It is a distinct chemical reaction between amino acids and "
            "sugars that only gets going once the surface is dry and hot — roughly above the boiling point "
            "of water. Everything wet is stuck at 100°C, which is why boiled meat is grey and seared meat is not."
        ),
        "steps": [
            "Pat the surface completely dry; any surface water must boil off before browning can begin.",
            "Preheat the pan properly and use a fat with a high enough smoke point for the job.",
            "Give the food room. A crowded pan releases steam faster than it can escape and you end up braising.",
            "Leave it alone. Every flip resets the surface temperature and delays the crust.",
            "Salt in advance where you can — salt draws out moisture, which then needs to evaporate.",
            "Listen: a loud, steady sizzle means water is leaving; silence means the pan cooled down.",
        ],
        "tips": [
            "Searing does not 'seal in juices' — that idea was disproved long ago. It builds flavour, which is a better reason.",
            "Caramelisation (sugar alone) and Maillard (sugar plus protein) are different reactions, often happening together.",
        ],
        "quiz": [
            {"q": "The Maillard reaction requires…", "options": ["A wet surface", "A dry surface and high heat", "Low, slow cooking", "Added sugar"], "correct": 1},
            {"q": "Searing meat…", "options": ["Seals in the juices", "Builds flavour through browning", "Cooks it through", "Tenderises the fibres"], "correct": 1},
            {"q": "A crowded pan browns badly because…", "options": ["The pan cools and trapped steam keeps the surface wet", "There is not enough oil", "The food touches", "The heat is too high"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Browning cannot happen while surface water remains because…", "options": ["Water blocks oxygen", "Evaporating water holds the surface near 100°C, below Maillard temperatures", "Water dissolves the proteins", "Steam is too cold"], "correct": 1},
            {"q": "Maillard differs from caramelisation in that Maillard involves…", "options": ["Only sugars", "Amino acids reacting with reducing sugars", "Only fats", "Water"], "correct": 1},
            {"q": "Salting meat well ahead of searing helps because…", "options": ["It draws out moisture that then evaporates, and the surface dries", "It lowers the cooking temperature", "It prevents sticking", "It adds sugar"], "correct": 0},
        ],
    },
    {
        "slug": "heat-sear", "branch": "heat", "title": "Sear & Sauté", "icon": "🍤",
        "req_tier": 3, "est_min": 20,
        "summary": "Dry the surface, trust the crust, then turn the stuck-on bits into a sauce.",
        "intro": (
            "Sautéing is fast cooking in a little fat over high heat, with the food moving. Searing is the "
            "opposite: high heat with the food perfectly still. Both end with fond — the browned residue on "
            "the pan — which is the free sauce most people wash down the sink."
        ),
        "steps": [
            "Pat dry, season, and heat the pan until the oil shimmers.",
            "Lay the food away from you and do not move it until it releases cleanly from the pan.",
            "Flip once, finish the second side, and rest the food on a rack rather than a plate.",
            "Pour off excess fat, leaving the browned fond behind.",
            "Deglaze with wine, stock or even water, scraping the fond loose as the liquid bubbles.",
            "Reduce, then finish off the heat with a knob of cold butter swirled in to thicken and gloss the sauce.",
        ],
        "tips": [
            "Resting on a plate steams the crust you just made; a rack keeps it crisp.",
            "Deglaze while the pan is still hot — cold fond is stubborn.",
        ],
        "quiz": [
            {"q": "The browned bits stuck to the pan are called…", "options": ["Fond", "Roux", "Slurry", "Curd"], "correct": 0},
            {"q": "Before searing, the surface of the meat should be…", "options": ["Wet", "Patted dry", "Frozen solid", "Heavily oiled"], "correct": 1},
            {"q": "Finishing a pan sauce with cold butter off the heat…", "options": ["Thickens and glosses it", "Makes it thinner", "Cools it for serving", "Removes the salt"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Adding butter off the heat rather than on it matters because…", "options": ["Butter burns easily", "The emulsion breaks if it gets too hot", "It melts faster", "It reduces the sauce"], "correct": 1},
            {"q": "Resting meat on a rack rather than a plate keeps the crust crisp because…", "options": ["It cools faster", "Escaping steam is not trapped underneath", "The rack absorbs fat", "It drains the juices"], "correct": 1},
            {"q": "Pouring off excess fat before deglazing matters because…", "options": ["Fat prevents fond dissolving and leaves the sauce greasy", "Fat burns", "It saves calories", "Fat neutralises the acid"], "correct": 0},
        ],
    },
    {
        "slug": "heat-roasting", "branch": "heat", "title": "Roasting & Carryover", "icon": "🔆",
        "req_tier": 5, "est_min": 25,
        "summary": "Ovens lie, thermometers don't. Cook to temperature, pull early, let the stored heat finish the job.",
        "intro": (
            "The single biggest upgrade to roasting is a probe thermometer. Time-based recipes assume your "
            "oven, your pan and your piece of meat — three things they cannot know. Temperature is the only "
            "honest measure of doneness, and it keeps rising after you take the food out."
        ),
        "steps": [
            "Bring large cuts closer to room temperature before roasting so the outside is not overcooked before the centre is done.",
            "Use a hot oven for browning and a moderate one for even cooking; combine the two by starting hot and dropping the temperature.",
            "Probe the thickest part, away from bone, and trust the number over the clock.",
            "Pull the meat 3–8°C below your target — the bigger the cut, the bigger the carryover.",
            "Rest it: a large roast needs twenty minutes or more, a steak five to ten.",
            "Keep an oven thermometer inside; most domestic ovens run 10–20°C off their dial.",
        ],
        "tips": [
            "Tent loosely with foil while resting — sealing it tight steams the crust.",
            "The juices that run out onto the board belong in the sauce, not in the bin.",
        ],
        "quiz": [
            {"q": "Carryover cooking means food…", "options": ["Stops the moment it leaves the heat", "Keeps cooking after you remove the heat", "Only cooks in the oven", "Cooks twice as fast"], "correct": 1},
            {"q": "You should pull a roast from the oven…", "options": ["Exactly at target temperature", "A few degrees below target", "Well above target", "When the timer ends"], "correct": 1},
            {"q": "Resting meat mainly…", "options": ["Cools it for safety", "Lets the temperature even out and juices redistribute", "Adds flavour", "Firms the crust"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "Carryover is greater in a large roast than in a steak because…", "options": ["Large cuts are fattier", "More stored heat flows inward from a thicker exterior", "Ovens are hotter for roasts", "Steaks rest longer"], "correct": 1},
            {"q": "Starting hot then dropping the oven temperature gives you…", "options": ["Faster cooking only", "Browning on the outside with a more even interior", "Less carryover", "A crisper rest"], "correct": 1},
            {"q": "Tenting loosely rather than wrapping tightly during resting…", "options": ["Keeps it hotter", "Lets steam escape so the crust stays crisp", "Speeds up carryover", "Prevents juices escaping"], "correct": 1},
        ],
    },
    {
        "slug": "heat-braise", "branch": "heat", "title": "Braising & Collagen", "icon": "🍖",
        "req_tier": 7, "est_min": 30,
        "summary": "Low, slow, and partly submerged — how the toughest cuts become the best ones.",
        "intro": (
            "Tough cuts are tough because they are full of collagen, the connective tissue of hard-working "
            "muscle. Held long enough at the right temperature with moisture present, that collagen becomes "
            "gelatine — which is why a braise is both tender and silky, while a lean cut cooked the same way is dry."
        ),
        "steps": [
            "Choose a working muscle: shoulder, shin, cheek, oxtail. Lean cuts have nothing to convert.",
            "Brown the meat thoroughly first, in batches, and build fond in the pot.",
            "Sweat aromatics in the same pot, then deglaze so nothing browned is left behind.",
            "Add liquid to come roughly halfway up the meat — a braise is not a boil.",
            "Hold it at a bare simmer, in the oven or on the lowest burner, for several hours.",
            "Cool the braise in its liquid, then skim the set fat from the top before reheating and serving.",
        ],
        "tips": [
            "A braise is almost always better the next day: the meat reabsorbs liquid as it cools.",
            "If it is boiling hard, the meat fibres squeeze and the result is stringy — turn it down.",
        ],
        "quiz": [
            {"q": "Braising turns collagen into…", "options": ["Gelatine", "Protein", "Starch", "Fat"], "correct": 0},
            {"q": "The right cut for braising is…", "options": ["Lean tenderloin", "A hard-working muscle like shoulder or shin", "Breast meat", "Any cut"], "correct": 1},
            {"q": "The liquid in a braise should…", "options": ["Cover the meat completely", "Come roughly halfway up", "Barely wet the base", "Be added at the end"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "A braise held at a hard boil turns stringy because…", "options": ["Collagen is destroyed", "Muscle fibres contract and squeeze out moisture faster than collagen converts", "The liquid evaporates", "Gelatine breaks down"], "correct": 1},
            {"q": "Cooling a braise in its liquid overnight improves it because…", "options": ["The flavour concentrates", "The meat reabsorbs gelatine-rich liquid as it cools, and fat sets for easy skimming", "It ferments slightly", "The collagen keeps converting"], "correct": 1},
            {"q": "A lean cut braised for hours ends up dry because…", "options": ["It cooks faster", "It has little collagen to become gelatine, so lost moisture is never compensated", "It absorbs no liquid", "It browns too much"], "correct": 1},
        ],
    },
    {
        "slug": "heat-precision", "branch": "heat", "title": "Temperature Precision", "icon": "🌡️",
        "req_tier": 9, "est_min": 25,
        "summary": "Doneness is a temperature, not a time. Sous-vide, reverse sears and the logic behind both.",
        "intro": (
            "Every texture you want in a protein corresponds to a temperature at which specific proteins "
            "denature. Once you think in temperatures rather than minutes, techniques that look exotic — "
            "sous-vide, reverse searing, low-temperature eggs — turn out to be the same simple idea."
        ),
        "steps": [
            "Learn the landmarks: myosin sets around 50°C, collagen begins converting near 60°C and accelerates higher, and most proteins are fully firm past 70°C.",
            "Hold food at your target temperature and it cannot overshoot — the water bath or low oven is the thermostat.",
            "Reverse sear by cooking low until the centre is a few degrees under target, then searing hard and fast at the end.",
            "Remember that time at temperature, not just temperature, determines pasteurisation and tenderness.",
            "Dry the surface thoroughly before the final sear; food out of a bag or a humid oven is wet.",
            "Rest is minimal after a reverse sear — the gradient inside the meat is already gentle.",
        ],
        "tips": [
            "Thicker food needs longer to reach temperature but does not need a higher temperature.",
            "A cheap probe thermometer teaches you more about your oven than any recipe.",
        ],
        "quiz": [
            {"q": "Reverse searing means…", "options": ["Searing first, then cooking low", "Cooking low first, then searing at the end", "Searing twice", "Never searing"], "correct": 1},
            {"q": "Holding food in a water bath at target temperature means it…", "options": ["Cannot overcook past that temperature", "Cooks faster", "Needs no resting ever", "Browns automatically"], "correct": 0},
            {"q": "Before the final sear, food from a bath must be…", "options": ["Chilled", "Dried thoroughly", "Salted heavily", "Rested"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "Food safety in low-temperature cooking depends on…", "options": ["Temperature alone", "Time held at a given temperature", "The bag used", "Salt content"], "correct": 1},
            {"q": "A reverse-seared steak needs little resting because…", "options": ["It is cooked longer", "The internal temperature gradient is already shallow", "It contains less water", "It was seared hot"], "correct": 1},
            {"q": "A steak held at 55°C for hours becomes more tender without becoming more done because…", "options": ["Water is absorbed", "Collagen slowly converts while the muscle proteins stay at the same doneness", "Fat renders fully", "Salt penetrates"], "correct": 1},
        ],
    },
]
