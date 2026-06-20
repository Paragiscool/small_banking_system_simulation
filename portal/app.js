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

    // Dynamic Registration Form Submission
    const regForm = document.getElementById('registrationForm');
    if(regForm) {
        regForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = regForm.querySelector('button');
            const originalText = btn.innerText;
            btn.innerText = "Generating Keys...";
            btn.disabled = true;
            
            const appName = document.getElementById('appName').value;
            const redirectUri = document.getElementById('redirectUri').value;

            try {
                const response = await fetch('http://127.0.0.1:8000/portal/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ app_name: appName, redirect_uri: redirectUri })
                });

                if(response.ok) {
                    const data = await response.json();
                    alert(data.message);
                    
                    // Update dashboard UI with new keys
                    const credRows = document.querySelectorAll('.credential-row code');
                    if(credRows.length >= 2) {
                        credRows[0].innerText = data.client_id;
                        credRows[1].innerText = data.client_secret;
                    }
                    
                    switchView('dashboard');
                } else {
                    alert("Registration failed. Is the backend running?");
                }
            } catch (err) {
                alert("Network error. Ensure uvicorn is running on port 8000.");
            } finally {
                btn.innerText = originalText;
                btn.disabled = false;
            }
        });
    }
});
