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

// displays autocomplete suggestions
document.addEventListener("DOMContentLoaded", () => {
    let input = document.querySelector('#case-search');
    let list = document.querySelector('#suggestion-list');
    let box = document.getElementById('suggestion-box');
    if (!input || !list || !box) return;

    input.addEventListener('keyup', async function(event) {
        let html = '';

        const term = input.value.trim();
        try {
            const res = await fetch(`/autocomplete?term=${encodeURIComponent(term)}`);
            const matches = await res.json();

            for (let match of matches) {
                html += `
                    <li class="list-group-item list-group-item-action">
                        ${match.name}
                    </li>
                    `;
            }

            if (matches.length === 0) {
                html = '<li><em>No results found.</em></li>';
                box.style.display = 'none'; // Hide autocomplete if no inputs found
            }
            else{
                box.style.display = 'block'; // Else show the autocomplete results!
            }
        } catch (err) {
            console.error(err);
            html = '<li><em>Error loading results.</em></li>';
        }

        list.innerHTML = html;
    });
});
