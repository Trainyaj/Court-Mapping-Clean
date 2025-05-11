// displays an error popup if the user attempts to search for a case name
// that has no matches in the database
window.onload = function() {
    const modal = document.getElementById("errorModal");
    const closeBtn = document.querySelector(".close-button");

    // returns if no error
    if (!modal || !closeBtn) {
        return;
    }
    modal.style.display = "flex";

    closeBtn.onclick = function() {
        modal.style.display = "none";
    };

    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    };
};

// displays autocomplete suggestions generated /autocomplete
document.addEventListener("DOMContentLoaded", () => {
    // gets html elements for user input, list of suggestions (which will be modified)
    // and the box around those suggestions 
    let input = document.querySelector('#case-search');
    let list = document.querySelector('#suggestion-list');
    let box = document.getElementById('suggestion-box');
    // if any of those elments can't be found (perhaps due to user tinkering),
    //  don't show any suggestions
    if (!input || !list || !box) return;

    // very much inspired (and using some code of) the in-class word autocomplete
    input.addEventListener('keyup', async function(event) {
        let html = '';
        // term is the user input
        const term = input.value;
        try {
            // gets case_name matches for the user input
            const res = await fetch(`/autocomplete?term=${encodeURIComponent(term)}`);
            const matches = await res.json();

            // manually builds the html list of matches (ugly, I know, sorry)
            for (let match of matches) {
                html += `
                    <li class="list-group-item list-group-item-action">
                        ${match.name}
                    </li>
                    `;
            }

            // if no matches were found, hides the autocomplete
            if (matches.length === 0) {
                html = '<li><em>No results found.</em></li>';
                box.style.display = 'none'; 
            }
            // otherwise shows the autocomplete (which might have been hidden before)
            else {
                box.style.display = 'block'; 
            }
        } catch (err) {
            console.error(err);
            html = '<li><em>Error loading results.</em></li>';
        }
        // Updates the html with the new search results
        list.innerHTML = html;
    });
});
