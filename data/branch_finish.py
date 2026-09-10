# -*- coding: utf-8 -*-
"""Stocks & Soups (5) și Plating & Pastry (6) — ramurile care închid arborele."""

LESSONS = [
    # ================= STOCKS & SOUPS =================
    {
        "slug": "stock-basics", "branch": "stock", "title": "Stock Fundamentals", "icon": "🍲",
        "req_tier": 2, "est_min": 25,
        "summary": "Bones, water, patience and a temperature that never reaches a boil.",
        "intro": (
            "Stock is the cheapest upgrade in cooking: the bones are nearly free and the technique is mostly "
            "waiting. The single rule that separates good stock from bad is temperature — a stock that boils "
            "turns cloudy and greasy, and no amount of straining fixes it."
        ),
        "steps": [
            "Use bones with joints and connective tissue; those give gelatine, and gelatine gives body.",
            "Cover with cold water and bring up slowly — starting cold draws more out of the bones.",
            "Skim the grey scum that rises during the first twenty minutes and discard it.",
            "Add aromatics later rather than at the start; they need an hour, not six.",
            "Hold at a bare tremble for several hours, never letting it boil.",
            "Strain gently without pressing the solids, cool quickly, and chill so the fat sets for easy removal.",
        ],
        "tips": [
            "Never salt a stock. You do not yet know what it will become, and reduction will concentrate it.",
            "Good stock sets to a wobble in the fridge. If yours stays liquid, use more jointed bones next time.",
        ],
        "quiz": [
            {"q": "Stock should be cooked at…", "options": ["A rolling boil", "A bare tremble", "A hard simmer", "Room temperature"], "correct": 1},
            {"q": "You should start stock with…", "options": ["Cold water", "Boiling water", "Hot stock", "Warm broth"], "correct": 0},
            {"q": "Stock should be salted…", "options": ["Heavily at the start", "Not at all — season the final dish", "Halfway through", "After straining"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "Boiling makes stock cloudy because it…", "options": ["Emulsifies fat and breaks proteins into suspension", "Adds air", "Dissolves the bones", "Concentrates salt"], "correct": 0},
            {"q": "Stock that sets to a wobble when chilled is rich in…", "options": ["Gelatine from collagen", "Fat", "Salt", "Starch"], "correct": 0},
            {"q": "Pressing the solids while straining is avoided because it…", "options": ["Forces fine particles through and clouds the stock", "Wastes stock", "Cools it", "Adds bitterness only"], "correct": 0},
        ],
    },
    {
        "slug": "stock-brown", "branch": "stock", "title": "Brown Stock & Demi", "icon": "🦴",
        "req_tier": 4, "est_min": 30,
        "summary": "Roast first, then simmer. The deep, dark base under classical sauces.",
        "intro": (
            "White stock is bones and water. Brown stock is the same bones roasted hard first, which layers "
            "Maillard flavour on top of the gelatine. Reduce it far enough and it becomes a glaze intense "
            "enough to season a whole dish with a spoonful."
        ),
        "steps": [
            "Roast the bones at high heat until deeply coloured — pale bones give pale stock.",
            "Roast the aromatics separately or add them partway, so they colour without burning.",
            "Deglaze the roasting tray and add every scraped-up bit to the pot; that is where the flavour is.",
            "Add a small amount of tomato paste, cooked until it darkens, for depth and colour.",
            "Simmer gently for many hours, skimming as needed.",
            "Strain, degrease and reduce to your target: a sauce base, a demi-glace, or a glossy glace.",
        ],
        "tips": [
            "Burnt bones taste burnt, not deep. Dark brown is the target, black is a mistake.",
            "Freeze reduced stock in an ice tray — each cube is an instant sauce base.",
        ],
        "quiz": [
            {"q": "Brown stock differs from white stock because the bones are…", "options": ["Roasted first", "Boiled harder", "Soaked overnight", "Salted"], "correct": 0},
            {"q": "Tomato paste is cooked until it darkens in order to…", "options": ["Add depth and colour", "Thicken the stock", "Reduce acidity only", "Preserve it"], "correct": 0},
            {"q": "The roasting tray should be…", "options": ["Deglazed and added to the pot", "Washed immediately", "Discarded", "Reused unwashed"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "A glace is stock reduced until it…", "options": ["Becomes a syrupy, intensely flavoured glaze that sets solid when cold", "Doubles in volume", "Turns clear", "Loses its gelatine"], "correct": 0},
            {"q": "Demi-glace traditionally combines brown stock with…", "options": ["A brown sauce base, reduced together", "Cream", "Butter only", "White wine only"], "correct": 0},
            {"q": "Over-roasted, blackened bones ruin a stock because…", "options": ["Pyrolysis products taste acrid and cannot be simmered out", "They release no gelatine", "They absorb water", "They float"], "correct": 0},
        ],
        "extra": ["heat-maillard"],
    },
    {
        "slug": "stock-soup", "branch": "stock", "title": "Building a Soup", "icon": "🥣",
        "req_tier": 5, "est_min": 25,
        "summary": "Layering a soup so it tastes like one dish rather than things floating in water.",
        "intro": (
            "Most disappointing soups are under-built rather than under-seasoned: the ingredients were added "
            "at once and simmered together. Layering means each element gets the treatment it needs before "
            "the liquid arrives."
        ),
        "steps": [
            "Sweat the aromatic base slowly in fat until soft and sweet, without colouring it.",
            "Brown any protein separately and build fond, then deglaze into the pot.",
            "Bloom spices and tomato paste in the fat before liquid goes in.",
            "Add stock rather than water wherever possible, and add ingredients in order of cooking time.",
            "Simmer only as long as the slowest ingredient needs; anything longer turns everything to mush.",
            "Finish with acid, fresh herbs and fat — the three things that make a soup taste alive.",
        ],
        "tips": [
            "A soup that tastes flat after long simmering usually needs acid, not salt.",
            "Add delicate greens and herbs off the heat; residual warmth is enough to wilt them.",
        ],
        "quiz": [
            {"q": "The aromatic base of a soup should be…", "options": ["Sweated slowly without colouring", "Browned hard", "Boiled", "Added last"], "correct": 0},
            {"q": "Ingredients should be added…", "options": ["All at once", "In order of cooking time", "Only at the end", "After the soup is blended"], "correct": 1},
            {"q": "A long-simmered soup that tastes flat most often needs…", "options": ["Acid", "More simmering", "More water", "More protein"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Blooming spices in fat before adding liquid works because their flavour compounds are…", "options": ["Fat-soluble", "Water-soluble", "Destroyed by water", "Volatile only when cold"], "correct": 0},
            {"q": "Simmering a soup past the slowest ingredient's cooking time…", "options": ["Degrades the texture of everything else without adding flavour", "Improves the flavour indefinitely", "Concentrates the stock usefully", "Sets the starch"], "correct": 0},
            {"q": "Finishing with fat — oil, butter, cream — improves a soup because fat…", "options": ["Carries aroma compounds and gives body on the palate", "Thickens it chemically", "Removes acidity", "Adds salt"], "correct": 0},
        ],
    },
    {
        "slug": "stock-consomme", "branch": "stock", "title": "Clarification & Consommé", "icon": "🍵",
        "req_tier": 9, "est_min": 35,
        "summary": "A raft of egg white that filters a cloudy stock into something you can read print through.",
        "intro": (
            "Consommé is the technical showpiece of classical soup work: a stock so clear it looks like tea "
            "and so concentrated it tastes like the concentrated essence of its ingredients. The clarification "
            "raft does the filtering, and the rule is that you must not disturb it."
        ),
        "steps": [
            "Start with a cold, well-made, fully degreased stock — clarification cannot rescue a bad one.",
            "Whisk egg whites with minced lean meat and finely chopped aromatics to form the clarification mixture.",
            "Stir it into the cold stock, then heat slowly while stirring until it begins to set.",
            "Stop stirring the moment the raft forms and floats.",
            "Make a small vent hole in the raft and hold the pot at the barest simmer for around an hour.",
            "Ladle the clear liquid out gently through the vent and strain through fine cloth; season only at the end.",
        ],
        "tips": [
            "Never let a consommé boil once the raft has formed — it will break up and cloud the whole pot.",
            "The raft is spent flavour, not waste to eat. Discard it once you have your consommé.",
        ],
        "quiz": [
            {"q": "The raft in a consommé is made mainly from…", "options": ["Egg whites and lean meat", "Flour and butter", "Gelatine", "Cream"], "correct": 0},
            {"q": "Once the raft has formed you should…", "options": ["Stop stirring", "Stir more vigorously", "Increase to a boil", "Cover tightly"], "correct": 0},
            {"q": "Consommé should be seasoned…", "options": ["At the end", "Before clarifying", "Never", "While stirring the raft"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "The raft clarifies stock because coagulating egg proteins…", "options": ["Trap suspended particles as they rise through the liquid", "Dissolve the impurities", "Absorb fat only", "Add gelatine"], "correct": 0},
            {"q": "Boiling breaks a consommé because…", "options": ["Turbulence tears the raft and redistributes trapped particles", "The proteins dissolve", "Fat melts", "Gelatine breaks down"], "correct": 0},
            {"q": "Starting with cold stock matters because the clarification mixture must…", "options": ["Disperse fully before the proteins begin to set", "Be sterilised", "Dissolve the gelatine", "Absorb salt"], "correct": 0},
        ],
    },
    {
        "slug": "stock-global", "branch": "stock", "title": "Broths Around the World", "icon": "🌍",
        "req_tier": 11, "est_min": 30,
        "summary": "Dashi, tonkotsu, pho, bouillon — different rules, and why each one breaks the previous lesson.",
        "intro": (
            "Classical French stock technique is one tradition among many, and several of the world's great "
            "broths deliberately violate its rules. Tonkotsu is boiled hard on purpose; dashi is made in "
            "minutes. Knowing why makes both techniques usable rather than contradictory."
        ),
        "steps": [
            "Make dashi in under twenty minutes: steep kombu in water below a simmer, remove it, then briefly infuse katsuobushi.",
            "Never boil kombu — it turns slimy and bitter, and its glutamate is already extracted at low heat.",
            "Understand tonkotsu: a hard rolling boil for many hours deliberately emulsifies fat and collagen into an opaque, rich broth.",
            "Build pho by charring onion and ginger first, then simmering gently with whole spices, and skimming meticulously for clarity.",
            "Recognise the pattern: clarity and emulsification are opposite goals, and boiling is the switch between them.",
            "Season each in its own idiom — soy and mirin, salt and tare, or fish sauce and lime.",
        ],
        "tips": [
            "Dashi proves that long cooking is not the same as deep flavour. Umami extraction is fast.",
            "Every rule in cooking is a rule about a goal. Change the goal and the rule inverts.",
        ],
        "quiz": [
            {"q": "Kombu should be…", "options": ["Steeped below a simmer and removed before boiling", "Boiled hard for an hour", "Roasted first", "Fermented"], "correct": 0},
            {"q": "Tonkotsu broth is boiled hard in order to…", "options": ["Emulsify fat and collagen into an opaque broth", "Clarify it", "Speed it up only", "Remove fat"], "correct": 0},
            {"q": "Onion and ginger for pho are…", "options": ["Charred first", "Added raw at the end", "Boiled separately", "Omitted"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Dashi extracts deep savouriness in minutes because kombu and katsuobushi are…", "options": ["Already concentrated sources of glutamate and inosinate", "Boiled hard", "Fermented in the pot", "High in gelatine"], "correct": 0},
            {"q": "Glutamate and inosinate together taste far more savoury than either alone because they…", "options": ["Act synergistically on umami receptors", "Add saltiness", "Cancel bitterness", "Thicken the broth"], "correct": 0},
            {"q": "The technique difference between consommé and tonkotsu comes down to…", "options": ["Whether you want particles filtered out or emulsified in", "The bones used", "Cooking time only", "The seasoning"], "correct": 0},
        ],
    },

    # ================= PLATING & PASTRY =================
    {
        "slug": "plate-balance", "branch": "plate", "title": "Balancing a Plate", "icon": "🍽️",
        "req_tier": 5, "est_min": 20,
        "summary": "Texture, temperature, acid and richness — the four checks before food leaves the kitchen.",
        "intro": (
            "A dish can be technically perfect and still boring. What makes a plate satisfying is contrast: "
            "something crisp against something soft, something sharp against something rich. Run the same "
            "four checks every time and dull dishes become rare."
        ),
        "steps": [
            "Check texture: if everything on the plate is soft, add something crisp.",
            "Check acid: richness without acid feels heavy after three bites.",
            "Check temperature: a cold element against a hot one wakes up a plate.",
            "Check seasoning last, on the composed dish rather than on each component alone.",
            "Cut the number of components rather than adding more; three things done well beat six done adequately.",
            "Taste a full forkful the way a diner would eat it, not each element separately.",
        ],
        "tips": [
            "If a dish needs a sauce to be edible, the dish is not finished. Sauce should add, not rescue.",
            "Salt on the finished plate — a flaky finishing salt — reads completely differently from salt cooked in.",
        ],
        "quiz": [
            {"q": "A plate where everything is soft most needs…", "options": ["A crisp element", "More sauce", "More salt", "More heat"], "correct": 0},
            {"q": "Richness on a plate is best balanced by…", "options": ["Acid", "More fat", "Sugar", "Heat"], "correct": 0},
            {"q": "Final seasoning should be judged…", "options": ["On the composed dish", "On each component alone", "Before cooking", "Never"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Acid makes rich food feel lighter because it…", "options": ["Stimulates salivation and cuts the coating sensation of fat", "Dissolves the fat", "Lowers the temperature", "Reduces salt perception"], "correct": 0},
            {"q": "Tasting a full forkful rather than each component separately matters because…", "options": ["Balance exists in the combination, not in the parts", "It is faster", "Components taste the same", "It uses less food"], "correct": 0},
            {"q": "Finishing salt reads differently from salt cooked in because it…", "options": ["Dissolves on the tongue in bursts rather than being evenly dispersed", "Is chemically different", "Is stronger", "Is saltier per gram"], "correct": 0},
        ],
        "extra": ["sauce-emulsion"],
    },
    {
        "slug": "plate-composition", "branch": "plate", "title": "Composition & Height", "icon": "🎨",
        "req_tier": 6, "est_min": 20,
        "summary": "Where things go on the plate, and why negative space does more work than garnish.",
        "intro": (
            "Plating is not decoration, it is direction: you are telling the diner where to start and what to "
            "eat together. The most common mistake is filling the plate. Space around food reads as "
            "confidence, and it makes what is there look deliberate."
        ),
        "steps": [
            "Choose the plate before the arrangement; a rim frames the food and a large plate creates space.",
            "Anchor the main element off-centre rather than dead centre, and build around it.",
            "Give the composition height in one place — flat food reads as unfinished.",
            "Keep sauce deliberate: a pool, a swipe or dots, but not a flood over everything.",
            "Use garnish that belongs to the dish and can be eaten, never decoration for its own sake.",
            "Wipe the rim before it goes out. Every time.",
        ],
        "tips": [
            "Odd numbers of elements look more natural than even ones.",
            "If you cannot explain why something is on the plate, take it off.",
        ],
        "quiz": [
            {"q": "Negative space on a plate…", "options": ["Makes the composition look deliberate", "Looks like a mistake", "Should always be filled", "Only matters in restaurants"], "correct": 0},
            {"q": "Garnish should be…", "options": ["Edible and part of the dish", "Purely decorative", "As large as possible", "Always green"], "correct": 0},
            {"q": "Height on a plate…", "options": ["Gives the composition structure", "Should be avoided", "Only works with dessert", "Makes food cold"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Odd numbers of elements look more natural because…", "options": ["The eye does not pair them symmetrically and keeps moving", "They are easier to count", "They fill more space", "They are traditional"], "correct": 0},
            {"q": "Plating off-centre works because it…", "options": ["Creates asymmetry that leads the eye rather than freezing it", "Fits more food", "Keeps food hotter", "Uses smaller plates"], "correct": 0},
            {"q": "Flooding a plate with sauce weakens a dish because it…", "options": ["Removes contrast and makes every bite identical", "Cools the food", "Adds too much salt", "Hides the plate"], "correct": 0},
        ],
    },
    {
        "slug": "plate-doughs", "branch": "plate", "title": "Sweet Doughs & Creams", "icon": "🍮",
        "req_tier": 8, "est_min": 30,
        "summary": "Pâte sucrée, crème pâtissière, choux — the pastry building blocks that combine into everything.",
        "intro": (
            "Most classical desserts are a small number of components assembled in different ways. Learn a "
            "sweet pastry, a pastry cream and choux paste, and a very large part of the pâtisserie repertoire "
            "becomes available as combinations rather than as new recipes."
        ),
        "steps": [
            "Make pâte sucrée by creaming butter and sugar first, then adding egg and flour — this limits gluten and gives a short, crisp shell.",
            "Rest, roll cold, line the tin without stretching, and blind bake with weights until fully coloured.",
            "For crème pâtissière, cook a custard with starch to a full boil so the starch gelatinises and the yolk enzyme is destroyed.",
            "Chill pastry cream with film on the surface, then whisk smooth before using it.",
            "For choux, cook the paste on the heat to dry it, then beat in eggs a little at a time until it drops in a V from the spatula.",
            "Bake choux hot at first to build steam, then lower the heat to dry the shells so they do not collapse.",
        ],
        "tips": [
            "A pastry cream that goes runny hours later usually was not boiled long enough to kill the starch-digesting enzyme in the yolks.",
            "Do not open the oven while choux is rising. The escaping steam is the thing lifting them.",
        ],
        "quiz": [
            {"q": "Crème pâtissière must be brought to…", "options": ["A full boil", "80°C only", "Room temperature", "A simmer for seconds"], "correct": 0},
            {"q": "Choux paste is ready when it…", "options": ["Drops in a V from the spatula", "Pours like batter", "Forms a stiff ball that will not move", "Is completely smooth and runny"], "correct": 0},
            {"q": "Pâte sucrée starts by…", "options": ["Creaming butter and sugar", "Rubbing cold butter into flour", "Melting butter", "Boiling sugar"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Pastry cream must be boiled because heat destroys…", "options": ["Alpha-amylase in the yolks, which would otherwise break the starch down", "The sugar", "The starch itself", "The dairy proteins"], "correct": 0},
            {"q": "Drying the choux paste on the heat before adding eggs…", "options": ["Removes water so the paste can absorb more egg, giving a better rise", "Cooks the flour for flavour only", "Melts the butter", "Prevents browning"], "correct": 0},
            {"q": "Choux shells collapse after baking when they are…", "options": ["Removed before the structure has dried and set", "Baked too hot throughout", "Piped too small", "Over-egged only"], "correct": 0},
        ],
        "extra": ["eggs-custard"],
    },
    {
        "slug": "plate-chocolate", "branch": "plate", "title": "Chocolate & Tempering", "icon": "🍫",
        "req_tier": 10, "est_min": 30,
        "summary": "Six crystal forms, one you want. Temperature curves, snap and shine.",
        "intro": (
            "Cocoa butter can crystallise in several different forms, and only one of them gives chocolate "
            "its snap, gloss and clean melt. Tempering is the process of encouraging that form and "
            "eliminating the others — which is why it is entirely a matter of temperature control."
        ),
        "steps": [
            "Melt the chocolate gently to around 45–50°C, so all existing crystal forms are erased.",
            "Cool it while agitating — over a cold bath or by seeding with tempered chocolate — to encourage the stable form.",
            "Bring dark chocolate down to about 28–29°C, then rewarm to roughly 31–32°C for working.",
            "Use lower working temperatures for milk and white chocolate, which contain more milk fat.",
            "Test on a knife or parchment: properly tempered chocolate sets within minutes with a glossy surface.",
            "Keep the working bowl at temperature and stir regularly; chocolate falls out of temper as it cools.",
        ],
        "tips": [
            "Even a drop of water will seize melted chocolate. Everything must be bone dry.",
            "Dull, streaky chocolate with white bloom is untempered or badly stored, not spoiled — you can remelt and start again.",
        ],
        "quiz": [
            {"q": "Tempering chocolate controls…", "options": ["Which cocoa butter crystal form dominates", "The sugar content", "The cocoa percentage", "The milk solids"], "correct": 0},
            {"q": "Properly tempered dark chocolate is worked at roughly…", "options": ["31–32°C", "45°C", "20°C", "60°C"], "correct": 0},
            {"q": "A drop of water in melted chocolate will…", "options": ["Seize it into a grainy mass", "Thin it", "Improve the shine", "Do nothing"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "The desirable cocoa butter crystal form is favoured by…", "options": ["Cooling with agitation, then holding just below the melting point of unstable forms", "Rapid chilling", "Slow melting only", "High heat"], "correct": 0},
            {"q": "Fat bloom appears on chocolate when…", "options": ["Unstable crystals migrate to the surface, often after temperature swings", "It absorbs water", "Sugar recrystallises", "It is too old to eat"], "correct": 0},
            {"q": "Water seizes chocolate because it…", "options": ["Makes the sugar and cocoa particles clump into a paste", "Cools it too fast", "Dissolves the cocoa butter", "Adds air"], "correct": 0},
        ],
    },
    {
        "slug": "plate-sugar", "branch": "plate", "title": "Sugar Work", "icon": "🍯",
        "req_tier": 12, "est_min": 35,
        "summary": "Caramel, hard crack and the stages of sugar — where a thermometer stops being optional.",
        "intro": (
            "Boiling sugar syrup passes through defined stages as water leaves it, and each stage has a "
            "temperature and a use. It is also the most dangerous thing in a domestic kitchen: caramel is "
            "far hotter than boiling water and it sticks to skin."
        ),
        "steps": [
            "Learn the landmarks: soft ball around 115°C for fudge and buttercream, hard crack around 150°C for brittle, caramel from about 160°C.",
            "Use a clean, heavy pan and do not stir once the sugar has dissolved — stirring encourages crystallisation.",
            "Brush the sides of the pan with water, or add a little glucose or acid, to prevent stray crystals seeding the syrup.",
            "Watch the colour closely past 160°C; caramel goes from amber to burnt in seconds.",
            "Stop the cooking by plunging the pan base into water, or by adding cream or butter carefully at arm's length.",
            "Keep a bowl of iced water beside you — sugar burns are serious and immediate cooling matters.",
        ],
        "tips": [
            "Adding cream to hot caramel erupts violently. Warm the cream first and add it slowly, off the heat.",
            "Crystallised syrup can be rescued: add water, redissolve completely, and start the boil again.",
        ],
        "quiz": [
            {"q": "Hard crack stage is around…", "options": ["150°C", "100°C", "115°C", "200°C"], "correct": 0},
            {"q": "Stirring sugar syrup after it dissolves…", "options": ["Encourages unwanted crystallisation", "Cools it evenly", "Prevents burning", "Is required"], "correct": 0},
            {"q": "Cream added to hot caramel should be…", "options": ["Warmed and added slowly off the heat", "Cold and added fast", "Whipped first", "Added at hard crack"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Sugar syrup temperature indicates the stage because it tracks…", "options": ["The remaining water content of the syrup", "The sugar type", "The pan material", "The stirring speed"], "correct": 0},
            {"q": "Glucose or an acid is added to sugar syrup to…", "options": ["Interfere with sucrose crystal formation", "Lower the boiling point", "Add sweetness", "Speed the boil"], "correct": 0},
            {"q": "Caramel burns are more severe than boiling water burns because caramel…", "options": ["Is far hotter and adheres to skin instead of running off", "Is acidic", "Contains sugar", "Cools slower only"], "correct": 0},
        ],
    },
    {
        "slug": "plate-signature", "branch": "plate", "title": "Building a Signature Dish", "icon": "👑",
        "req_tier": 14, "est_min": 45,
        "summary": "The capstone: take everything in this tree and make one dish that is unmistakably yours.",
        "intro": (
            "A signature dish is not the most complicated thing you can cook — it is the dish you can cook "
            "identically every time, that says something specific, and that you would be happy to be judged "
            "on. Building one is a process of subtraction more than addition."
        ),
        "steps": [
            "Start from an idea, not a technique: a memory, an ingredient at its peak, a combination you keep returning to.",
            "Draft the dish with more components than you need, then cook it and remove whatever does not earn its place.",
            "Fix the specification — weights, temperatures, timings — so it is reproducible rather than lucky.",
            "Cook it for people who will tell you the truth, and take notes on what they eat last.",
            "Run the balance checks: texture, acid, temperature, seasoning, and one clear focal point.",
            "Cook it ten more times. Consistency, not novelty, is what makes a dish a signature.",
        ],
        "tips": [
            "The dish is finished when removing anything else would make it worse. Not before.",
            "Write the recipe down properly. A signature dish you cannot hand to someone else is only half a dish.",
        ],
        "quiz": [
            {"q": "A signature dish is defined mainly by…", "options": ["Reproducibility and a clear point of view", "Complexity", "Number of components", "Expensive ingredients"], "correct": 0},
            {"q": "The drafting process should mostly involve…", "options": ["Removing components that do not earn their place", "Adding more elements", "Increasing portion size", "Adding more sauce"], "correct": 0},
            {"q": "A dish is finished when…", "options": ["Removing anything else would make it worse", "The plate is full", "It has five components", "It takes three hours"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Fixing weights, temperatures and timings matters because…", "options": ["It converts a good result into a repeatable one", "It speeds up cooking", "It reduces cost", "It impresses diners"], "correct": 0},
            {"q": "Watching what people eat last on the plate tells you…", "options": ["Which component is weakest or least appealing", "How hungry they are", "Whether it is hot enough", "The portion size"], "correct": 0},
            {"q": "Consistency matters more than novelty in a signature dish because…", "options": ["A dish that varies between services cannot build a reputation", "Novelty is undesirable", "It costs less", "It is faster to plate"], "correct": 0},
        ],
        "extra": ["bake-sourdough", "stock-consomme", "heat-precision"],
    },
]
