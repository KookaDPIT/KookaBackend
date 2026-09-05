# -*- coding: utf-8 -*-
"""Eggs & Dairy (6) și Sauces & Emulsions (7).

`extra` leagă ramurile între ele: emulsiile cer și control termic, și ouă.
"""

LESSONS = [
    # ================= EGGS & DAIRY =================
    {
        "slug": "eggs-boiled", "branch": "eggs", "title": "Boiled & Poached", "icon": "🥚",
        "req_tier": 1, "est_min": 15,
        "summary": "One pot, one timer, total control over the yolk — plus the trick that makes poaching easy.",
        "intro": (
            "A boiled egg is a clock problem, and the clock only works if the starting conditions are the "
            "same every time. Lower eggs into already-boiling water rather than starting them cold, and "
            "suddenly your seven minutes means the same thing every morning."
        ),
        "steps": [
            "Bring water to a rolling boil, then lower eggs in on a spoon and immediately reduce to a steady simmer.",
            "Time from the moment they go in: roughly 6 minutes for a runny yolk, 8 for jammy, 10–11 for firm.",
            "Move them straight into iced water to stop the cooking and make peeling far easier.",
            "For poaching, use the freshest eggs you can — old whites spread into rags.",
            "Add a splash of vinegar to the poaching water and strain the egg through a sieve first to remove the loose outer white.",
            "Poach at a bare tremble, never a boil, for about three minutes.",
        ],
        "tips": [
            "Slightly older eggs peel more easily after boiling; fresher eggs poach better. Buy for the job.",
            "A grey-green ring around the yolk means overcooked — harmless, but it is a timer telling you something.",
        ],
        "quiz": [
            {"q": "Lowering eggs into already-boiling water rather than starting cold gives you…", "options": ["Faster cooking", "A consistent, repeatable timer", "Easier peeling only", "A firmer white"], "correct": 1},
            {"q": "Poaching water should be…", "options": ["At a rolling boil", "At a bare tremble", "Barely warm", "Cold at the start"], "correct": 1},
            {"q": "The best eggs for poaching are…", "options": ["The freshest you can find", "At least three weeks old", "Refrigerated for a month", "It makes no difference"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "The grey-green ring around an overcooked yolk is…", "options": ["Mould", "Iron sulphide formed by overcooking", "Undercooked protein", "Added colouring"], "correct": 1},
            {"q": "Straining a raw egg through a sieve before poaching removes…", "options": ["The yolk membrane", "The loose outer white that turns to rags", "Excess water", "The chalazae"], "correct": 1},
            {"q": "Older eggs peel more easily after boiling because…", "options": ["The shell thins", "The pH of the white rises, weakening its bond to the membrane", "They contain less water", "The yolk shrinks"], "correct": 1},
        ],
    },
    {
        "slug": "eggs-scramble", "branch": "eggs", "title": "The Soft Scramble", "icon": "🍳",
        "req_tier": 2, "est_min": 15,
        "summary": "Low heat, constant motion, and the discipline to stop early.",
        "intro": (
            "Scrambled eggs go from silky to rubbery in about fifteen seconds, and nearly always because the "
            "pan was too hot. Egg proteins set gently below the boiling point of water; anything faster and "
            "they squeeze out their moisture and turn grainy."
        ),
        "steps": [
            "Beat the eggs thoroughly until no streaks of white remain — uneven mixing gives uneven texture.",
            "Melt butter in a non-stick or well-seasoned pan over low heat.",
            "Add the eggs and stir constantly with a spatula, scraping the base as curds start to form.",
            "Keep the curds small and moving; lift the pan off the heat whenever it feels like it is racing away.",
            "Take them off while they still look slightly underdone — carryover finishes them on the plate.",
            "Season at the very end, and add a splash of cream or a cube of cold butter to halt the cooking.",
        ],
        "tips": [
            "Salt added at the start can loosen the curd; salting at the end keeps the texture tight.",
            "If they look wet in the pan, they will be perfect on the plate. If they look perfect in the pan, they are already overcooked.",
        ],
        "quiz": [
            {"q": "For a silky scramble, use…", "options": ["High heat, stir once", "Low heat, stir constantly", "Boiling water", "No stirring at all"], "correct": 1},
            {"q": "You should take scrambled eggs off the heat when they look…", "options": ["Fully set", "Slightly underdone", "Browned", "Dry"], "correct": 1},
            {"q": "Rubbery, weeping scrambled eggs are usually caused by…", "options": ["Too much butter", "Too much heat", "Too much stirring", "Cold eggs"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "Overcooked eggs weep liquid because the proteins…", "options": ["Absorb water", "Coagulate tightly and squeeze water out of the network", "Dissolve", "React with salt"], "correct": 1},
            {"q": "Adding cold butter or cream at the end works because it…", "options": ["Adds flavour only", "Drops the temperature and halts coagulation", "Thickens the eggs", "Emulsifies the yolk"], "correct": 1},
            {"q": "A classic French omelette is pale rather than browned because…", "options": ["It is cooked at low heat, avoiding Maillard browning", "It contains no fat", "It is steamed", "The eggs are older"], "correct": 0},
        ],
    },
    {
        "slug": "eggs-omelette", "branch": "eggs", "title": "The French Omelette", "icon": "🌯",
        "req_tier": 4, "est_min": 20,
        "summary": "Pale, custardy, rolled — the omelette that chefs use as an interview test.",
        "intro": (
            "The French omelette is a test because it hides nothing: no browning to cover unevenness, no "
            "filling to distract. Everything depends on pan control and on stopping a few seconds before "
            "you think you should."
        ),
        "steps": [
            "Beat three eggs until completely uniform, then season lightly.",
            "Melt butter in a small non-stick pan over medium-low heat until it foams but does not colour.",
            "Pour in the eggs and stir rapidly with a fork or spatula while shaking the pan, keeping the curd very fine.",
            "When the mixture is mostly set but still glossy, stop stirring and smooth the surface flat.",
            "Tilt the pan away from you and roll the omelette over on itself from the far side.",
            "Turn it out seam-side down and brush the top with a little butter for shine.",
        ],
        "tips": [
            "A small pan makes a thicker, easier omelette. Three eggs in a large pan is a pancake.",
            "The French omelette should have no colour at all — if it is brown, the heat was too high.",
        ],
        "quiz": [
            {"q": "A classic French omelette should be…", "options": ["Browned and crisp", "Pale and custardy", "Rock hard", "Deep fried"], "correct": 1},
            {"q": "You stop stirring when the eggs are…", "options": ["Fully firm", "Mostly set but still glossy", "Still fully liquid", "Browned underneath"], "correct": 1},
            {"q": "Butter for a French omelette should be heated until it…", "options": ["Foams without colouring", "Browns to a nutty colour", "Smokes", "Separates"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Shaking the pan while stirring produces…", "options": ["A very fine, even curd", "Larger curds", "More browning", "A drier omelette"], "correct": 0},
            {"q": "An omelette rolled while slightly underdone finishes cooking because…", "options": ["The residual heat inside sets the centre", "It is returned to the pan", "The plate is hot", "The butter keeps cooking it"], "correct": 0},
            {"q": "Using too large a pan for three eggs gives you…", "options": ["A thin sheet that overcooks before it can be rolled", "A thicker omelette", "Better browning", "Nothing different"], "correct": 0},
        ],
    },
    {
        "slug": "eggs-custard", "branch": "eggs", "title": "Custards & Curds", "icon": "🍮",
        "req_tier": 6, "est_min": 25,
        "summary": "Tempering, thickening and the narrow temperature window where custard is silk instead of scrambled egg.",
        "intro": (
            "A custard is egg used as a thickener rather than as the dish itself. The whole craft is keeping "
            "the eggs below the point where they set into curds — which means gentle heat, constant movement, "
            "and knowing what to do when it goes wrong."
        ),
        "steps": [
            "Warm the dairy separately with your aromatics — vanilla, citrus zest, spices — and let it infuse.",
            "Whisk yolks with sugar until pale; the sugar physically protects the proteins from setting too fast.",
            "Temper: pour the hot dairy into the yolks in a thin stream while whisking hard, never the reverse.",
            "Return to low heat and stir constantly, scraping the base and corners of the pan.",
            "Cook until it coats the back of a spoon and a drawn finger leaves a clean line — around 80°C, no higher.",
            "Strain immediately into a cold bowl to catch any set bits and to stop the cooking.",
        ],
        "tips": [
            "A splash of cornflour in the yolks makes custard far more forgiving — it raises the temperature at which it curdles.",
            "If it starts to split, blitz it hard with a stick blender straight away; it often comes back.",
        ],
        "quiz": [
            {"q": "Tempering means…", "options": ["Adding hot liquid to eggs slowly while whisking", "Chilling the eggs first", "Boiling the custard hard", "Adding sugar at the end"], "correct": 0},
            {"q": "A stirred custard is done at roughly…", "options": ["60°C", "80°C", "100°C", "120°C"], "correct": 1},
            {"q": "Straining the finished custard is done to…", "options": ["Cool it", "Remove any bits that set", "Add air", "Thicken it"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "Sugar whisked into the yolks makes custard more forgiving because it…", "options": ["Absorbs water", "Raises the temperature at which egg proteins coagulate", "Lowers the boiling point", "Adds acidity"], "correct": 1},
            {"q": "Adding starch to a custard lets you boil it safely because starch…", "options": ["Coats the proteins and inhibits their bonding", "Lowers the temperature", "Removes the yolks", "Adds water"], "correct": 0},
            {"q": "Pouring the yolks into the hot dairy rather than the reverse tends to fail because…", "options": ["The yolks hit high heat all at once and scramble", "The dairy cools too fast", "Sugar burns", "It cannot be whisked"], "correct": 0},
        ],
    },
    {
        "slug": "eggs-cheese", "branch": "eggs", "title": "Cheese & Melting", "icon": "🧀",
        "req_tier": 8, "est_min": 20,
        "summary": "Why some cheeses melt into silk and others split into oil and rubber.",
        "intro": (
            "Melting cheese well is a matter of moisture, age and acidity. Young, moist cheeses flow; hard, "
            "aged ones have lost the water that lets them do so and break instead. A little starch or an "
            "emulsifying salt bridges the gap."
        ),
        "steps": [
            "Choose young, moist cheeses for melting — the aged ones bring flavour but need help.",
            "Grate rather than cube: smaller pieces melt before the ones underneath overheat.",
            "Toss grated cheese with a spoonful of cornflour before melting; the starch keeps the fat and protein together.",
            "Melt over low heat and add the cheese off the heat at the end wherever you can.",
            "Add an acid-and-starch base — a light béchamel — when you want a sauce that will not break on standing.",
            "Never boil a cheese sauce; the proteins tighten and squeeze the fat out.",
        ],
        "tips": [
            "A pinch of sodium citrate turns almost any cheese into a perfectly smooth sauce. It is what makes processed cheese behave.",
            "If a sauce splits, take it off the heat and whisk in a splash of cold liquid to bring it back.",
        ],
        "quiz": [
            {"q": "Tossing grated cheese with cornflour before melting helps because starch…", "options": ["Adds flavour", "Keeps the fat and protein from separating", "Absorbs heat", "Thins the sauce"], "correct": 1},
            {"q": "A cheese sauce splits most often because it was…", "options": ["Boiled", "Under-salted", "Made with young cheese", "Whisked too much"], "correct": 0},
            {"q": "Which melts most smoothly on its own?", "options": ["A young, moist cheese", "A hard aged cheese", "A dried grating cheese", "A blue cheese"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Aged cheeses break rather than melt because they have…", "options": ["Too much salt", "Lost moisture and developed a tighter protein network", "Too much fat", "Higher pH"], "correct": 1},
            {"q": "Sodium citrate works as an emulsifying salt because it…", "options": ["Adds acidity", "Sequesters calcium, letting casein disperse in water", "Thickens the sauce", "Adds sodium"], "correct": 1},
            {"q": "A split cheese sauce can often be rescued by…", "options": ["Boiling harder", "Removing from heat and whisking in cold liquid", "Adding more cheese", "Adding salt"], "correct": 1},
        ],
    },
    {
        "slug": "eggs-souffle", "branch": "eggs", "title": "Meringue & Soufflé", "icon": "🍥",
        "req_tier": 10, "est_min": 30,
        "summary": "Whipping whites into a structure that holds air — and getting it into the oven before it collapses.",
        "intro": (
            "Egg whites can hold many times their volume in air because their proteins unfold and form a "
            "network around the bubbles. Everything that goes wrong with meringue and soufflé comes down to "
            "either fat contaminating that network or over-whipping it until it tears."
        ),
        "steps": [
            "Start with a scrupulously clean, grease-free bowl — any fat, including a speck of yolk, prevents proper foaming.",
            "Whip at medium speed until foamy, then add sugar gradually once soft peaks form.",
            "Stop at firm, glossy peaks that hold their shape; over-whipped whites look grainy and separate.",
            "For a soufflé, fold a quarter of the whites into your flavoured base first to loosen it.",
            "Fold in the rest in two additions with a light cutting-and-turning motion — you are protecting bubbles, not mixing.",
            "Bake immediately in a preheated oven and do not open the door during the rise.",
        ],
        "tips": [
            "Copper or a pinch of cream of tartar stabilises whites and widens the window before over-whipping.",
            "Butter the ramekin in upward strokes and coat with sugar or breadcrumbs — the soufflé climbs the grooves.",
        ],
        "quiz": [
            {"q": "Egg whites fail to whip properly if the bowl contains…", "options": ["Any fat or yolk", "Sugar", "Salt", "Cold air"], "correct": 0},
            {"q": "Sugar should be added to whipping whites…", "options": ["All at the start", "Gradually once soft peaks form", "Only at the very end", "Never"], "correct": 1},
            {"q": "When folding whites into a soufflé base you should first…", "options": ["Fold in all the whites at once", "Loosen the base with a quarter of the whites", "Whisk the base hard", "Chill the base"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "Fat prevents whites from foaming because it…", "options": ["Weighs them down", "Disrupts the protein network forming around air bubbles", "Adds moisture", "Lowers the temperature"], "correct": 1},
            {"q": "Cream of tartar stabilises egg whites by…", "options": ["Adding sugar", "Lowering pH, which slows protein over-bonding", "Absorbing water", "Adding fat"], "correct": 1},
            {"q": "A soufflé rises mainly because…", "options": ["Baking powder reacts", "Trapped air expands and water turns to steam while the proteins set around it", "The whites keep whipping", "Sugar caramelises"], "correct": 1},
        ],
    },

    # ================= SAUCES & EMULSIONS =================
    {
        "slug": "sauce-roux", "branch": "sauce", "title": "Roux & Mother Sauces", "icon": "🥄",
        "req_tier": 3, "est_min": 20,
        "summary": "Flour and fat, cooked to a colour. The base under béchamel, velouté and half of classical cooking.",
        "intro": (
            "A roux is equal parts fat and flour cooked together, and how long you cook it decides two things "
            "at once: how much it tastes of toasted flour, and how little it thickens. Dark roux is delicious "
            "and weak; white roux is bland and powerful."
        ),
        "steps": [
            "Melt butter, whisk in an equal weight of flour, and cook while stirring.",
            "Stop at pale and sandy for béchamel, at blond for velouté, or take it to a nutty brown for darker sauces.",
            "Add your liquid gradually, whisking hard after each addition to keep it lump-free.",
            "Bring to a simmer and hold it there for several minutes — raw flour tastes of raw flour.",
            "Season at the end, once the sauce has reduced to the thickness you want.",
            "Cover the surface directly with film if it must wait, or it will form a skin.",
        ],
        "tips": [
            "Cold liquid into hot roux, or hot liquid into cold roux. Matching temperatures is what causes lumps.",
            "Darker roux thickens less: for the same body you need noticeably more of it.",
        ],
        "quiz": [
            {"q": "A roux is made from…", "options": ["Fat and flour", "Butter and cream", "Egg and oil", "Stock and starch"], "correct": 0},
            {"q": "Compared with a white roux, a dark roux…", "options": ["Thickens more", "Thickens less but tastes richer", "Thickens the same", "Cannot be used in sauces"], "correct": 1},
            {"q": "Lumps in a roux-based sauce usually come from…", "options": ["Adding liquid at the same temperature as the roux", "Too much butter", "Over-whisking", "Too much salt"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "A dark roux thickens less because prolonged cooking…", "options": ["Evaporates the fat", "Breaks down the starch molecules that do the thickening", "Adds protein", "Removes the flour"], "correct": 1},
            {"q": "Simmering a béchamel for several minutes after it thickens is necessary to…", "options": ["Cook out the raw flour taste and fully hydrate the starch", "Reduce the volume", "Melt the butter", "Add colour"], "correct": 0},
            {"q": "Béchamel and velouté differ mainly in…", "options": ["The roux colour and the liquid used — milk versus stock", "The fat used", "The thickening method", "Cooking time only"], "correct": 0},
        ],
    },
    {
        "slug": "sauce-emulsion", "branch": "sauce", "title": "Cold Emulsions", "icon": "🥣",
        "req_tier": 5, "est_min": 25,
        "summary": "Mayonnaise and vinaigrette: forcing oil and water to hold hands and stay together.",
        "intro": (
            "Oil and water do not mix, but they can be persuaded to stay suspended in each other if the "
            "droplets are small enough and something coats them. That something is an emulsifier — lecithin "
            "in egg yolk, mustard in a vinaigrette."
        ),
        "steps": [
            "Start with the water phase: yolk, a little acid, mustard, salt — all whisked together first.",
            "Add the oil in a very thin stream at the start, whisking constantly; the first spoonful is where emulsions are won or lost.",
            "Once it thickens and turns pale, you can add oil faster.",
            "Thin with a few drops of water or lemon if it becomes too stiff to accept more oil.",
            "For vinaigrette, whisk mustard into the vinegar first, then stream in oil at roughly three parts oil to one part acid.",
            "Taste and adjust acid and salt last, once the texture is right.",
        ],
        "tips": [
            "A broken mayonnaise is fixable: start a fresh yolk in a clean bowl and whisk the broken mixture into it drop by drop.",
            "Everything at the same temperature emulsifies more readily — a fridge-cold yolk fights you.",
        ],
        "quiz": [
            {"q": "An emulsion combines…", "options": ["Two solids", "Fat and water that normally separate", "Sugar and salt", "Air and flour"], "correct": 1},
            {"q": "The emulsifier in mayonnaise is…", "options": ["Lecithin in the egg yolk", "The vinegar", "The salt", "The oil"], "correct": 0},
            {"q": "A broken mayonnaise is best rescued by…", "options": ["Whisking harder", "Whisking it slowly into a fresh yolk", "Adding more oil", "Heating it"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "The first spoonful of oil must go in slowly because…", "options": ["The emulsifier can only coat a limited amount of droplet surface at once", "Oil is cold", "The yolk is thick", "The bowl is dry"], "correct": 0},
            {"q": "Mustard works in a vinaigrette because it acts as…", "options": ["An acid", "An emulsifier and a stabiliser", "A thickener only", "A flavouring only"], "correct": 1},
            {"q": "Adding a few drops of water to a stiff mayonnaise helps because it…", "options": ["Dilutes the flavour", "Increases the water phase so it can hold more oil droplets", "Cools it", "Adds acidity"], "correct": 1},
        ],
        "extra": ["eggs-scramble"],
    },
    {
        "slug": "sauce-herb", "branch": "sauce", "title": "Herb & Raw Sauces", "icon": "🌿",
        "req_tier": 6, "est_min": 20,
        "summary": "Pesto, salsa verde, chimichurri — uncooked sauces that live or die on how you treat the herbs.",
        "intro": (
            "Raw herb sauces are the fastest way to make a plain piece of protein or vegetable taste finished. "
            "There is no cooking to hide behind, so the whole technique is about preserving the volatile "
            "aromatics in the herbs rather than bruising and oxidising them into something dull and brown."
        ),
        "steps": [
            "Use the freshest herbs you can and dry them thoroughly; water dilutes the sauce and speeds browning.",
            "Chop with a genuinely sharp knife — a dull blade crushes the leaves and turns them black.",
            "Work quickly and keep everything cool; heat from a blender motor degrades delicate herbs.",
            "Add acid late rather than early: acid dulls the green colour on contact.",
            "Build the texture with oil last, stirring it in rather than blending it, so the sauce stays loose and bright.",
            "Season and taste at the end, and serve within hours rather than days.",
        ],
        "tips": [
            "Blanching herbs briefly and shocking them in iced water locks in a vivid green for a sauce you need to hold.",
            "A mortar and pestle bruises differently from a blade and gives a rounder, less bitter pesto.",
        ],
        "quiz": [
            {"q": "Herbs for a raw sauce should be chopped with…", "options": ["A very sharp knife", "A dull knife for texture", "A food processor always", "Scissors"], "correct": 0},
            {"q": "Acid should be added to a herb sauce…", "options": ["Late, because it dulls the green colour", "First, to preserve it", "Never", "Before the herbs"], "correct": 0},
            {"q": "Wet herbs are a problem because water…", "options": ["Dilutes the sauce and speeds browning", "Makes it too thick", "Adds bitterness only", "Prevents chopping"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Bruised herbs turn dark because damaged cells release…", "options": ["Enzymes that oxidise the plant's phenolic compounds", "Water", "Chlorophyll", "Acid"], "correct": 0},
            {"q": "Blanching and shocking herbs preserves colour because the brief heat…", "options": ["Deactivates the browning enzymes before they can work", "Adds chlorophyll", "Removes water", "Softens the leaves"], "correct": 0},
            {"q": "Blending a pesto at high speed can turn it bitter because the friction…", "options": ["Heats the oil and herbs, driving off aromatics and oxidising them", "Adds air only", "Breaks the emulsion", "Over-salts it"], "correct": 0},
        ],
    },
    {
        "slug": "sauce-hollandaise", "branch": "sauce", "title": "Warm Emulsions", "icon": "🍋",
        "req_tier": 7, "est_min": 25,
        "summary": "Hollandaise, béarnaise and beurre blanc — emulsions held together by heat you must not exceed.",
        "intro": (
            "A warm emulsion is a cold one with an extra hazard: the same heat that helps it thicken will "
            "scramble the yolks if it goes a few degrees too far. Everything about the technique is about "
            "keeping the pan just below that line."
        ),
        "steps": [
            "Make a reduction — wine, vinegar, shallot, peppercorns — and strain it; this is where béarnaise gets its character.",
            "Whisk yolks with the cooled reduction over a bain-marie, never over direct heat.",
            "Whisk until the mixture thickens into a sabayon and the whisk leaves visible ribbons.",
            "Take the bowl off the heat and stream in warm clarified butter slowly, whisking all the while.",
            "Season with salt and lemon at the end, and thin with a spoonful of warm water if it tightens.",
            "Hold it lukewarm, never hot — above roughly 65°C it will split.",
        ],
        "tips": [
            "Clarified butter emulsifies more reliably than whole butter: the milk solids and extra water work against you.",
            "If it splits, whisk it into a fresh yolk, or into a spoonful of warm water, off the heat.",
        ],
        "quiz": [
            {"q": "Hollandaise is made over…", "options": ["Direct high heat", "A bain-marie", "A cold bowl", "An open flame"], "correct": 1},
            {"q": "Butter is streamed in…", "options": ["All at once", "Slowly, while whisking", "After chilling", "Before the yolks"], "correct": 1},
            {"q": "Hollandaise splits if it gets…", "options": ["Too cold", "Too hot", "Too acidic", "Too salty"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "The sabayon stage matters because whisking yolks over gentle heat…", "options": ["Partially denatures them, so they hold far more butter", "Cooks them fully", "Removes water", "Adds air only"], "correct": 0},
            {"q": "Clarified butter works better than whole butter because it has…", "options": ["More fat and no milk solids or excess water to destabilise the emulsion", "More flavour", "A lower melting point", "More protein"], "correct": 0},
            {"q": "Beurre blanc is stabilised primarily by…", "options": ["Egg yolk", "The reduction's acid plus the butter's own milk solids, kept warm not hot", "Starch", "Cream only"], "correct": 1},
        ],
        "extra": ["heat-sear"],
    },
    {
        "slug": "sauce-reduction", "branch": "sauce", "title": "Reductions & Glazes", "icon": "🍷",
        "req_tier": 8, "est_min": 25,
        "summary": "Boiling water away to concentrate everything else — the simplest sauce technique and the least forgiving.",
        "intro": (
            "Reduction concentrates flavour, body and salt at the same rate. That last one is why you season "
            "a reduction at the end: a sauce salted at the start becomes inedible by the time it coats a spoon."
        ),
        "steps": [
            "Start with a flavourful liquid — stock, wine, braising liquid — and use a wide pan for faster evaporation.",
            "Simmer rather than boil hard; a violent boil emulsifies fat into the sauce and clouds it.",
            "Skim the scum and fat that rise to the surface as it reduces.",
            "Judge thickness by how it coats the back of a spoon, not by volume.",
            "Season only once you have reached the final thickness.",
            "Finish off the heat with cold butter for gloss, or a splash of cream for body.",
        ],
        "tips": [
            "A gelatine-rich stock reduces to a glossy glaze; a thin, gelatine-poor one just gets salty.",
            "Reduce in a wide pan, then finish in a small one — surface area early, control late.",
        ],
        "quiz": [
            {"q": "You should season a reduction…", "options": ["At the start", "Once it reaches final thickness", "Halfway through", "Never"], "correct": 1},
            {"q": "A wide pan reduces faster because it has…", "options": ["More surface area for evaporation", "Thicker walls", "Better heat retention", "Less liquid"], "correct": 0},
            {"q": "A hard rolling boil during reduction tends to…", "options": ["Speed it up harmlessly", "Cloud the sauce by emulsifying fat into it", "Improve the gloss", "Add body"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "A stock reduces to a glossy glaze rather than a salty liquid when it is rich in…", "options": ["Fat", "Gelatine", "Salt", "Starch"], "correct": 1},
            {"q": "Skimming during reduction matters because impurities and fat…", "options": ["Concentrate along with everything else and muddy the flavour", "Add too much body", "Slow evaporation", "Lower the temperature"], "correct": 0},
            {"q": "Adding cold rather than room-temperature butter to finish a sauce…", "options": ["Melts slower, letting it emulsify instead of splitting", "Adds more fat", "Cools it for serving", "Tastes different"], "correct": 0},
        ],
    },
    {
        "slug": "sauce-pan", "branch": "sauce", "title": "Pan Sauces on the Fly", "icon": "🫕",
        "req_tier": 9, "est_min": 20,
        "summary": "Five minutes between taking the meat out and putting a real sauce on the plate.",
        "intro": (
            "A pan sauce is the highest ratio of result to effort in cooking. Everything you need is already "
            "in the pan when the meat comes out; the technique is just a fixed sequence you can run without "
            "a recipe."
        ),
        "steps": [
            "Take the protein out and rest it on a rack; leave the fond in the pan.",
            "Pour off excess fat, keeping about a spoonful, and sweat a finely chopped shallot in it.",
            "Deglaze with an acid — wine, vermouth, vinegar — and scrape every browned bit loose.",
            "Reduce that almost to a syrup, then add stock and reduce again by about half.",
            "Add any resting juices from the meat back into the pan.",
            "Off the heat, whisk in cold butter, then adjust with salt, pepper, herbs and a squeeze of acid.",
        ],
        "tips": [
            "Reduce the wine almost completely before adding stock, or the sauce tastes raw and sharp.",
            "Taste for acid last. Almost every pan sauce is improved by a few drops more.",
        ],
        "quiz": [
            {"q": "A pan sauce starts by…", "options": ["Washing the pan", "Deglazing the fond left after searing", "Adding cream", "Making a roux"], "correct": 1},
            {"q": "Resting juices from the meat should be…", "options": ["Discarded", "Added back into the sauce", "Used to baste", "Frozen"], "correct": 1},
            {"q": "Butter is whisked in…", "options": ["Off the heat, at the end", "At the very start", "While boiling", "Before the stock"], "correct": 0},
        ],
        "mastery_quiz": [
            {"q": "Wine is reduced nearly to a syrup before the stock goes in because…", "options": ["It concentrates flavour and cooks off the harsh raw alcohol notes", "It thickens the sauce", "It prevents splitting", "It removes acidity entirely"], "correct": 0},
            {"q": "The shallot is sweated rather than browned because…", "options": ["Browning adds bitterness that competes with the fond", "It cooks faster", "It absorbs fat", "It thickens the sauce"], "correct": 0},
            {"q": "A pan sauce tastes flat despite correct seasoning. The likeliest fix is…", "options": ["More salt", "A few drops of acid", "More butter", "Longer reduction"], "correct": 1},
        ],
        "extra": ["heat-roasting"],
    },
    {
        "slug": "sauce-modern", "branch": "sauce", "title": "Purées & Modern Thickeners", "icon": "🧪",
        "req_tier": 11, "est_min": 25,
        "summary": "Blenders, starches and hydrocolloids — thickening without flour or butter.",
        "intro": (
            "Classical sauces thicken with flour, fat or reduction. Modern kitchens often want the flavour "
            "without the weight, which means learning what each thickener actually does: starches gel, gums "
            "thicken cold, and a good blender can turn a vegetable into a sauce on its own."
        ),
        "steps": [
            "For a vegetable purée, cook until fully soft, blend hot with a little cooking liquid, and pass through a fine sieve.",
            "Use cornflour slurries for clear, glossy sauces — mix with cold liquid first, then add to simmering liquid.",
            "Remember that cornflour sets on cooling and thins if boiled too long; arrowroot stays clearer but is more fragile.",
            "Use xanthan gum in tiny amounts, blended in, for sauces that must stay thick when cold.",
            "Adjust consistency with the cooking liquid rather than water, so you never dilute flavour.",
            "Season purées aggressively — blending mutes salt perception.",
        ],
        "tips": [
            "A very small amount of gum goes very far. Overdo it and the sauce turns slimy and cannot be fixed.",
            "Passing a purée through a fine sieve is the difference between homemade and restaurant.",
        ],
        "quiz": [
            {"q": "A cornflour slurry must be mixed with…", "options": ["Cold liquid before adding to hot", "Boiling liquid directly", "Oil", "Butter"], "correct": 0},
            {"q": "Xanthan gum should be used…", "options": ["Generously", "In very small amounts", "Only when hot", "Instead of salt"], "correct": 1},
            {"q": "Purées should be seasoned…", "options": ["Lightly", "Aggressively, because blending mutes salt perception", "Not at all", "Only after chilling"], "correct": 1},
        ],
        "mastery_quiz": [
            {"q": "Cornflour-thickened sauces thin out if boiled too long because…", "options": ["Water evaporates", "The starch granules rupture and the network breaks down", "Salt interferes", "The gel sets"], "correct": 1},
            {"q": "Xanthan gum thickens cold liquids where starch cannot because it…", "options": ["Hydrates without heat", "Requires boiling", "Contains protein", "Is an emulsifier only"], "correct": 0},
            {"q": "Arrowroot is preferred over cornflour for a glossy fruit sauce because it…", "options": ["Stays clearer and does not taste starchy", "Thickens more", "Withstands long boiling", "Sets harder"], "correct": 0},
        ],
    },
]
