
const API_URL =
    "https://diet-insights-ahmed01.azurewebsites.net/api/insights";

let barChart = null;
let scatterChart = null;
let pieChart = null;

const dietFilter = document.getElementById("dietFilter");
const dietSearch = document.getElementById("dietSearch");
const refreshBtn = document.getElementById("refreshBtn");
const insightsBtn = document.getElementById("insightsBtn");
const loadingStatus = document.getElementById("loadingStatus");
const executionTime = document.getElementById("executionTime");

const dietNames = {
    all: "All Diets",
    dash: "DASH",
    keto: "Keto",
    mediterranean: "Mediterranean",
    paleo: "Paleo",
    vegan: "Vegan"
};

const dietColors = {
    dash: "#2563eb",
    keto: "#f59e0b",
    mediterranean: "#10b981",
    paleo: "#8b5cf6",
    vegan: "#ef4444"
};

function normalizeDiets(diets) {
    if (Array.isArray(diets)) {
        return diets;
    }

    if (diets && typeof diets === "object") {
        return Object.entries(diets).map(([name, values]) => ({
            diet: name,
            ...values
        }));
    }

    return [];
}

function getDietName(item) {
    return String(
        item.diet ?? item.diet_type ?? item.name ?? ""
    ).toLowerCase();
}

function getNumber(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number : 0;
}

function destroyCharts() {
    if (barChart) barChart.destroy();
    if (scatterChart) scatterChart.destroy();
    if (pieChart) pieChart.destroy();

    barChart = null;
    scatterChart = null;
    pieChart = null;
}

function renderBarChart(diets) {
    const labels = diets.map(item =>
        dietNames[getDietName(item)] ??
        getDietName(item)
    );

    barChart = new Chart(
        document.getElementById("barChart"),
        {
            type: "bar",
            data: {
                labels,
                datasets: [
                    {
                        label: "Protein (g)",
                        data: diets.map(item =>
                            getNumber(
                                item.avg_protein ?? item.avg_protein_g
                            )
                        ),
                        backgroundColor: "#2563eb"
                    },
                    {
                        label: "Carbs (g)",
                        data: diets.map(item =>
                            getNumber(
                                item.avg_carbs ?? item.avg_carbs_g
                            )
                        ),
                        backgroundColor: "#10b981"
                    },
                    {
                        label: "Fat (g)",
                        data: diets.map(item =>
                            getNumber(
                                item.avg_fat ?? item.avg_fat_g
                            )
                        ),
                        backgroundColor: "#f59e0b"
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom"
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: "Average Nutrients (g)"
                        }
                    }
                }
            }
        }
    );
}

function renderPieChart(diets) {
    pieChart = new Chart(
        document.getElementById("pieChart"),
        {
            type: "pie",
            data: {
                labels: diets.map(item =>
                    dietNames[getDietName(item)] ??
                    getDietName(item)
                ),
                datasets: [{
                    label: "Recipe Count",
                    data: diets.map(item =>
                        getNumber(item.recipe_count)
                    ),
                    backgroundColor: diets.map(item =>
                        dietColors[getDietName(item)] ?? "#64748b"
                    )
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom"
                    }
                }
            }
        }
    );
}

function normalizeRecipes(recipes) {
    if (Array.isArray(recipes)) {
        return recipes;
    }

    if (recipes && typeof recipes === "object") {
        return Object.entries(recipes).flatMap(
            ([diet, items]) =>
                Array.isArray(items)
                    ? items.map(item => ({ diet, ...item }))
                    : []
        );
    }

    return [];
}

function renderScatterChart(recipes) {
    const points = recipes.map(recipe => ({
        x: getNumber(recipe.protein_g),
        y: getNumber(recipe.carbs_g)
    }));

    scatterChart = new Chart(
        document.getElementById("scatterChart"),
        {
            type: "scatter",
            data: {
                datasets: [{
                    label: "Top Protein Recipes",
                    data: points,
                    backgroundColor: "#8b5cf6",
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom"
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: "Protein (g)"
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: "Carbs (g)"
                        }
                    }
                }
            }
        }
    );
}

async function loadDashboard() {
    const selectedDiet = dietFilter.value;

    refreshBtn.disabled = true;
    insightsBtn.disabled = true;
    loadingStatus.textContent = "Loading nutritional data...";
    executionTime.textContent = "Execution Time: --";

    try {
        const response = await fetch(
            `${API_URL}?diet=${encodeURIComponent(selectedDiet)}`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        console.log("Azure API Response:", data);

        if (!data || !data.diets) {
            throw new Error("Unexpected API response format");
        }

        let diets = normalizeDiets(data.diets);
        let recipes = normalizeRecipes(
            data.top_protein_recipes
        );

        // Filter locally as well if the API returns all diets.
        if (selectedDiet !== "all") {
            diets = diets.filter(
                item => getDietName(item) === selectedDiet
            );

            recipes = recipes.filter(
                item =>
                    !item.diet ||
                    getDietName(item) === selectedDiet
            );
        }

        destroyCharts();

        renderBarChart(diets);
        renderScatterChart(recipes);
        renderPieChart(diets);

        const ms = data.metadata?.execution_time_ms;

        executionTime.textContent =
            ms !== undefined && ms !== null
                ? `Execution Time: ${ms} ms`
                : "Execution Time: Not available";

        loadingStatus.textContent =
            diets.length > 0
                ? "Data loaded successfully."
                : "No data found for the selected diet.";

    } catch (error) {
        console.error("Dashboard Error:", error);

        loadingStatus.textContent =
            `Failed to load data: ${error.message}`;

        destroyCharts();

    } finally {
        refreshBtn.disabled = false;
        insightsBtn.disabled = false;
    }
}

dietFilter.addEventListener("change", loadDashboard);

refreshBtn.addEventListener("click", loadDashboard);

insightsBtn.addEventListener("click", loadDashboard);

dietSearch.addEventListener("input", () => {
    const search = dietSearch.value.toLowerCase().trim();

    const options = [...dietFilter.options];

    const match = options.find(option =>
        option.text.toLowerCase().includes(search) ||
        option.value.includes(search)
    );

    if (match && search) {
        dietFilter.value = match.value;
    } else if (!search) {
        dietFilter.value = "all";
    }

    loadDashboard();
});

document.addEventListener("DOMContentLoaded", loadDashboard);
