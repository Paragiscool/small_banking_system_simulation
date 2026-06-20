document.addEventListener('DOMContentLoaded', () => {
    // Navigation logic
    const navLinks = document.querySelectorAll('.nav-link');
    const viewSections = document.querySelectorAll('.view-section');

    function switchView(targetId) {
        // Update links
        navLinks.forEach(link => {
            if(link.dataset.target === targetId) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

        // Update sections
        viewSections.forEach(section => {
            if(section.id === targetId) {
                section.classList.remove('hidden');
                section.classList.add('active');
            } else {
                section.classList.remove('active');
                setTimeout(() => {
                    if(!section.classList.contains('active')) {
                        section.classList.add('hidden');
                    }
                }, 400); // Wait for fade out (though we just snap hide it here for simplicity)
            }
        });
    }

    // Attach click listeners to nav links
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            switchView(e.target.dataset.target);
        });
    });

    // Login/Register button routing
    document.getElementById('loginBtn').addEventListener('click', () => {
        switchView('dashboard'); // Assuming login drops them in dashboard for demo
    });

    document.getElementById('registerBtn').addEventListener('click', () => {
        switchView('register');
    });

    // Registration Form Submission Mock
    const regForm = document.getElementById('registrationForm');
    if(regForm) {
        regForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const btn = regForm.querySelector('button');
            const originalText = btn.innerText;
            btn.innerText = "Generating Keys...";
            btn.disabled = true;

            setTimeout(() => {
                alert("Registration Successful! Redirecting to Dashboard.");
                btn.innerText = originalText;
                btn.disabled = false;
                switchView('dashboard');
            }, 1500);
        });
    }
});
