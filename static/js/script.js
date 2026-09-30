/* =========================================================
   PocketSmart AI
   Frontend Controller
   ========================================================= */

const API = "/api";

const TOKEN_KEY = "pocketsmart_token";
const USER_KEY = "pocketsmart_user";
const THEME_KEY = "theme";
const BUDGET_KEY = "budgetSettings";
const EXPENSE_KEY = "expenses";

let expenses = JSON.parse(localStorage.getItem(EXPENSE_KEY) || "[]");

let currentRecommendations = {};
let sessionCache = {};


/* =========================================================
   AUTHENTICATION
   ========================================================= */

function token() {
    return localStorage.getItem(TOKEN_KEY);
}


function user() {
    try {
        return JSON.parse(localStorage.getItem(USER_KEY) || "null");
    } catch {
        return null;
    }
}


function authHeaders(json = true) {
    const headers = {};

    if (json) {
        headers["Content-Type"] = "application/json";
    }

    const currentToken = token();

    if (currentToken) {
        headers["Authorization"] = `Bearer ${currentToken}`;
    }

    return headers;
}


async function apiFetch(url, options = {}) {
    const response = await fetch(url, options);

    if (response.status === 401) {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        window.location.href = "/login";
        throw new Error("Your session has expired. Please login again.");
    }

    let data = {};

    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (!response.ok) {
        let message = "Request failed.";

        if (typeof data.detail === "string") {
            message = data.detail;
        } else if (Array.isArray(data.detail)) {
            message = data.detail
                .map(item => item.msg || "Invalid input")
                .join(", ");
        } else if (data.message) {
            message = data.message;
        }

        throw new Error(message);
    }

    return data;
}


async function verifySession() {
    if (!token()) {
        window.location.href = "/login";
        return false;
    }

    try {
        const data = await apiFetch(`${API}/session-info`, {
            headers: authHeaders(false)
        });

        const storedUser = user() || {};
        const currentUser = data.user || data.user_info || data;

        const name = currentUser.name || storedUser.name || "User";
        const email = currentUser.email || storedUser.email || "";

        localStorage.setItem(
            USER_KEY,
            JSON.stringify({ ...storedUser, ...currentUser, name, email })
        );

        const welcome = document.getElementById("welcomeUser");

        if (welcome) {
            welcome.textContent = `Welcome, ${name}`;
        }

        return true;

    } catch {
        return false;
    }
}


async function logoutUser() {
    try {
        if (token()) {
            await fetch(`${API}/logout`, {
                method: "POST",
                headers: authHeaders(false)
            });
        }
    } catch (_) {}

    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);

    window.location.href = "/login";
}


/* =========================================================
   UTILITIES
   ========================================================= */

function escapeHTML(value) {
    const div = document.createElement("div");
    div.textContent = value == null ? "" : String(value);
    return div.innerHTML;
}


function formatCurrency(value) {
    return (
        "₹" +
        Number(value || 0).toLocaleString("en-IN", {
            maximumFractionDigits: 0
        })
    );
}


function showError(message) {
    alert(message || "Something went wrong. Please try again.");
}


function scrollToPlanners() {
    document.getElementById("planners")?.scrollIntoView({ behavior: "smooth" });
}


function scrollToFeatures() {
    document.getElementById("features")?.scrollIntoView({ behavior: "smooth" });
}


/* =========================================================
   THEME  (dark by default — Stark theme)
   ========================================================= */

function initTheme() {
    const button = document.getElementById("themeToggle");
    const saved = localStorage.getItem(THEME_KEY);

    /* FIX: dark is the default; only "light" turns it off */
    if (saved !== "light") {
        document.body.classList.add("dark");
    }

    if (button) {
        button.textContent = document.body.classList.contains("dark")
            ? "☀"
            : "◐";
    }

    button?.addEventListener("click", () => {
        document.body.classList.toggle("dark");

        const dark = document.body.classList.contains("dark");

        localStorage.setItem(THEME_KEY, dark ? "dark" : "light");

        button.textContent = dark ? "☀" : "◐";
    });
}


/* =========================================================
   PLANNER NAVIGATION
   ========================================================= */

function closePlanners() {
    ["homePlanner", "partyPlanner", "jewelryPlanner"].forEach(id => {
        const element = document.getElementById(id);

        if (element) {
            element.style.display = "none";
        }
    });
}


function openPlanner(id) {
    closePlanners();

    const section = document.getElementById(id);

    if (!section) return;

    section.style.display = "block";

    section.scrollIntoView({ behavior: "smooth", block: "start" });
}


function openHomePlanner() {
    openPlanner("homePlanner");
}


function openPartyPlanner() {
    openPlanner("partyPlanner");
}


function openJewelryPlanner() {
    openPlanner("jewelryPlanner");
}


/* =========================================================
   BUDGET DASHBOARD
   ========================================================= */

function getBudgetValues() {
    const read = id =>
        Number(document.getElementById(id)?.value) || 0;

    return {
        income: read("incomeInput"),
        food: read("foodInput"),
        transport: read("transportInput"),
        shopping: read("shoppingInput"),
        bills: read("billsInput")
    };
}


function updateBudget() {
    const budget = getBudgetValues();

    const spent =
        budget.food +
        budget.transport +
        budget.shopping +
        budget.bills;

    const remaining = budget.income - spent;

    const percentage =
        budget.income > 0 ? (spent / budget.income) * 100 : 0;

    function setText(id, value) {
        const element = document.getElementById(id);

        if (element) {
            element.textContent = value;
        }
    }

    const clampedPercentage = Math.min(Math.max(percentage, 0), 100);

    setText("incomeDisplay", formatCurrency(budget.income));
    setText("spentDisplay", formatCurrency(spent));
    setText("remainingDisplay", formatCurrency(remaining));
    setText("savingsDisplay", formatCurrency(Math.max(remaining, 0)));
    setText("percentageDisplay", `${percentage.toFixed(1)}%`);

    setText(
        "savingsPercentageDisplay",
        `${Math.max((remaining / (budget.income || 1)) * 100, 0).toFixed(1)}%`
    );

    setText("overviewSpent", formatCurrency(spent));
    setText("overviewIncome", formatCurrency(budget.income));
    setText("overviewPercentage", `${percentage.toFixed(1)}%`);
    setText("overviewRemaining", formatCurrency(Math.max(remaining, 0)));

    const overviewProgress = document.getElementById("overviewProgress");

    if (overviewProgress) {
        const bar =
            overviewProgress.querySelector(".overview-progress-bar") ||
            overviewProgress;

        bar.style.width = `${clampedPercentage}%`;
    }

    const categories = [
        ["foodExpenseDisplay", "foodProgress", budget.food],
        ["transportExpenseDisplay", "transportProgress", budget.transport],
        ["shoppingExpenseDisplay", "shoppingProgress", budget.shopping],
        ["billsExpenseDisplay", "billsProgress", budget.bills]
    ];

    categories.forEach(([amountId, progressId, value]) => {
        setText(amountId, formatCurrency(value));

        const bar = document.getElementById(progressId);

        if (bar) {
            bar.style.width = `${
                budget.income > 0
                    ? Math.min((value / budget.income) * 100, 100)
                    : 0
            }%`;
        }
    });

    const remainingDisplay = document.getElementById("remainingDisplay");

    if (remainingDisplay) {
        remainingDisplay.style.color = remaining < 0 ? "#ef4444" : "";
    }

    /* HERO CARD */

    const heroAmount = document.querySelector(".hero .budget-amount");

    if (heroAmount) {
        heroAmount.textContent = formatCurrency(budget.income);
    }

    const heroProgress = document.querySelector(".hero .progress-bar");

    if (heroProgress) {
        heroProgress.style.width = `${clampedPercentage}%`;
    }

    const heroInfo = document.querySelectorAll(".hero .budget-info strong");

    if (heroInfo[0]) {
        heroInfo[0].textContent = formatCurrency(spent);
    }

    if (heroInfo[1]) {
        heroInfo[1].textContent = formatCurrency(Math.max(remaining, 0));
    }

    localStorage.setItem(BUDGET_KEY, JSON.stringify(budget));

    syncSessionData();
}


function loadBudgetSettings() {
    try {
        const saved = JSON.parse(localStorage.getItem(BUDGET_KEY) || "null");

        if (!saved) return;

        ["income", "food", "transport", "shopping", "bills"].forEach(key => {
            const input = document.getElementById(`${key}Input`);

            if (input && saved[key] != null) {
                input.value = saved[key];
            }
        });

    } catch (_) {}
}


/* =========================================================
   EXPENSE TRACKER
   ========================================================= */

function saveExpenses() {
    localStorage.setItem(EXPENSE_KEY, JSON.stringify(expenses));
}


function getCategoryIcon(category) {
    const icons = {
        Food: "🍔",
        Transport: "🚗",
        Shopping: "🛍️",
        Bills: "📱",
        Other: "📦"
    };

    return icons[category] || "📦";
}


function addExpense() {
    const name = document.getElementById("expenseName")?.value.trim();

    const category =
        document.getElementById("expenseCategory")?.value || "Other";

    const amount = Number(document.getElementById("expenseAmount")?.value);

    if (!name) {
        return showError("Please enter an expense name.");
    }

    if (!amount || amount <= 0) {
        return showError("Please enter a valid amount.");
    }

    expenses.push({
        id: Date.now(),
        name,
        category,
        amount,
        created_at: new Date().toISOString()
    });

    saveExpenses();
    renderExpenses();
    clearExpenseForm();
}


function clearExpenseForm() {
    const name = document.getElementById("expenseName");
    const amount = document.getElementById("expenseAmount");

    if (name) {
        name.value = "";
    }

    if (amount) {
        amount.value = "";
    }
}


function deleteExpense(id) {
    expenses = expenses.filter(expense => expense.id !== id);

    saveExpenses();
    renderExpenses();
}


function renderExpenses() {
    const list =
        document.getElementById("expenseHistory") ||
        document.getElementById("expenseList");

    const count = document.getElementById("expenseCount");

    if (!list) return;

    if (count) {
        count.textContent = `${expenses.length} ${
            expenses.length === 1 ? "expense" : "expenses"
        }`;
    }

    if (!expenses.length) {
        list.innerHTML = `
            <div class="empty-expenses">
                <div>🧾</div>
                <strong>No expenses yet</strong>
                <p>Add your first expense above.</p>
            </div>
        `;

        return;
    }

    list.innerHTML = expenses
        .slice()
        .reverse()
        .map(expense => `
            <div class="expense-item">

                <div class="expense-left">

                    <div class="expense-icon">
                        ${getCategoryIcon(expense.category)}
                    </div>

                    <div>
                        <strong>${escapeHTML(expense.name)}</strong>
                        <small>${escapeHTML(expense.category)}</small>
                    </div>

                </div>

                <div class="expense-right">

                    <strong>${formatCurrency(expense.amount)}</strong>

                    <button
                        type="button"
                        class="delete-expense"
                        onclick="deleteExpense(${expense.id})"
                        title="Delete expense"
                    >×</button>

                </div>

            </div>
        `)
        .join("");
}


/* =========================================================
   MARKDOWN / AI RESULT RENDERING
   ========================================================= */

function renderMarkdown(text) {
    if (!text) {
        return "<p>No recommendation available.</p>";
    }

    const safe = escapeHTML(text);
    const lines = safe.split("\n");

    let html = "";
    let insideTable = false;

    lines.forEach(line => {
        const trimmed = line.trim();

        if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
            if (!insideTable) {
                html += '<div class="ai-table-wrapper"><table class="ai-table">';
                insideTable = true;
            }

            if (/^\|[\s|:-]+\|$/.test(trimmed)) {
                return;
            }

            const cells = trimmed.split("|").slice(1, -1);

            html += "<tr>";

            cells.forEach(cell => {
                html += `<td>${cell.trim()}</td>`;
            });

            html += "</tr>";

            return;
        }

        if (insideTable) {
            html += "</table></div>";
            insideTable = false;
        }

        if (!trimmed) {
            html += "<br>";
            return;
        }

        if (trimmed.startsWith("### ")) {
            html += `<h5>${trimmed.slice(4)}</h5>`;
            return;
        }

        if (trimmed.startsWith("## ")) {
            html += `<h4>${trimmed.slice(3)}</h4>`;
            return;
        }

        if (trimmed.startsWith("# ")) {
            html += `<h3>${trimmed.slice(2)}</h3>`;
            return;
        }

        if (trimmed.startsWith("- ")) {
            html += `<div class="ai-bullet">• ${trimmed.slice(2)}</div>`;
            return;
        }

        if (/^\d+\.\s/.test(trimmed)) {
            html += `<div class="ai-bullet">${trimmed}</div>`;
            return;
        }

        html += `<p>${trimmed}</p>`;
    });

    if (insideTable) {
        html += "</table></div>";
    }

    return html;
}


function recommendationText(data) {
    if (!data) return "";

    const candidate =
        data.recommendation ||
        data.result ||
        data.response ||
        data.message ||
        "";

    return typeof candidate === "string" ? candidate : "";
}


/* =========================================================
   RECOMMENDATION RESULT
   ========================================================= */

function setPlannerResult(planner, data) {
    const recommendation = recommendationText(data);

    const result = document.getElementById(`${planner}PlannerResult`);
    const output = document.getElementById(`${planner}Recommendation`);

    if (!result || !output) return;

    const recommendationId = data.recommendation_id || data.id || null;

    currentRecommendations[planner] = {
        id: recommendationId,
        text: recommendation
    };

    output.innerHTML = `

        <div class="recommendation-toolbar">

            <div class="recommendation-status">
                <span class="status-dot"></span>
                AI RECOMMENDATION READY
            </div>

            ${
                recommendationId
                    ? `<button
                            type="button"
                            class="save-recommendation-btn"
                            onclick="saveRecommendationById(${Number(recommendationId)})"
                       >☆ Save</button>`
                    : ""
            }

        </div>

        <div class="recommendation-body">
            ${renderMarkdown(recommendation)}
        </div>

        <div class="platform-links">

            <h4>Recommended Platforms</h4>

            <div class="platform-grid">
                ${platformCards(planner)}
            </div>

        </div>

    `;

    result.style.display = "block";

    result.scrollIntoView({ behavior: "smooth", block: "start" });
}


function platformCards(planner) {
    let platforms = [];

    if (planner === "home") {
        platforms = [
            ["IKEA", "Furniture, storage & decor", "https://www.ikea.com/in/en/"],
            ["Amazon", "Home products & electronics", "https://www.amazon.in/"],
            ["Flipkart", "Appliances & household products", "https://www.flipkart.com/"]
        ];
    }

    if (planner === "party") {
        platforms = [
            ["Swiggy", "Food & catering options", "https://www.swiggy.com/"],
            ["Zomato", "Restaurants & food services", "https://www.zomato.com/"],
            ["OYO", "Hotels & accommodation", "https://www.oyorooms.com/"]
        ];
    }

    if (planner === "jewelry") {
        platforms = [
            ["Amazon", "Jewelry marketplace", "https://www.amazon.in/"],
            ["Flipkart", "Jewelry marketplace", "https://www.flipkart.com/"]
        ];
    }

    return platforms
        .map(platform => `
            <a
                class="platform-card"
                href="${platform[2]}"
                target="_blank"
                rel="noopener noreferrer"
            >
                <strong>${platform[0]}</strong>
                <span>${platform[1]}</span>
                <small>Open platform ↗</small>
            </a>
        `)
        .join("");
}


function setLoading(button, text) {
    if (!button) {
        return () => {};
    }

    const original = button.textContent;

    button.disabled = true;
    button.textContent = text;

    return () => {
        button.disabled = false;
        button.textContent = original;
    };
}


/* =========================================================
   HOME PLANNER
   ========================================================= */

async function generateHomePlan() {
    const budget = Number(document.getElementById("homeBudget")?.value);
    const room = document.getElementById("homeRoom")?.value;
    const style = document.getElementById("homeStyle")?.value;
    const items = document.getElementById("homeItems")?.value.trim();
    const quantity = document.getElementById("homeQuantity")?.value.trim();

    if (!budget || budget <= 0 || !room || !style || !items || !quantity) {
        return showError("Please complete all Home Planner fields.");
    }

    const button = document.querySelector("#homePlanner .calculate-btn");
    const done = setLoading(button, "Generating Home Plan...");

    try {
        const data = await apiFetch(`${API}/generate-home`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ budget, room, style, items, quantity })
        });

        setPlannerResult("home", data);

        await savePlannerSession("home", {
            budget, room, style, items, quantity
        });

        loadHistory();

    } catch (error) {
        showError(error.message);

    } finally {
        done();
    }
}


/* =========================================================
   PARTY PLANNER
   ========================================================= */

async function generatePartyPlan() {
    const budget = Number(document.getElementById("partyBudget")?.value);
    const guests = Number(document.getElementById("partyGuests")?.value);
    const event_type = document.getElementById("partyEvent")?.value;
    const venue = document.getElementById("partyVenue")?.value;

    if (
        !budget || budget <= 0 ||
        !guests || guests <= 0 ||
        !event_type || !venue
    ) {
        return showError("Please complete all Party Planner fields.");
    }

    const button = document.querySelector("#partyPlanner .calculate-btn");
    const done = setLoading(button, "Generating Party Plan...");

    try {
        const data = await apiFetch(`${API}/generate-party`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ budget, guests, event_type, venue })
        });

        setPlannerResult("party", data);

        await savePlannerSession("party", {
            budget, guests, event_type, venue
        });

        loadHistory();

    } catch (error) {
        showError(error.message);

    } finally {
        done();
    }
}


/* =========================================================
   JEWELRY PLANNER
   ========================================================= */

async function generateJewelryPlan() {
    const budget = Number(document.getElementById("jewelryBudget")?.value);
    const occasion = document.getElementById("jewelryOccasion")?.value;
    const style = document.getElementById("jewelryStyle")?.value;
    const file = document.getElementById("outfitImage")?.files?.[0];

    if (!budget || budget <= 0 || !occasion || !style) {
        return showError("Please complete all Jewelry Planner fields.");
    }

    if (file && file.size > 8 * 1024 * 1024) {
        return showError("Please choose an image smaller than 8 MB.");
    }

    const button = document.querySelector("#jewelryPlanner .calculate-btn");
    const done = setLoading(button, "Analyzing Jewelry...");

    try {
        const form = new FormData();

        form.append("budget", budget);
        form.append("occasion", occasion);
        form.append("style", style);

        if (file) {
            form.append("outfit_image", file);
        }

        /* No Content-Type here — the browser sets the multipart boundary */
        const headers = {};

        if (token()) {
            headers.Authorization = `Bearer ${token()}`;
        }

        const data = await apiFetch(`${API}/generate-jewelry`, {
            method: "POST",
            headers,
            body: form
        });

        setPlannerResult("jewelry", data);

        await savePlannerSession("jewelry", {
            budget,
            occasion,
            style,
            has_outfit_image: Boolean(file)
        });

        loadHistory();

    } catch (error) {
        showError(error.message);

    } finally {
        done();
    }
}


/* =========================================================
   SESSION DATA
   ========================================================= */

async function syncSessionData() {
    if (!token()) return;

    const budget = getBudgetValues();

    try {
        /* FIX: backend expects { "data": { ... } } */
        await apiFetch(`${API}/session-data`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({
                data: { ...sessionCache, budget }
            })
        });

    } catch (_) {}
}


async function savePlannerSession(key, value) {
    sessionCache[key] = value;

    await syncSessionData();
}


async function loadSessionData() {
    if (!token()) return;

    try {
        const data = await apiFetch(`${API}/session-data`, {
            headers: authHeaders(false)
        });

        sessionCache =
            (data.data && typeof data.data === "object" ? data.data : null) ||
            data.session_data ||
            {};

        if (sessionCache.budget) {
            Object.entries(sessionCache.budget).forEach(([key, value]) => {
                const input = document.getElementById(`${key}Input`);

                if (input && value != null) {
                    input.value = value;
                }
            });

            updateBudget();
        }

    } catch (_) {}
}


/* =========================================================
   HISTORY
   ========================================================= */

function historyContainer() {
    return document.getElementById("historyList");
}


function savedContainer() {
    return document.getElementById("savedList");
}


function plannerIcon(type) {
    return (
        {
            home: "🏠",
            party: "🎉",
            jewelry: "💎"
        }[String(type || "").toLowerCase()] || "✦"
    );
}


function previewText(text, length = 220) {
    const plain = String(text || "")
        .replace(/[#*`|]/g, "")
        .replace(/\s+/g, " ")
        .trim();

    return plain.length > length ? plain.slice(0, length) + "…" : plain;
}


function savedItemCard(item, actionLabel, actionHandler) {
    const type = item.planner_type || item.type || "Recommendation";

    return `
        <article class="saved-item">

            <div class="saved-item-icon">${plannerIcon(type)}</div>

            <div class="saved-item-main">

                <div class="saved-item-top">
                    <span class="history-type">${escapeHTML(type)}</span>
                    <small>
                        ${escapeHTML(
                            item.saved_at || item.created_at || ""
                        )}
                    </small>
                </div>

                <h4>${escapeHTML(type)} Plan</h4>

                <p>${escapeHTML(previewText(recommendationText(item)))}</p>

                <div class="saved-item-actions">

                    <button
                        type="button"
                        onclick="loadRecommendation(${Number(item.id)})"
                    >Open</button>

                    <button
                        type="button"
                        onclick="${actionHandler}(${Number(item.id)})"
                    >${actionLabel}</button>

                </div>

            </div>

        </article>
    `;
}


function renderHistory(items) {
    const container = historyContainer();

    if (!container) return;

    if (!items.length) {
        container.innerHTML = `
            <div class="empty-state">
                <div>🕘</div>
                <strong>No recommendation history yet</strong>
                <p>Generate a Home, Party or Jewelry plan to see it here.</p>
            </div>
        `;

        return;
    }

    container.innerHTML = items
        .map(item => savedItemCard(item, "☆ Save", "saveRecommendationById"))
        .join("");
}


async function loadHistory() {
    if (!token() || !historyContainer()) {
        return;
    }

    try {
        const data = await apiFetch(`${API}/history`, {
            headers: authHeaders(false)
        });

        const items = Array.isArray(data)
            ? data
            : data.history || data.items || [];

        renderHistory(items);

    } catch (error) {
        console.warn("History:", error.message);
    }
}


/* =========================================================
   SAVED RECOMMENDATIONS
   ========================================================= */

function renderSaved(items) {
    const container = savedContainer();

    if (!container) return;

    if (!items.length) {
        container.innerHTML = `
            <div class="empty-state">
                <div>☆</div>
                <strong>No saved recommendations</strong>
                <p>Save a recommendation after generating a plan.</p>
            </div>
        `;

        return;
    }

    container.innerHTML = items
        .map(item => savedItemCard(item, "★ Saved", "removeSaved"))
        .join("");
}


async function loadSavedRecommendations() {
    if (!token() || !savedContainer()) {
        return;
    }

    try {
        const data = await apiFetch(`${API}/saved-recommendations`, {
            headers: authHeaders(false)
        });

        /* FIX: backend returns the list under "saved" */
        const items = Array.isArray(data)
            ? data
            : data.saved || data.recommendations || data.items || [];

        renderSaved(items);

    } catch (error) {
        console.warn("Saved recommendations:", error.message);
    }
}


async function loadRecommendation(id) {
    try {
        const data = await apiFetch(
            `${API}/recommendations-details/${id}`,
            { headers: authHeaders(false) }
        );

        /* FIX: backend nests the record under "recommendation" */
        const rec =
            data.recommendation && typeof data.recommendation === "object"
                ? data.recommendation
                : data;

        const type = String(rec.planner_type || rec.type || "").toLowerCase();

        const text =
            recommendationText(rec) ||
            (typeof rec.full_result === "string" ? rec.full_result : "");

        let target = null;

        if (type.includes("home")) {
            target = "home";
            openPlanner("homePlanner");
        } else if (type.includes("party")) {
            target = "party";
            openPlanner("partyPlanner");
        } else if (type.includes("jewel")) {
            target = "jewelry";
            openPlanner("jewelryPlanner");
        }

        if (target) {
            setPlannerResult(target, {
                ...rec,
                recommendation: text,
                recommendation_id: id
            });

        } else {
            const history = historyContainer();

            if (history) {
                history.innerHTML = `
                    <div class="recommendation-body">
                        ${renderMarkdown(text)}
                    </div>
                `;
            }
        }

    } catch (error) {
        showError(error.message);
    }
}


async function saveRecommendationById(id) {
    try {
        await apiFetch(`${API}/recommendations/${id}/save`, {
            method: "POST",
            headers: authHeaders(false)
        });

        await loadSavedRecommendations();

        alert("Recommendation saved.");

    } catch (error) {
        showError(error.message);
    }
}


async function removeSaved(id) {
    try {
        await apiFetch(`${API}/recommendations/${id}/save`, {
            method: "DELETE",
            headers: authHeaders(false)
        });

        await loadSavedRecommendations();

    } catch (error) {
        showError(error.message);
    }
}


/* =========================================================
   JARVIS AI
   ========================================================= */

async function askJarvis() {
    const processing = document.getElementById("jarvisProcessing");
    const responseBox = document.getElementById("jarvisResponse");

    if (processing) {
        processing.style.display = "flex";
    }

    if (responseBox) {
        responseBox.style.display = "none";
    }

    const budget = getBudgetValues();

    const question =
        `Analyze my current monthly budget. ` +
        `Income ${formatCurrency(budget.income)}, ` +
        `food ${formatCurrency(budget.food)}, ` +
        `transport ${formatCurrency(budget.transport)}, ` +
        `shopping ${formatCurrency(budget.shopping)}, ` +
        `bills ${formatCurrency(budget.bills)}. ` +
        `Give practical observations and three actions.`;

    try {
        const data = await apiFetch(`${API}/jarvis`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ question })
        });

        if (responseBox) {
            responseBox.innerHTML = `
                <div class="jarvis-message-icon">◈</div>

                <div>
                    <strong>JARVIS RESPONSE</strong>

                    <div class="recommendation-body">
                        ${renderMarkdown(recommendationText(data))}
                    </div>
                </div>
            `;

            responseBox.style.display = "flex";
        }

    } catch (error) {
        showError(error.message);

    } finally {
        if (processing) {
            processing.style.display = "none";
        }
    }
}


/* =========================================================
   INITIALIZATION
   ========================================================= */

document.addEventListener("DOMContentLoaded", async () => {
    initTheme();

    document
        .getElementById("logoutButton")
        ?.addEventListener("click", logoutUser);

    loadBudgetSettings();
    updateBudget();
    renderExpenses();

    if (!token()) {
        window.location.href = "/login";
        return;
    }

    const authenticated = await verifySession();

    if (!authenticated) {
        return;
    }

    await loadSessionData();

    await Promise.all([
        loadHistory(),
        loadSavedRecommendations()
    ]);
});