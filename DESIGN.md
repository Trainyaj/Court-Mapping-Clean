Implementing this project was a wild ride. 

I first decided to transition away from  CS50's virtual sandbox and run everything from my computer, which led to *quite* a challenging setup process (Visual Studio Code didn't work, then python didn't work, then various libraries didn't work so on and so forth).

Backend citation data:
I initially tried to use bulk citation data from CourtListiner.com. However, this data was *huge* (25GB+ in SQL), contained lots of non-supreme court data I didn't care about (including for citations linked by ID, which were extremely resource intentsive  because that added calls to check whether the IDs were linked to supreme court caes or not), didn't contain old citations (before ~1950, very roughly), and contained *many*, many copies of many supreme court cases (many generated automatically), only 1 of which actually contained the citations I cared about. 

After trying to get this data to work for a few days, I turned to a different set of citations, already generated from CourtListiner.com by Lissner and Carver. These citations were also less than ideal (they only went up to 2003), but they were a *lot* easier to work with (only supreme court cases, much smaller database, more complete set of pre-2003 citations), so I decided to go with their data, which I importeed to cases.db.

Front-end website:
Creating the front-end website and its connections to the backend were relatively straightforward. I used ideas from class (html templates, header bars, Flask, etc.) to create a basic website shell runable via app.py. The website didn't need to be anything special, so I just created four pages: index.html allows users to search for cases to graph, serach_results.html displays the results of their search (and allows users to expand said resutls), and about and credits.html provide more information about the website.

In main.js, I also implemented basic error checking in case the user tried to search for a case that didn't exist, and a case autocomplete based very heavily on the autocomplete example shown in class.

The database in hand and the front-end usable, I turned to the real challenge: creating my citaiton graphs.

I initially tried to use graphviz (through pygraphviz) to create the graphs. This involved using python to generate the structure of the citaiton graphs (as pygraphviz objects), and then creating images from the graph. Sadly, the images created were *super* ugly, and, perhaps, importantly, static PNGs. I realized this would make it near-impossible for me to implement the ability for users to add-on to the graphs that they generated, so I dropped graphviz.

Instead, I switched to cytoscape (specifically, cytoscape.js), front-end software better specialized in the *visualization* of graphs than graphviz. To implement graphs in cytoscape, I updated my python function (create_citation_graph and all its helper functions, called by search_results()), to return a list of cases (nodes) and citations (edges) in a format usable by cytoscape (a list of dictionaries). The python function was quite simple to create a first pass at, but it turned out to have *lots* of finicky edge cases (what if two cases cite each other, what if several cases have the same name, etc.) I had to deal with, so I ended up spending a lot of time writing it.

That function done, on the recommendation of ChatGPT, I used JSONs to pass my lists of dictionaries from my python backend, through Flask, to my front end (search_results.js). At that point, creating and displaying my citation graph was quite straightforward, with the main task being making the graph look good *and* be readable (not as simple as it seems).

Finally, I added the ability to click on a case in the front-end and add all the citations connected to that case to the graph. Front-end wise, the check for clicking was easy to implement—one of the big benefits of cytoscape.js being *designed* to display interactive graphs in webpages.

The backend (expand_case()) was quite challenging because of all the edge cases but not unlike from the inital graph generation—just lots of small things to be accounted for (how do I ensure that cases already in the graph don't have duplicate citations added, how do I generate citations between the new cases and the cases already in the graph, etc).

Video Script:
I'm Jay Sweitzer-Shalit, a First Year in Adams, Planning to Concentrate in Applied Math. 

This is my project, Supreme Court Citation Mapping. Inspired by the web of science, which creates maps of academic paper citations, I created a web page that creates a map of supreme court case citations.

Example 1: Brown v. Board
Example 2: Plessy v. Ferguson

project’s title, your name and year, your dorm/house and concentration, and any other details that you’d like to convey to viewers.