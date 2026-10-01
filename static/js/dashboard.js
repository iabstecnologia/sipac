/**
 * SIPAC - Módulo de Visualização e Dashboard
 * Gerencia a renderização de gráficos interativos Chart.js
 * consumindo dados serializados com segurança via json_script.
 */

document.addEventListener("DOMContentLoaded", function () {
    const dataElement = document.getElementById("charts-data");
    if (!dataElement) {
        // Página não possui dados de gráficos
        return;
    }

    if (typeof Chart === "undefined") {
        console.warn("SIPAC: Biblioteca Chart.js não encontrada.");
        return;
    }

    let chartsData;
    try {
        chartsData = JSON.parse(dataElement.textContent);
    } catch (e) {
        console.error("SIPAC: Falha ao interpretar dados JSON dos gráficos:", e);
        return;
    }

    // Configurações globais padrão do Chart.js
    Chart.defaults.font.family = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif";
    Chart.defaults.color = "#495057";

    // Paleta de cores corporativa SIPAC
    const COLORS = {
        primary: "#198754",
        primaryLight: "rgba(25, 135, 84, 0.15)",
        primaryHover: "#146c43",
        blue: "#0d6efd",
        blueLight: "rgba(13, 110, 253, 0.8)",
        cyan: "#0dcaf0",
        orange: "rgba(253, 126, 20, 0.85)",
        yellow: "#ffc107",
        pink: "#d63384",
        purple: "#6f42c1",
        gray: "#6c757d",
        palette: [
            "#198754",
            "#0d6efd",
            "#20c997",
            "#fd7e14",
            "#6f42c1",
            "#0dcaf0",
            "#ffc107",
            "#d63384",
            "#6c757d",
        ],
    };

    /**
     * Helper para verificar se um conjunto de dados possui valores numéricos > 0
     */
    function hasData(dataset) {
        return dataset && Array.isArray(dataset.data) && dataset.data.some((val) => val > 0);
    }

    /**
     * 1. Gráfico de Evolução Cronológica (Linha com Área)
     */
    const ctxEvolucao = document.getElementById("chartEvolucao");
    if (ctxEvolucao && chartsData.evolucao) {
        const data = chartsData.evolucao;
        new Chart(ctxEvolucao, {
            type: "line",
            data: {
                labels: data.labels && data.labels.length > 0 ? data.labels : ["Sem dados"],
                datasets: [
                    {
                        label: "Participações",
                        data: data.data && data.data.length > 0 ? data.data : [0],
                        borderColor: COLORS.primary,
                        backgroundColor: COLORS.primaryLight,
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: COLORS.primary,
                        pointBorderColor: "#fff",
                        pointHoverRadius: 6,
                        pointRadius: 4,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return ` Participações: ${context.parsed.y.toLocaleString("pt-BR")}`;
                            },
                        },
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                        },
                        grid: {
                            color: "rgba(0, 0, 0, 0.05)",
                        },
                    },
                    x: {
                        grid: {
                            display: false,
                        },
                    },
                },
            },
        });
    }

    /**
     * 2. Gráfico de Gênero (Doughnut / Rosca)
     */
    const ctxGenero = document.getElementById("chartGenero");
    if (ctxGenero && chartsData.genero) {
        const data = chartsData.genero;
        const generoColors = {
            Masculino: COLORS.blue,
            Feminino: COLORS.pink,
            "Não Informado": COLORS.gray,
        };
        const bgColors = (data.labels || []).map(
            (label) => generoColors[label] || COLORS.gray
        );

        new Chart(ctxGenero, {
            type: "doughnut",
            data: {
                labels: data.labels && data.labels.length > 0 ? data.labels : ["Sem dados"],
                datasets: [
                    {
                        data: data.data && data.data.length > 0 ? data.data : [1],
                        backgroundColor: bgColors.length > 0 ? bgColors : [COLORS.gray],
                        borderWidth: 2,
                        borderColor: "#ffffff",
                        hoverOffset: 4,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "65%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            padding: 16,
                            usePointStyle: true,
                        },
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const val = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                return ` ${context.label}: ${val.toLocaleString("pt-BR")} (${pct}%)`;
                            },
                        },
                    },
                },
            },
        });
    }

    /**
     * 3. Gráfico de Participações por Estado (Barras Verticais)
     */
    const ctxEstado = document.getElementById("chartEstado");
    if (ctxEstado && chartsData.estado) {
        const data = chartsData.estado;
        new Chart(ctxEstado, {
            type: "bar",
            data: {
                labels: data.labels && data.labels.length > 0 ? data.labels : ["Sem dados"],
                datasets: [
                    {
                        label: "Participações",
                        data: data.data && data.data.length > 0 ? data.data : [0],
                        backgroundColor: "rgba(25, 135, 84, 0.85)",
                        hoverBackgroundColor: COLORS.primaryHover,
                        borderRadius: 4,
                        borderSkipped: false,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return ` Participações: ${context.parsed.y.toLocaleString("pt-BR")}`;
                            },
                        },
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                        },
                        grid: {
                            color: "rgba(0, 0, 0, 0.05)",
                        },
                    },
                    x: {
                        grid: {
                            display: false,
                        },
                    },
                },
            },
        });
    }

    /**
     * 4. Gráfico de Comunidades Tradicionais (Donut)
     */
    const ctxComunidade = document.getElementById("chartComunidade");
    if (ctxComunidade && chartsData.comunidade) {
        const data = chartsData.comunidade;
        new Chart(ctxComunidade, {
            type: "doughnut",
            data: {
                labels: data.labels && data.labels.length > 0 ? data.labels : ["Sem dados"],
                datasets: [
                    {
                        data: data.data && data.data.length > 0 ? data.data : [1],
                        backgroundColor: COLORS.palette.slice(0, (data.labels || []).length),
                        borderWidth: 2,
                        borderColor: "#ffffff",
                        hoverOffset: 4,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "60%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            padding: 12,
                            usePointStyle: true,
                            font: {
                                size: 11,
                            },
                        },
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const val = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                return ` ${context.label}: ${val.toLocaleString("pt-BR")} (${pct}%)`;
                            },
                        },
                    },
                },
            },
        });
    }

    /**
     * 5. Gráfico de Metas Internas (Barras Horizontais)
     */
    const ctxMeta = document.getElementById("chartMeta");
    if (ctxMeta && chartsData.meta) {
        const data = chartsData.meta;
        new Chart(ctxMeta, {
            type: "bar",
            data: {
                labels: data.labels && data.labels.length > 0 ? data.labels : ["Sem dados"],
                datasets: [
                    {
                        label: "Participações",
                        data: data.data && data.data.length > 0 ? data.data : [0],
                        backgroundColor: COLORS.blueLight,
                        borderRadius: 4,
                    },
                ],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return ` Participações: ${context.parsed.x.toLocaleString("pt-BR")}`;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                        },
                        grid: {
                            color: "rgba(0, 0, 0, 0.05)",
                        },
                    },
                    y: {
                        grid: {
                            display: false,
                        },
                        ticks: {
                            autoSkip: false,
                            font: {
                                size: 11,
                            },
                        },
                    },
                },
            },
        });
    }

    /**
     * 6. Gráfico de Frentes Responsáveis (Barras Horizontais)
     */
    const ctxFrente = document.getElementById("chartFrente");
    if (ctxFrente && chartsData.frente) {
        const data = chartsData.frente;
        new Chart(ctxFrente, {
            type: "bar",
            data: {
                labels: data.labels && data.labels.length > 0 ? data.labels : ["Sem dados"],
                datasets: [
                    {
                        label: "Participações",
                        data: data.data && data.data.length > 0 ? data.data : [0],
                        backgroundColor: COLORS.orange,
                        borderRadius: 4,
                    },
                ],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return ` Participações: ${context.parsed.x.toLocaleString("pt-BR")}`;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                        },
                        grid: {
                            color: "rgba(0, 0, 0, 0.05)",
                        },
                    },
                    y: {
                        grid: {
                            display: false,
                        },
                    },
                },
            },
        });
    }

    console.log("SIPAC: Todos os gráficos analíticos foram inicializados com sucesso.");
});
