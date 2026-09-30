// ============================================
// PocketSmart AI - Authentication
// ============================================

function showMessage(element, message, success = false) {
    if (!element) return;

    element.textContent = message;
    element.style.display = "block";

    if (success) {
        element.style.color = "#00ff9d";
    } else {
        element.style.color = "#ff5c5c";
    }
}


// ============================================
// REGISTER
// ============================================

const registerForm = document.getElementById("registerForm");

if (registerForm) {
    registerForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const name = document.getElementById("registerName").value.trim();
        const email = document.getElementById("registerEmail").value.trim();
        const password = document.getElementById("registerPassword").value;
        const confirmPassword =
            document.getElementById("confirmPassword").value;

        const registerMessage =
            document.getElementById("registerMessage");

        // Basic validation
        if (!name || !email || !password || !confirmPassword) {
            showMessage(
                registerMessage,
                "Please fill in all fields."
            );
            return;
        }

        if (password.length < 8) {
            showMessage(
                registerMessage,
                "Password must be at least 8 characters."
            );
            return;
        }

        if (password !== confirmPassword) {
            showMessage(
                registerMessage,
                "Passwords do not match."
            );
            return;
        }

        // Disable button while processing
        const registerButton =
            registerForm.querySelector("button[type='submit']");

        if (registerButton) {
            registerButton.disabled = true;
            registerButton.textContent = "Creating Account...";
        }

        try {
            const response = await fetch("/api/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: name,
                    email: email,
                    password: password
                })
            });

            // Try to read JSON response
            let data;

            try {
                data = await response.json();
            } catch {
                data = {};
            }

            console.log("REGISTER STATUS:", response.status);
            console.log("REGISTER RESPONSE:", data);

            if (!response.ok) {
                let errorMessage = "Unable to create the account.";

                if (typeof data.detail === "string") {
                    errorMessage = data.detail;
                } else if (Array.isArray(data.detail)) {
                    errorMessage = data.detail
                        .map(error => error.msg)
                        .join(", ");
                } else if (data.message) {
                    errorMessage = data.message;
                }

                throw new Error(errorMessage);
            }

            showMessage(
                registerMessage,
                data.message || "Account created successfully!",
                true
            );

            // Redirect to login after successful registration
            setTimeout(() => {
                window.location.href = "/login";
            }, 1200);

        } catch (error) {
            console.error("REGISTER ERROR:", error);

            showMessage(
                registerMessage,
                error.message || "Unable to create the account right now."
            );

        } finally {
            if (registerButton) {
                registerButton.disabled = false;
                registerButton.textContent = "Create Account";
            }
        }
    });
}


// ============================================
// LOGIN
// ============================================

const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const email =
            document.getElementById("loginEmail").value.trim();

        const password =
            document.getElementById("loginPassword").value;

        const loginMessage =
            document.getElementById("loginMessage");

        // Basic validation
        if (!email || !password) {
            showMessage(
                loginMessage,
                "Please enter your email and password."
            );
            return;
        }

        // Disable button
        const loginButton =
            loginForm.querySelector("button[type='submit']");

        if (loginButton) {
            loginButton.disabled = true;
            loginButton.textContent = "Signing In...";
        }

        try {
            const response = await fetch("/api/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });

            let data;

            try {
                data = await response.json();
            } catch {
                data = {};
            }

            console.log("LOGIN STATUS:", response.status);
            console.log("LOGIN RESPONSE:", data);

            if (!response.ok) {
                let errorMessage = "Unable to login.";

                if (typeof data.detail === "string") {
                    errorMessage = data.detail;
                } else if (Array.isArray(data.detail)) {
                    errorMessage = data.detail
                        .map(error => error.msg)
                        .join(", ");
                } else if (data.message) {
                    errorMessage = data.message;
                }

                throw new Error(errorMessage);
            }

            // Store authentication information
            localStorage.setItem(
                "pocketsmart_token",
                data.token
            );

            localStorage.setItem(
                "pocketsmart_user",
                JSON.stringify(data.user)
            );

            showMessage(
                loginMessage,
                "Login successful! Redirecting...",
                true
            );

            setTimeout(() => {
                window.location.href = "/";
            }, 700);

        } catch (error) {
            console.error("LOGIN ERROR:", error);

            showMessage(
                loginMessage,
                error.message || "Unable to login right now."
            );

        } finally {
            if (loginButton) {
                loginButton.disabled = false;
                loginButton.textContent = "Login";
            }
        }
    });
}