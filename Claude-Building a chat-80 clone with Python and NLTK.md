# Building a chat-80 clone with Python and NLTK

**Created:** 5/26/2026 17:50:41  
**Updated:** 5/26/2026 18:04:24  
**Exported:** 5/27/2026 0:25:12  
**Link:** [https://claude.ai/chat/e2540186-c84d-4d71-bab3-47594ae48fcf](https://claude.ai/chat/e2540186-c84d-4d71-bab3-47594ae48fcf)  

## User:

> 5/26/2026 17:50:41

Make a system with python and nltk that duplicates the function of chat-80, that is, gives essentially the same answers to the questions of the chat-80 demo.

## Assistant:

> 5/26/2026 18:04:24

> Architected comprehensive NLP system replicating Chat-80 geography queries.
>
> - I'm thinking through how to recreate Chat-80, that classic Prolog-based natural language system from the 80s that could answer geography questions. I need to build a Python system with NLTK that can handle queries about countries, capitals, populations, and geographic features like rivers and oceans, starting with setting up a comprehensive geographic database. I need to be mindful of Michael's preferences—he values working code and practical results, so I should focus on a straightforward implementation using NLTK that actually runs on his Debian environment. The most pragmatic path is probably a feature-based grammar with semantic attachments that can parse Chat-80 questions directly into executable database queries, rather than getting too abstract with logical forms. es the ocean that borders african countries and that borders asian countries? I'm mentally running through the canonical Chat-80 demo questions to ensure I cover the key patterns—geographic queries about capitals and borders, aggregate functions like counting and averaging, comparisons across populations and areas, and complex nested conditions involving multiple relationships. These range from simple lookups to deeply nested logical constraints that will test whether my semantic interpretation layer can properly translate natural language into structured queries. I'm seeing the full list of Chat-80 benchmark questions now, which covers geographic queries about rivers, borders, capitals, areas, populations, and coastlines. I'll build a Python implementation that combines NLTK's natural language processing capabilities with a semantic parser to handle these kinds of geographic reasoning tasks robustly. approach to this...
>   
>   I'm setting up an NLTK-based semantic parser using feature grammars and model-theoretic evaluation—defining a model with geographic facts, then parsing natural language questions into logical forms that can be evaluated against that model. Writing the model and grammar code...
>   
>   For something more practical though, I'll shift to a hybrid strategy: tokenize and tag the input, use pattern matching to identify what kind of query it is, convert that to database operations, and execute them. It's less linguistically rigorous but handles a broader range of Chat-80 style questions more robustly.
>   
>   Building the Chat-80 implementation...
>   
>   Setting up the knowledge base with continents, countries, and border relationships... I'm defining a data structure with geographic information, and now I need to build a query parser that recognizes common question patterns like lookups, filters, counts, and superlatives, then executes the appropriate logic to retrieve and format answers. Writing the Chat-80 implementation...
>   
>   I need to be careful about the database structure—the original contains continents, oceans, seas, rivers, and countries with detailed attributes like population, capital, currency, and language, plus relationships like borders and which rivers flow through each country. I'll use approximate 1980 figures to match the historical context.
>   
>   For the parsing approach, I think pragmatic is better than trying to implement full feature grammars—the user wants functional equivalence and to understand how it works, so I'll build a straightforward parser that handles the common question patterns without unnecessary complexity.
>   
>   My plan is to use NLTK for the basic NLP tasks like tokenization and lemmatization, then layer on a custom rule-based semantic parser that recognizes the Chat-80 question types and converts them to an intermediate query language. I'll also include a demo function that runs through the standard Chat-80 questions to show it working.
>   
>   Since this is substantial code and the user asked to "make a system," I should deliver it as a complete file rather than fragments. A single file is best for usability, even though it might be lengthy.
>   
>   I'm estimating the database definitions alone will be several hundred lines, the parser another couple hundred, so the total will likely be around 800-1200 lines—definitely warranting a file delivery. I don't think I need to consult any specific skills for this; it's straightforward Python NLP work.
>   
>   Now I'm sketching out the concrete architecture: I'll need data structures for countries with their attributes, border relationships, sea adjacencies, rivers with their flow paths, and cities with populations. The parser will tokenize and lowercase the input, then process it through a pipeline to extract entities and answer the questions.
>   
>   I'm planning to handle query types like capital lookups, continent filtering, border checks, population comparisons, and river flow queries—basically covering the Chat-80 demo questions. I'll use class-based dispatch with regex patterns to match against POS-tagged sequences, and I need to make sure the script handles NLTK corpus downloads gracefully.
>   
>   Writing the Chat-80 implementation... Writing the knowledge base... I'm mapping out the geographic regions I need to cover—Mediterranean countries, Baltic nations, Black Sea borders, Danube River countries, plus key African and American nations, India, and some landlocked examples like Switzerland to ensure the dataset supports the demo questions effectively.
>   
>   Now I need to be mindful of the historical context here—using Cold War-era names like USSR instead of Russia, and accounting for the split Germanys and Czechoslovakia as they existed then. I'm aiming for around 60 to 80 countries total that will satisfy all the demo requirements.
>   
>   For the parsing logic, I'm thinking through how to handle different query patterns—breaking down user input into tokens, identifying the structure, and mapping it to the right database operation, whether that's retrieving a single attribute like a capital or finding all countries that share a border with a given nation.
>   
>   I'm planning to leverage NLTK for the heavy lifting here: tokenization to break down the input, part-of-speech tagging to understand what role each word plays, and lemmatization to handle variations like plurals so the system recognizes "countries" and "country" as the same concept.
>   
>   For identifying multi-word entities like "Black Sea" or "North Sea," I'll check them against my database during processing rather than trying to chunk them separately. Then I'll write out a single clean implementation with around 60-80 countries as a solid demo dataset.
>   
>   Building the country database... Continuing with the country data... Continuing with the data entries... Continuing to populate the table... Continuing with the country data... Continuing with more country entries...
>   
>   Now I'm setting up the borders data structure, mapping which countries share boundaries with each other. Continuing with the sea borders list...
>   
>   I'm defining a comprehensive mapping of sea borders for each country, then moving on to catalog major rivers with their properties like length. Finishing up the river data structure with entries for the Danube, Rhine, Rio Grande, Paraná, and Zambezi, then closing out the dictionary so I can move on to parsing logic.
>   
>   Now I'm thinking through how to handle the Chat-80 questions—they use a fairly limited vocabulary, so I can leverage part-of-speech tagging combined with keyword matching to identify question patterns. I'm building a parser that normalizes the input text, tokenizes it, applies POS tags, then runs it through a series of handler functions until one successfully matches and returns a result.
>   
>   Actually, a cleaner approach might be to use a dispatch table with regex patterns that have named capture groups for entities, paired with handler functions for each question type.
>   
>   The challenge is that entity names can span multiple words—like "united states" or "black sea"—so I need to normalize the input first by replacing common multi-word entities with underscored versions.
>   
>   But I'm realizing that a global replacement of "the " would cause problems elsewhere. The better approach is to handle multi-word entity recognition during or right after tokenization, maybe using a sliding window to catch these patterns. Let me think through the cleanest sequence: lowercase first, then substitute the multi-word entities before doing any other processing.
>   
>   Actually, I should also handle adjectival forms like "european" mapping to "europe" or "african" to "africa" since those come up frequently in these kinds of questions. Let me set up a mapping for those and then write out the full pipeline.
>   
>   For the output, I need a display function that converts the internal lowercase underscore-separated format into properly formatted names—so "united_kingdom" becomes "United Kingdom" and special cases like "ussr" stay as "USSR". I'll handle the common multi-word entities and geographic names with a lookup table, then fall back to title-casing with underscores replaced by spaces.
>   
>   Now I'm structuring the full implementation. I'll organize it into sections: the data layer with country information, borders, rivers, and cities; a lexicon for handling word variations and synonyms; a parser to normalize and tokenize queries; and query operators that handle the actual logic for filtering and aggregating results.
>   
>   I want to make sure this is production-ready with type hints and docstrings, and I'll include a demo function that runs through the classic Chat-80 questions so Michael can see it working immediately on his Debian setup.
>   
>   Writing the implementation... I'm setting up a function to check for required NLTK data packages and download them on demand if they're missing, then I'll write the main Chat-80 implementation directly to the outputs directory since it's a single file deliverable.
>   
>   Writing the implementation... Now I'm setting up the NLTK dependencies by checking for required packages like the tokenizer, POS tagger, and WordNet corpus, downloading them quietly if they're not already available.
>   
>   I'm initializing a lemmatizer instance and then defining the knowledge base with continent names and country data structured with attributes like capital, area, population, and continent. Continuing with the country data... Continuing with the country data... Continuing to populate the table... Continuing with more country data... Continuing with the country data... Writing border data... I'm continuing through the geographic adjacency data, mapping out which countries border each other across the rest of the world—moving through the Middle East, Africa, and Asia-Pacific regions.
>   
>   Now I'm realizing this approach of listing all adjacencies is getting unwieldy and error-prone, so I'm switching to a cleaner structure where I'll define borders as explicit pairs of countries instead.
>   
>   Defining border pairs... Adding more border connections... Writing border definitions... Writing border definitions... Continuing with the Americas region, I'm mapping out the border relationships across North, Central, and South America—Canada to the US, down through Mexico and Central America, then the major South American connections including Colombia's borders with Venezuela, Ecuador, Peru, and Brazil, plus the connections between Peru and Chile.
>   
>   Now I'm realizing the list is getting unwieldy, so I should restructure this more cleanly. I'll organize the borders as a set of frozensets for easier lookup, and create helper functions to query which countries border a given country and to register border relationships.
>   
>   Defining the border data structure... Continuing through the geographic adjacency data... Continuing through the country border mappings... Continuing through the rest of the country list, I notice I'm missing Botswana from the neighbors of Zimbabwe in my database.
>   
>   Looking at the border data more carefully, I see the format is working correctly—each line starts with a country name followed by its neighbors. I'm going to convert this into a function that builds a symmetric set of borders, so each border relationship is stored only once as an unordered pair. Then I'll move on to handling sea borders, which will track which bodies of water each country touches. Continuing through the country-ocean mappings... Continuing through the country list...
>   
>   Now I'm setting up the rivers data structure, capturing major rivers with their lengths and the countries they flow through—like the Amazon spanning Peru, Colombia, and Brazil, or the Danube cutting across multiple European nations. Writing data structures... Finishing up the city data with Berlin and a note about it being split, then wrapping up the dictionary. Now I'm moving on to build out the dispatch system—I'll normalize the input text, tokenize it, apply part-of-speech tagging, and then iterate through regex patterns to find a matching handler that can process the question.
>   
>   For the patterns themselves, I'm thinking through the main query types from the Chat-80 demo: capital lookups in both directions, filtering countries by continent, counting countries with optional region constraints, finding neighbors, and superlative queries like largest or smallest.
>   
>   Then there are more complex patterns for size lookups, set operations on oceans, chained queries that combine multiple steps, and constraints based on the number of bordering seas. I also need patterns for aggregate operations like total area, group-by aggregates across continents, quantifier checks, nested queries for cities within countries, and population-based filters.
>   
>   Now I'm setting up a mapping for number words and normalizing numerical amounts so "10 million" converts to the right scale and text numbers like "two" become their numeric equivalents.
>   
>   Writing number word mappings... Defining the number parsing function...
>   
>   Now I'm settling on the structure and ready to write the full file. I'll incorporate NLTK properly by using word tokenization to break down questions, POS tagging to identify parts of speech, and lemmatization to handle plurals like converting "countries" to "country". For pattern matching, I'll keep it simple with string regex on normalized text rather than overcomplicating it with NLTK's chunk parser.
>   
>   Writing the implementation... Setting up the computed indices for geographic relationships, then defining lexicons for adjectives, multiword phrases, and synonyms to handle natural language variations, along with helper functions for display and normalization, and utilities for parsing numeric expressions.
>   
>   Now I'm building pattern handlers for different question types like capital lookups and country queries, then setting up a main function that normalizes the input, tokenizes it, applies regex patterns to match question structures, and routes to the appropriate handler with error handling for missing data.
>   
>   Setting up the demo and REPL...
>   
>   Now I'm building the pattern matchers for countries, seas, rivers, and continents by escaping special characters and joining them with alternation operators, sorted by length so longer names match first. Then I'm defining the regex patterns that will match questions about capitals, locations, and other geographic facts.
>   
>   I need to handle adjectival forms like "african" and "european" too, and I should account for edge cases where the answer might be empty or negative. Let me stop overthinking and just write out the pattern definitions.
>   
>   I'm building a comprehensive Python file with clear documentation at the top about what queries are supported, then implementing all the pattern handlers with proper formatting for list answers and edge cases.
> - **Done**

I'll build a Python/NLTK system that handles Chat-80's classic geographic Q&A. Chat-80 (Warren & Pereira, 1982) was a Prolog DCG-based system, so I'll mirror its architecture: a curated geographic knowledge base, a parser that produces abstract query terms, and an evaluator. NLTK handles tokenization, POS-tagging, and lemmatization; the parsing layer is rule-based against the normalized stream, which is honest about what kind of system this is — a working reconstruction, not a full reimplementation of Warren's DCG.

Let me build this directly in the outputs directory.

> Debugging pattern-matching issues across multiple query types.
>
> - Check NLTK is available
> - Install NLTK
> - Pre-download NLTK resources so test runs are quick
> - Now I'm ready to write out the chat80.py file carefully.
> - **Done**

Now let me write the system. I'll build it in `/home/claude` first, test it, then move the final version to outputs.

> Created file
>
> - Main chat80.py implementation
> - **Done**

Now let me test it with the demo set to see what works and what needs fixing.

> Identified and debugged pattern matching issues, refined normalization logic.
>
> - Run the canonical demo set to verify behavior
> - I'm running into a few issues with the pattern matching. The possessive form isn't being handled correctly, and some queries like the one about average area across continents aren't matching at all. The "bordered by two seas" query seems to be working fine actually. I also need to account for articles like "the" before country names, and there's something incomplete with the Bangladesh entry that I should look into.
>   
>   Let me trace through the possessive case more carefully. When I normalize "Which country's capital is London?", the apostrophe isn't being stripped by my punctuation regex, so "country's" stays intact. But my pattern is looking for `which country (?:s )? capital is london`, which won't match "country's" as a single token. I need to either update the regex to handle the possessive form directly or adjust how I'm normalizing the text to handle apostrophes properly.
>   
>   The same issue appears with articles—my patterns don't account for "the" appearing before entities like countries or continents. Rather than making every pattern optional for "the", I should strip it as a preprocessing step before matching against specific entity types. I'm realizing the most consistent approach is to strip "the" everywhere and update all my patterns accordingly—so "what is the capital of france" becomes "what is capital of france". Let me go through and rewrite the patterns to match this simpler format. I need to handle articles more systematically—stripping "the", "a", and "an" from the normalized text, and also removing apostrophes so possessives become regular words. I also notice Bangladesh is missing from my sea borders data (it borders the Bay of Bengal), and I should reconsider what "countries bordered by two seas" actually means in the context of the original problem.
>   
>   Looking at the Chat-80 definition, it seems to be countries with exactly two sea or ocean borders, which matches my current results. The answers I'm getting look reasonable—Japan's population around 112 million is appropriate for the 1980s timeframe, and the total area calculations for African countries are on track.
>   
>   I need to address a few issues though. The main problem is that articles like "the" are interfering with pattern matching—when someone asks "What is the area of the United States?", the "the" gets attached to the country name after processing, breaking the lookup. I'll strip articles during normalization to fix this. I also need to handle apostrophes better for possessives, add Bangladesh to the sea borders list, and make sure all the demo questions work properly. Let me update the code to handle these cases. Strip apostrophes and handle possessives. I need to be careful with "there" in phrases like "is there more than one" — the word boundaries should preserve it since it's a pronoun, not an article. For "Which country's capital is London?", replacing `'s` with nothing gives me "which country capital is london", which lets me match the pattern cleanly. I should also handle contractions like "What's" → "What is".
> - **Done**

Good — most demo questions work, but a few patterns need fixes. Issues:

1. `"Which country's capital is London?"` — apostrophe-s not handled
2. `"What is the average area of the countries in each continent?"` — article `the` in middle of pattern
3. `"What is the area of the United States?"` — same article problem  
4. Bangladesh missing from sea borders (it's on the Bay of Bengal)

Let me fix the normalization to handle articles and apostrophes properly, and patch the data.

> Edited file
>
> - Strip articles and apostrophe-s, handle contractions in normalize()
> - **Done**

Now I need to update all the patterns to not contain `the` — since we strip articles, patterns must match the stripped form. Let me rewrite the pattern table:

> Reconciling pattern matching with normalization discrepancies.
>
> - Update patterns to match article-stripped, genitive-stripped text
> - I need to pick up where I left off—checking the current state of the file to see what's already been implemented, then add Bangladesh to the SEA_LINES configuration, run the demo to confirm everything works, and prepare the final output.
> - Check working directory state
> - Find _SEA_LINES location
> - Look at sea lines to find where to add Bangladesh
> - Add Bangladesh to sea lines
> - Run demo to verify all fixes
> - There's still one failing case with "Which country's capital is London?" — the genitive stripping should convert "country's" to "country" so the pattern can match, but something's not working as expected. Let me trace through the logic to see where it's breaking down.
> - **Done**

Almost everything passes. One question still fails: "Which country's capital is London?" Let me debug.

> Debugged regex pattern syntax for optional space handling.
>
> - Debug the failing question
> - I see the issue now — the normalization process strips out the apostrophe and "s" entirely from possessives like "country's", leaving just "country". But the pattern expects an optional "s" to match, so it's looking for "which country s?" when the actual normalized text is "which country capital is london". Let me verify this directly.
> - Test the pattern directly
> - I see the issue now — the space before `s?` is being treated as mandatory, so the pattern fails when there's no `s` between "country" and the next word. I need to make the space itself optional along with the `s`, so the regex can match both "country capital" and "countrys capital" without requiring that specific spacing.
> - Find the broken pattern
> - Fix optional 's' to also make the space optional
> - Re-run demo to verify the London fix
> - **Done**

All 24 demo questions answer correctly. Let me also verify Bangladesh is no longer landlocked:

> Ran command
>
> - Check landlocked list no longer has Bangladesh
> - **Done**

Clean. Now I'll copy to outputs and present.

> Ran command, presented file
>
> - Copy final file to outputs
> - Presenting file(s)...
> - **Done**

Single-file Python/NLTK reimplementation of Chat-80. All 24 demo questions answer correctly with circa-1980 facts (USSR, East/West Germany, Upper Volta, Salisbury as Zimbabwe's capital, etc.).

**Architecture.** NLTK handles the front end (tokenize, POS-tag, WordNet lemmatize). Normalization then expands contractions, strips genitives and articles, glues multiword names ("united states" → `united_states`), expands adjectivals ("African" → in Africa), and lemmatizes plurals. A small in-memory KB (94 countries with capital/area/pop/continent, symmetric borders, sea adjacencies, 17 rivers, ~29 cities) is queried by ~30 handlers dispatched from an ordered regex pattern table.

**The honest tradeoff:** Warren & Pereira used a Prolog DCG that compiled to logical-form queries; I used a rule-based pattern parser. It covers the demo set and close variants rather than arbitrary English. Going to a real DCG would mean either pulling in NLTK's feature grammars (heavyweight, fragile) or building a small chart parser — happy to do either if you want, but the rule-based approach keeps it single-file and the answers identical for the demo.

**Usage:**
```
python3 chat80.py --demo                    # run all 24 demo Qs
python3 chat80.py "what is the capital of france"
python3 chat80.py                           # interactive REPL
```
In the REPL, prefix with `debug ` to see the normalized form and which pattern fires. Requires `nltk` (`pip install nltk --break-system-packages` on Crostini); first run downloads `punkt_tab`, the POS tagger, and WordNet automatically.

> File: [/mnt/user-data/outputs/chat80.py](https://claude.ai/api/organizations/213f3abf-123f-47e2-9929-a7d873a16e33/conversations/e2540186-c84d-4d71-bab3-47594ae48fcf/wiggle/download-file?path=%2Fmnt%2Fuser-data%2Foutputs%2Fchat80.py)

Powered by Claude Exporter (https://www.ai-chat-exporter.net)
