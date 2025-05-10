# Court-Mapping

Documentation and set up instructions for Jay's CS50 final project: supreme court citation mapping.

TLDR: My project creates a webpage (with Flask) which allows the user to search for a supreme court case, generate a graph of all the cases that cite and are cited by the supreme court case using Cytoscape, then further expand the graph from there.

Detailed Documentation: 

Dependences:
My project needs:
-Python 3.13, including:
--flask (including Flask, render_template, request, and jsonify)
--sqlite3 (the Python module)
-Cytoscape.js (included in the static folder)
-Bootstrap (automatically imported in base.html)
-A computer
-My project folder (including my 2.5GB citatation database, cases.db)
-Way to view a webpage on said computer (which by default will load on http://127.0.0.1:5000)
And that is it!

To run my project, simply run my app.py in whatever interface of your chosing. I used the desktop verson of visual studio code and ran app.py by typing "python app.py" in my terminal window. If for some reason that doesn't work, "Flask Run" should accomplish the same. The navigate to the webpage you just created (which by default will load on http://127.0.0.1:5000) on the browser of your choice (I tested on Safari).

You should see a webpage with a header, a body labeled "Case Name" with a search bar below, and a footer. In the header, there are links to the homepage (where you start) and to the About and Credits pages, which provide additonal information. The About page also includes a basic guide to using the cite, to complement this document.

Moving on from those pages, the core function of the site is the case search. Start to type in the name of any supreme court case of your choosing (I recommend Plessy v. Ferguson). A list of fuzzy name matches will appear below the search bar to guide your search. Note that the search is *somewhat* fuzzy. It is case insensitive and will look for cases where your string appears anywhere in the case name, but it will fail to find cases where the exact string you typed doesn't appear. Once you have settled on a final case name, hit enter (or click the search button). 

You will now be taken to a new webpage which displays a graph generated from your casename, which may be somewhat messy depending on the number of linked cases found. The case you search will (most likely) be near the middle of the screen, and will be highlighted in green. All the cases it *cites* will have an arrow pointing from your case to the other case, and all the cases *cited* by it will have an arrow pointing from the other case to your case. Similarly, arrows between non-highlighted cases indicate ciations between those cases. Note that the citation dataset I am using isn't the best, so some cases have no name and many modern citations are missing, as are all cases decided post 2003. Also don't be concerned if more than one case has the same name—this is absolutely a thing at the Supreme Court (for example, Brown and Brown II).

If you want, you can now click on any other cases in the graph. You will be prompted to "Expand citations for case 'foo'?", and if you click yes the graph will rebuild itself including all cases that cited or were cited by *either* the case you searched for or the case you clicked, with arrows representing the citations between all those cases. You can click on additional cases as many times as you like to repeat this process.

And that's it.—That is all the documentation necessary to run and use my project!