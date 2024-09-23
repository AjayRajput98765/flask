// JavaScript to handle the toggle between login and sign-up forms
const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
const container = document.querySelector('.container');
const signUpLink = document.getElementById('signUpLink');

let counter = 1;
setInterval(function() {
    document.getElementById('radio' + counter).checked = true;
    counter++;
    if(counter > 4) {
        counter = 1;
    }
}, 5000); // Change slide every 5 seconds


// Switch to the Sign-Up page
signUpButton.addEventListener('click', () => {
    container.classList.add('right-panel-active');
});

// Switch to the Login page
signInButton.addEventListener('click', () => {
    container.classList.remove('right-panel-active');
});

// Switch to the Sign-Up page when clicking the link in the login form
signUpLink.addEventListener('click', (e) => {
    e.preventDefault();
    container.classList.add('right-panel-active');
});

// Additional functionality for searching notes
function searchNotes() {
    const searchInput = document.getElementById('search').value.toLowerCase();

    // Mapping of search terms to page URLs
    const notePages = {
        'python-notes': "{{ url_for('python_notes') }}",
        'c++-notes': "{{ url_for('cpp_notes') }}",
        'java-notes': "{{ url_for('java_notes') }}",
        'sql-notes': "{{ url_for('sql_notes') }}",
        'flask-notes': "{{ url_for('flask_notes') }}",
    };

    // Check if the search input matches any predefined static notes
    // Check if the search input matches any predefined static notes
if (notePages[searchInput]) {
    // Redirect to the corresponding page
    window.location.href = notePages[searchInput];
} else {
    // Normal filtering for dynamic and static notes
    const dynamicNotes = document.querySelectorAll('.notes-list .note');
    const staticNotes = document.querySelectorAll('.static-notes .note-card');

    let foundNote = null;

    dynamicNotes.forEach(note => {
        const title = note.getAttribute('data-title').toLowerCase();
        const description = note.getAttribute('data-description').toLowerCase();
        const subject = note.getAttribute('data-subject').toLowerCase();

        if (title.includes(searchInput) || description.includes(searchInput) || subject.includes(searchInput)) {
            note.style.display = 'block'; // Or '' to keep original display style
            if (!foundNote) foundNote = note; // First match found
        } else {
            note.style.display = 'none';
        }
    });

    staticNotes.forEach(note => {
        const title = note.getAttribute('data-title').toLowerCase();

        if (title.includes(searchInput)) {
            note.style.display = 'block'; // Or '' to keep original display style
            if (!foundNote) foundNote = note; // First match found if not already found
        } else {
            note.style.display = 'none';
        }
    });

    // Scroll to the first matching note if one was found
    if (foundNote) {
        foundNote.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}
}

